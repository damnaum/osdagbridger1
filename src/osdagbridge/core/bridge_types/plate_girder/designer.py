"""
Plate girder design — IS 800:2007 / IRC:24-2010

Covers the bread-and-butter workflow for steel highway bridges:
initial sizing → section properties → classification → moment &
shear capacity → deflection → web bearing.

Not a replacement for detailed FE analysis on unusual geometry;
that's what the opensees / ospgrillage adapters are for.
"""

import math
from typing import Any, Dict, Optional, Tuple

from .analyser import analyze_plate_girder
from .dto import PlateGirderInput, PlateGirderSection

# Material constants — IS 800:2007 Cl. 2.2 / Table 1
E_STEEL = 200_000.0   # MPa
G_STEEL = 76_923.0    # MPa  (= E / 2(1+0.3))
GAMMA_M0 = 1.10       # partial safety factor — yielding
GAMMA_M1 = 1.25       # partial safety factor — buckling
DENSITY_STEEL = 78.5  # kN/m³


def calculate_epsilon(fy: float) -> float:
    """Normalised yield ratio ε = √(250 / fy).

    Shows up everywhere in IS 800 Table 2 slenderness limits.
    For E250 grade it's simply 1.0; higher grades shrink it,
    tightening the limits.
    """
    return math.sqrt(250.0 / fy)


def initial_sizing(input_data: PlateGirderInput) -> Tuple[float, float, float, float]:
    """Work out a starting set of plate girder dimensions.

    The numbers here come from a mix of commonly used thumb rules
    (mostly from Subramanian's *Design of Steel Structures*,
    Ch. 8) and some practical workshop constraints we've picked
    up over the years:

      * Overall depth ≈ span / 12 – 15 (deeper for heavy 70R)
      * Web thickness chosen so d/tw stays under ~120 ε; going
        past 130 practically forces stiffeners every metre, which
        fabricators hate.
      * Flange width ≈ d/3 – d/4, capped by the outstand limit
        in IS 800 Table 2.
      * Flange thickness at least 2 × web thickness and not less
        than 20 mm — anything thinner buckles during transport.

    Returns (web_depth, web_thickness, flange_width, flange_thickness)
    all in millimetres.
    """
    span = input_data.effective_span
    fy = input_data.get_yield_strength()
    eps = calculate_epsilon(fy)

    # Deeper section for heavier vehicles; 70R trains are about
    # 50% heavier per axle than Class A.
    if input_data.live_load_class == "CLASS_70R":
        depth_ratio = 12
    elif input_data.live_load_class == "CLASS_AA":
        depth_ratio = 13
    else:
        depth_ratio = 14

    overall_d = span / depth_ratio
    # snap to nearest 50 mm — plate stock comes in round sizes
    overall_d = math.ceil(overall_d / 50) * 50

    tf = max(20.0, overall_d / 35)           # slightly chunkier flanges
    tf = math.ceil(tf / 2) * 2               # even mm for standard plate

    d_web = overall_d - 2 * tf

    # --- web thickness ---
    # Keep d/tw around 100–120 ε so we land in compact territory;
    # going thinner saves a few kg but the stiffener labour costs
    # more than the plate weight in most Indian fabrication yards.
    tw_min = max(8.0, d_web / (120 * eps))
    tw = math.ceil(tw_min / 2) * 2
    tw = max(10.0, tw)                       # 10 mm floor for highway bridges

    # --- flange width ---
    bf = d_web / 3
    # outstand limit for compact flange: (bf - tw) / (2 tf) < 9.4 ε
    max_outstand = 9.4 * eps * tf
    bf_max = 2 * max_outstand + tw
    bf = min(bf, bf_max)
    bf = math.ceil(bf / 10) * 10             # round to 10 mm
    bf = max(250.0, bf)                      # practical min for stability

    return d_web, tw, bf, tf


def calculate_section_properties(
    d_web: float,
    t_web: float,
    b_tf: float,
    t_tf: float,
    b_bf: Optional[float] = None,
    t_bf: Optional[float] = None,
    fy: float = 250.0,
) -> PlateGirderSection:
    """Build a full section-property set from plate dimensions.

    Assumes a doubly-symmetric section when bottom flange sizes
    are omitted (the common case for highway bridges).  All the
    parallel-axis stuff is spelled out longhand rather than
    using numpy so we stay dependency-light for the core.
    """
    # Default to symmetric section if bottom flange not specified
    if b_bf is None:
        b_bf = b_tf
    if t_bf is None:
        t_bf = t_tf

    # Total depth
    total_depth = d_web + t_tf + t_bf

    # Component areas
    area_web = d_web * t_web
    area_tf = b_tf * t_tf
    area_bf = b_bf * t_bf
    total_area = area_web + area_tf + area_bf

    # Centroid of each component from bottom of bottom flange
    y_bf = t_bf / 2
    y_web = t_bf + d_web / 2
    y_tf = t_bf + d_web + t_tf / 2

    # Overall centroid from bottom
    y_centroid = (area_bf * y_bf + area_web * y_web + area_tf * y_tf) / total_area

    # Moment of inertia about centroidal axis using parallel axis theorem
    # I_total = Σ(I_local + A*d²) for each component

    # Web contribution
    i_web_local = t_web * d_web**3 / 12
    i_web = i_web_local + area_web * (y_web - y_centroid) ** 2

    # Top flange contribution
    i_tf_local = b_tf * t_tf**3 / 12
    i_tf = i_tf_local + area_tf * (y_tf - y_centroid) ** 2

    # Bottom flange contribution
    i_bf_local = b_bf * t_bf**3 / 12
    i_bf = i_bf_local + area_bf * (y_bf - y_centroid) ** 2

    i_xx = i_web + i_tf + i_bf  # mm⁴

    # I_yy (about weak axis through web centre)
    i_yy = d_web * t_web**3 / 12 + t_tf * b_tf**3 / 12 + t_bf * b_bf**3 / 12

    # Elastic section moduli
    y_top = total_depth - y_centroid  # distance to top fiber
    y_bottom = y_centroid             # distance to bottom fiber

    z_top = i_xx / y_top       # mm³
    z_bottom = i_xx / y_bottom  # mm³

    # Plastic section modulus
    # For I-section: find equal area axis, then Zp = A_above * ȳ_above + A_below * ȳ_below
    # For doubly symmetric: Zp = (Af * (d + tf)) + (tw * dw² / 4)
    # General formula for possibly unsymmetric section:
    z_plastic = (
        (area_tf * (d_web + t_tf) + area_bf * (d_web + t_bf)) / 2
        + t_web * d_web**2 / 4
    )

    # Slenderness ratios
    web_slenderness = d_web / t_web

    # Flange outstand ratio: half the outstand / flange thickness
    flange_outstand = (b_tf - t_web) / 2
    flange_slenderness = flange_outstand / t_tf

    # Section classification using actual fy
    section_class = classify_section(web_slenderness, flange_slenderness, fy)

    return PlateGirderSection(
        web_depth=d_web,
        web_thickness=t_web,
        top_flange_width=b_tf,
        top_flange_thickness=t_tf,
        bottom_flange_width=b_bf,
        bottom_flange_thickness=t_bf,
        total_depth=total_depth,
        area=total_area,
        moment_of_inertia_xx=i_xx,
        moment_of_inertia_yy=i_yy,
        section_modulus_top=z_top,
        section_modulus_bottom=z_bottom,
        centroid_from_bottom=y_centroid,
        plastic_section_modulus=z_plastic,
        section_class=section_class,
        web_slenderness=web_slenderness,
        flange_slenderness=flange_slenderness,
    )


def classify_section(
    web_slenderness: float,
    flange_slenderness: float,
    fy: float,
) -> str:
    """IS 800 Table 2 section classification.

    Whichever plate element (web or flange outstand) is the most
    slender dictates the class.  The class in turn decides whether
    we can use plastic modulus (plastic/compact) or must fall back
    to elastic modulus (semi-compact/slender).
    """
    epsilon = calculate_epsilon(fy)

    # Limits from IS 800:2007, Table 2
    # Web limits (internal element in bending)
    web_plastic_limit = 84 * epsilon
    web_compact_limit = 105 * epsilon
    web_semi_compact_limit = 126 * epsilon

    # Flange limits (outstand element in compression)
    flange_plastic_limit = 8.4 * epsilon
    flange_compact_limit = 9.4 * epsilon
    flange_semi_compact_limit = 13.6 * epsilon

    # Section class is governed by whichever element is more slender
    if (
        web_slenderness <= web_plastic_limit
        and flange_slenderness <= flange_plastic_limit
    ):
        return "plastic"

    elif (
        web_slenderness <= web_compact_limit
        and flange_slenderness <= flange_compact_limit
    ):
        return "compact"

    elif (
        web_slenderness <= web_semi_compact_limit
        and flange_slenderness <= flange_semi_compact_limit
    ):
        return "semi-compact"

    else:
        return "slender"


def calculate_moment_capacity(
    section: PlateGirderSection,
    fy: float,
    unbraced_length: float,
    effective_length_factor: float = 1.0,
) -> Dict[str, float]:
    """Moment capacity (IS 800 Cl. 8.2) with LTB reduction.

    Returns the lesser of:
      a) cross-section plastic/elastic capacity, and
      b) lateral-torsional buckling capacity.

    For most bridge girders the cross-beam spacing keeps the
    unbraced length short enough that LTB doesn't govern, but
    we check anyway.
    """
    results = {}

    # section plastic/elastic capacity (Cl. 8.2.1.2)
    if section.section_class in ("plastic", "compact"):
        # Use plastic section modulus
        m_d = 1.0 * section.plastic_section_modulus * fy / GAMMA_M0
    else:
        # semi-compact/slender: fall back to elastic modulus
        z_elastic = min(section.section_modulus_top, section.section_modulus_bottom)
        m_d = z_elastic * fy / GAMMA_M0

    results["moment_capacity_section_kNm"] = m_d / 1e6

    # lateral-torsional buckling (Cl. 8.2.2)
    if unbraced_length > 0:
        # effective LTB length
        l_lt = effective_length_factor * unbraced_length

        h = section.total_depth
        i_y = section.moment_of_inertia_yy

        # St. Venant torsion constant for thin-walled open section
        # It ≈ Σ(b·t³ / 3)
        i_t = (
            section.top_flange_width * section.top_flange_thickness**3
            + section.bottom_flange_width * section.bottom_flange_thickness**3
            + section.web_depth * section.web_thickness**3
        ) / 3

        # warping constant (symmetric I): Iw = Iy · h² / 4
        i_w = i_y * h**2 / 4

        # elastic critical moment (uniform bending)
        term1 = math.pi**2 * E_STEEL * i_y / l_lt**2
        term2_inside = i_w / i_y + (l_lt**2 * G_STEEL * i_t) / (
            math.pi**2 * E_STEEL * i_y
        )

        # guard against tiny or negative term under the root
        if term2_inside <= 0:
            m_cr = float("inf")
        else:
            m_cr = term1 * math.sqrt(term2_inside)

        results["critical_moment_kNm"] = m_cr / 1e6

        # non-dimensional slenderness
        lambda_lt = math.sqrt(section.plastic_section_modulus * fy / m_cr)
        results["lambda_lt"] = lambda_lt

        # imperfection parameter — all plate girders are welded
        # h/bf ≤ 2 → αLT = 0.49;  h/bf > 2 → αLT = 0.76
        if section.total_depth / section.top_flange_width <= 2:
            alpha_lt = 0.49  # Welded, h/bf <= 2
        else:
            alpha_lt = 0.76  # Welded, h/bf > 2

        # Perry-Robertson style curve
        phi_lt = 0.5 * (1 + alpha_lt * (lambda_lt - 0.2) + lambda_lt**2)

        # χLT ≤ 1.0
        discriminant = phi_lt**2 - lambda_lt**2
        if discriminant <= 0:
            chi_lt = 1.0  # Very short unbraced length, no reduction
        else:
            chi_lt = min(1.0, 1.0 / (phi_lt + math.sqrt(discriminant)))

        results["alpha_lt"] = alpha_lt
        results["phi_lt"] = phi_lt
        results["chi_lt"] = chi_lt

        # reduced capacity considering LTB
        m_d_ltb = chi_lt * section.plastic_section_modulus * fy / GAMMA_M1
        results["moment_capacity_ltb_kNm"] = m_d_ltb / 1e6

        # Governing capacity is the lesser of section and LTB
        results["moment_capacity_governing_kNm"] = min(
            results["moment_capacity_section_kNm"],
            results["moment_capacity_ltb_kNm"],
        )
    else:
        # Continuously braced - no LTB check needed
        results["moment_capacity_governing_kNm"] = results[
            "moment_capacity_section_kNm"
        ]

    return results


def calculate_shear_capacity(
    section: PlateGirderSection,
    fy: float,
    stiffener_spacing: Optional[float] = None,
) -> Dict[str, float]:
    """Shear capacity per IS 800 Cl. 8.4.

    Stocky webs (d/tw ≤ 67ε) get full plastic shear.  Slender
    webs need a shear-buckling reduction — the kv coefficient
    improves substantially once you add transverse stiffeners.
    """
    results = {}

    d = section.web_depth
    t_w = section.web_thickness

    # shear area = d × tw for welded I-sections
    a_v = d * t_w

    # von Mises: τ_y = fy / √3
    f_yw = fy / math.sqrt(3)

    # plastic shear
    v_p = a_v * f_yw / GAMMA_M0
    results["plastic_shear_capacity_kN"] = v_p / 1000

    # web slenderness & limit
    lambda_w = d / t_w
    epsilon = calculate_epsilon(fy)
    results["web_slenderness"] = lambda_w
    results["epsilon"] = epsilon

    # Cl. 8.4.2: stocky web if d/tw ≤ 67ε
    critical_slenderness = 67 * epsilon

    if lambda_w <= critical_slenderness:
        # ok, full plastic capacity
        results["design_shear_capacity_kN"] = results["plastic_shear_capacity_kN"]
        results["method"] = "plastic"
        results["buckling_check_required"] = False
    else:
        # slender web --> shear buckling governs
        results["buckling_check_required"] = True

        # buckling coefficient kv (Cl. 8.4.2.2)
        if stiffener_spacing is None or stiffener_spacing > d:
            # unstiffened panel
            k_v = 5.35
            results["stiffening"] = "unstiffened"
        else:
            # stiffened: kv = 5.35 + 4/(c/d)²
            c = stiffener_spacing
            ratio = c / d
            k_v = 5.35 + 4.0 / ratio**2
            results["stiffening"] = f"stiffened at {c:.0f}mm"

        results["k_v"] = k_v

        # elastic critical shear stress
        poisson = 0.3
        tau_cr_e = (
            k_v * math.pi**2 * E_STEEL / (12 * (1 - poisson**2)) * (t_w / d) ** 2
        )
        results["tau_cr_elastic"] = tau_cr_e

        # non-dimensional web shear slenderness
        lambda_w_shear = math.sqrt(f_yw / tau_cr_e) if tau_cr_e > 0 else 999.0
        results["lambda_w_shear"] = lambda_w_shear

        # Table 14 shear buckling strength τ_b
        if lambda_w_shear <= 0.8:
            tau_b = f_yw
        elif lambda_w_shear < 1.2:
            tau_b = (1 - 0.8 * (lambda_w_shear - 0.8)) * f_yw
        else:
            tau_b = f_yw / lambda_w_shear**2

        results["tau_b"] = tau_b

        # Design shear capacity with buckling
        v_cr = a_v * tau_b / GAMMA_M1
        results["design_shear_capacity_kN"] = v_cr / 1000
        results["method"] = "post-critical"

    return results


def check_deflection(
    span: float,
    moment_of_inertia: float,
    total_udl_sls: float,
    max_point_load_sls: float = 0.0,
) -> Dict[str, float]:
    """Serviceability deflection check (IRC:24-2010 Cl. 504.5).

    Highway bridges are limited to span/600 under live load.
    We compute UDL and point-load components separately so the
    caller can see which one dominates.
    """
    results = {}

    # Deflection from UDL
    if total_udl_sls > 0:
        delta_udl = 5 * total_udl_sls * span**4 / (384 * E_STEEL * moment_of_inertia)
    else:
        delta_udl = 0.0

    # Deflection from point load at midspan
    if max_point_load_sls > 0:
        delta_point = max_point_load_sls * span**3 / (48 * E_STEEL * moment_of_inertia)
    else:
        delta_point = 0.0

    total_deflection = delta_udl + delta_point

    # Allowable: L/600 for highway bridges (IRC:24-2010, Clause 508.3)
    allowable_deflection = span / 600

    results["deflection_udl_mm"] = delta_udl
    results["deflection_point_mm"] = delta_point
    results["total_deflection_mm"] = total_deflection
    results["allowable_deflection_mm"] = allowable_deflection
    results["deflection_ratio"] = span / total_deflection if total_deflection > 0 else float("inf")
    results["deflection_ok"] = total_deflection <= allowable_deflection

    return results


def check_web_bearing(
    section: PlateGirderSection,
    fy: float,
    bearing_length: float,
    reaction: float,
) -> Dict[str, float]:
    """Web crippling at supports (IS 800 Cl. 8.7.4).

    If the bearing capacity is less than the reaction, the
    detail drawings need bearing stiffeners — flag it early.
    """
    t_w = section.web_thickness
    t_f = section.top_flange_thickness  # Assume same for bearing

    # Dispersion length through flange at 1:2.5 slope
    # n1 = bearing_length + 5*(tf + root_radius)
    # For welded sections, root radius ≈ 0 (weld toe)
    n1 = bearing_length + 5 * t_f

    # Web bearing capacity
    # Fw = (b1 + n1) * tw * fy / γm0
    # where b1 is the stiff bearing length
    fw = (bearing_length + n1) * t_w * fy / GAMMA_M0
    fw_kN = fw / 1000

    results = {
        "bearing_capacity_kN": fw_kN,
        "reaction_kN": reaction,
        "dispersion_length_mm": n1,
        "bearing_ok": fw_kN >= reaction,
    }

    if not results["bearing_ok"]:
        results["note"] = (
            f"Web bearing capacity {fw_kN:.1f} kN < reaction {reaction:.1f} kN. "
            "Bearing stiffeners required at supports."
        )

    return results


def design_plate_girder(input_data: PlateGirderInput) -> Dict[str, Any]:
    """Run the full plate girder design pipeline.

    Sequence: sizing → properties → dead loads → live-load
    analysis → factored forces → moment check → shear check →
    deflection check.  Collects warnings along the way so the
    caller (CLI, web, desktop) can display them.
    """
    results = {
        "input": input_data.model_dump(),
        "status": "in_progress",
        "warnings": [],
        "errors": [],
    }

    fy = input_data.get_yield_strength()
    fu = input_data.get_ultimate_strength()   # needed later for connection checks
    span_mm = input_data.effective_span
    span_m = span_mm / 1000

    # -- sizing --
    if input_data.web_depth is None:
        d_web, t_web, b_f, t_f = initial_sizing(input_data)
        results["sizing_method"] = "auto"
    else:
        d_web = input_data.web_depth
        t_web = input_data.web_thickness or 12.0  # Sensible default
        b_f = input_data.flange_width or d_web / 3
        t_f = input_data.flange_thickness or max(20.0, t_web * 2)
        results["sizing_method"] = "user_specified"

    results["initial_dimensions"] = {
        "web_depth_mm": d_web,
        "web_thickness_mm": t_web,
        "flange_width_mm": b_f,
        "flange_thickness_mm": t_f,
    }

    # -- section props --
    section = calculate_section_properties(d_web, t_web, b_f, t_f, fy=fy)

    # reclassify with actual fy
    section.section_class = classify_section(
        section.web_slenderness, section.flange_slenderness, fy
    )

    results["section_properties"] = {
        "total_depth_mm": section.total_depth,
        "area_mm2": section.area,
        "Ixx_mm4": section.moment_of_inertia_xx,
        "Iyy_mm4": section.moment_of_inertia_yy,
        "Zx_top_mm3": section.section_modulus_top,
        "Zx_bottom_mm3": section.section_modulus_bottom,
        "Zp_mm3": section.plastic_section_modulus,
        "centroid_from_bottom_mm": section.centroid_from_bottom,
        "section_class": section.section_class,
        "web_slenderness": section.web_slenderness,
        "flange_slenderness": section.flange_slenderness,
        "weight_per_m_kN": section.weight_per_meter,
    }

    results["material"] = {
        "steel_grade": input_data.steel_grade.value,
        "fy_MPa": fy,
        "fu_MPa": fu,
        "E_MPa": E_STEEL,
        "gamma_m0": GAMMA_M0,
        "gamma_m1": GAMMA_M1,
    }

    # -- dead load build-up --
    girder_self_weight = section.weight_per_meter  # kN/m per girder

    # typical 200mm RCC deck, 25 kN/m³
    deck_thickness_m = 0.200  # typical 200mm deck slab
    deck_width_per_girder = input_data.girder_spacing / 1000  # m
    deck_weight = 25.0 * deck_thickness_m * deck_width_per_girder  # kN/m

    # wearing surface (bituminous ≈ 22 kN/m³)
    wearing_coat_m = input_data.wearing_coat_thickness / 1000
    wearing_coat_weight = 22.0 * wearing_coat_m * deck_width_per_girder  # kN/m

    # cross-bracing adds roughly 5% to girder weight
    cross_beam_weight = 0.05 * girder_self_weight

    # barrier per girder (given total both sides)
    barrier_per_girder = input_data.crash_barrier_load / input_data.num_girders

    total_dead_load = girder_self_weight + deck_weight + cross_beam_weight
    total_superimposed = wearing_coat_weight + barrier_per_girder

    results["dead_loads"] = {
        "girder_self_weight_kN_m": round(girder_self_weight, 2),
        "deck_slab_kN_m": round(deck_weight, 2),
        "cross_beams_kN_m": round(cross_beam_weight, 2),
        "wearing_coat_kN_m": round(wearing_coat_weight, 2),
        "crash_barrier_kN_m": round(barrier_per_girder, 2),
        "total_dead_kN_m": round(total_dead_load, 2),
        "total_superimposed_kN_m": round(total_superimposed, 2),
    }

    # -- dead-load BM & SF (w·L²/8, w·L/2) --
    w_dead = total_dead_load + total_superimposed  # kN/m
    bm_dead = w_dead * span_m**2 / 8  # kN.m
    sf_dead = w_dead * span_m / 2      # kN (at support)

    results["dead_load_effects"] = {
        "total_udl_kN_m": round(w_dead, 2),
        "midspan_moment_kNm": round(bm_dead, 2),
        "support_shear_kN": round(sf_dead, 2),
    }

    # -- live-load --
    bm_live = 0.0
    sf_live = 0.0
    try:
        live_results = analyze_plate_girder(input_data)
        results["live_load_analysis"] = {
            k: round(v, 3) if isinstance(v, float) else v
            for k, v in live_results.items()
        }
        # crude distribution: lanes / girders
        dist_factor = input_data.num_lanes_loaded / input_data.num_girders
        bm_live = live_results.get("absolute_max_moment_kNm", 0) * dist_factor
        sf_live = live_results.get("max_shear_kN", 0) * dist_factor
        results["live_load_effects"] = {
            "max_moment_kNm": round(bm_live, 2),
            "max_shear_kN": round(sf_live, 2),
            "distribution_factor": round(dist_factor, 3),
        }
    except Exception as exc:
        results["warnings"].append(f"Live load analysis skipped: {exc}")

    # -- factored ULS forces (IRC:6 Table 1: γ_DL=1.35, γ_LL=1.50) --
    gamma_dl = 1.35
    gamma_ll = 1.50
    bm_factored = gamma_dl * bm_dead + gamma_ll * bm_live
    sf_factored = gamma_dl * sf_dead + gamma_ll * sf_live
    results["factored_design_forces"] = {
        "factored_moment_kNm": round(bm_factored, 2),
        "factored_shear_kN": round(sf_factored, 2),
        "gamma_dead": gamma_dl,
        "gamma_live": gamma_ll,
    }

    # -- moment capacity --
    # lateral bracing typically at cross-beam spacing
    unbraced_length = input_data.girder_spacing
    moment_results = calculate_moment_capacity(section, fy, unbraced_length)
    results["moment_capacity"] = moment_results

    # -- shear capacity --
    shear_results = calculate_shear_capacity(section, fy)
    results["shear_capacity"] = shear_results

    # -- deflection (SLS, unfactored) --
    w_sls = w_dead  # kN/m, unfactored for SLS
    w_sls_N_per_mm = w_sls  # kN/m = N/mm (1 kN/m = 1 N/mm)
    deflection_results = check_deflection(
        span_mm, section.moment_of_inertia_xx, w_sls_N_per_mm
    )
    results["deflection"] = deflection_results

    # -- diagnostics --
    eps = calculate_epsilon(fy)

    if section.web_slenderness > 200 * eps:
        results["warnings"].append(
            f"Web slenderness d/tw = {section.web_slenderness:.1f} exceeds 200ε"
            f" = {200 * eps:.1f}.  Intermediate transverse stiffeners needed."
        )

    if section.section_class == "slender":
        results["warnings"].append(
            "Section classified as SLENDER. Effective section properties should be "
            "used instead of gross section. Consider increasing flange or web thickness."
        )

    if section.section_class == "semi-compact":
        results["warnings"].append(
            "Section is semi-compact. Plastic section modulus cannot be fully "
            "utilized; elastic section modulus governs."
        )

    # Check moment adequacy against factored forces
    md_governing = moment_results.get("moment_capacity_governing_kNm", 0)
    if md_governing > 0 and bm_factored > md_governing:
        results["errors"].append(
            f"Factored moment {bm_factored:.1f} kN.m EXCEEDS capacity "
            f"{md_governing:.1f} kN.m. Section is inadequate."
        )

    # Check shear adequacy against factored forces
    vd = shear_results.get("design_shear_capacity_kN", 0)
    if vd > 0 and sf_factored > vd:
        results["errors"].append(
            f"Factored shear {sf_factored:.1f} kN EXCEEDS capacity "
            f"{vd:.1f} kN. Increase web thickness."
        )

    # Utilization ratios
    results["utilization"] = {
        "moment_ratio": round(bm_factored / md_governing, 3) if md_governing > 0 else 0,
        "shear_ratio": round(sf_factored / vd, 3) if vd > 0 else 0,
        "status": (
            "PASS"
            if (
                bm_factored <= md_governing
                and sf_factored <= vd
                and deflection_results.get("deflection_ok", True)
            )
            else "FAIL"
        ),
    }

    results["status"] = "completed"

    return results

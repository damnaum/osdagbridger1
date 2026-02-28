"""
Plate Girder Design Module as per IS 800:2007

Implements complete design workflow for steel plate girder bridge:
1. Initial sizing based on empirical rules and span
2. Section property calculation (area, I, Z, etc.)
3. Section classification (plastic/compact/semi-compact/slender)
4. Moment capacity check (section capacity + lateral-torsional buckling)
5. Shear capacity check (plastic or post-critical method)
6. Deflection serviceability check
7. Web bearing and buckling check

Reference:
    IS 800:2007 - General Construction in Steel
    IRC:24-2010 - Steel Road Bridges
"""

import math
from typing import Tuple, Optional, Dict, Any, Literal

from .dto import PlateGirderInput, PlateGirderSection, SteelGrade
from .analyser import analyze_plate_girder


# ──────────────────────────────────────────────────────────────
# Material constants (IS 800:2007, Clause 2.2)
# ──────────────────────────────────────────────────────────────
E_STEEL = 200_000.0  # MPa  (Young's modulus of structural steel)
G_STEEL = 76_923.0   # MPa  (Shear modulus, E / 2(1+ν), ν=0.3)
GAMMA_M0 = 1.10      # Partial safety factor for material (yielding, Cl. 5.4.1)
GAMMA_M1 = 1.25      # Partial safety factor (buckling, Cl. 5.4.1)
DENSITY_STEEL = 78.5  # kN/m³


def calculate_epsilon(fy: float) -> float:
    """
    Calculate epsilon factor for section classification.

    ε = √(250/fy)

    This factor is used throughout IS 800:2007 for
    normalizing slenderness limits across steel grades.

    Args:
        fy: Yield strength of steel in MPa

    Returns:
        Epsilon factor (1.0 for E250 grade)

    Example:
        >>> calculate_epsilon(250)
        1.0
        >>> calculate_epsilon(350)
        0.845
    """
    return math.sqrt(250.0 / fy)


def initial_sizing(input_data: PlateGirderInput) -> Tuple[float, float, float, float]:
    """
    Calculate initial plate girder dimensions based on empirical rules.

    Thumb rules for simply supported steel plate girders:
    - Overall depth: L/12 to L/15 (deeper for heavier loads)
    - Web thickness: d/180 to d/200 (to avoid stiffeners if possible)
    - Flange width: b = d/3 to d/4
    - Flange thickness: tf = 1.5*tw to 2.5*tw

    These are starting points; the designer module iterates if checks fail.

    Args:
        input_data: PlateGirderInput with span and loading info

    Returns:
        Tuple of (web_depth, web_thickness, flange_width, flange_thickness) in mm
    """
    span = input_data.effective_span  # mm
    fy = input_data.get_yield_strength()
    epsilon = calculate_epsilon(fy)

    # Estimate overall depth based on span-to-depth ratio
    # For highway bridges with Class A/70R, use L/12 to L/14
    if input_data.live_load_class == "CLASS_70R":
        depth_factor = 12  # More conservative for heavy loads
    elif input_data.live_load_class == "CLASS_AA":
        depth_factor = 13
    else:
        depth_factor = 14  # Class A is lighter

    overall_depth = span / depth_factor

    # Round to practical dimensions (nearest 50mm for fabrication)
    overall_depth = math.ceil(overall_depth / 50) * 50

    # Initial flange thickness estimate (will be refined)
    flange_thickness = max(20.0, overall_depth / 40)  # Rough estimate
    flange_thickness = math.ceil(flange_thickness / 2) * 2  # Round to even mm

    # Web depth (clear between flanges)
    web_depth = overall_depth - 2 * flange_thickness

    # Web thickness - try to keep d/tw < 200*epsilon to avoid transverse stiffeners
    # But not less than 8mm for weldability
    min_web_thickness = max(8.0, web_depth / (200 * epsilon))
    web_thickness = math.ceil(min_web_thickness / 2) * 2  # Round to even mm

    # Minimum 8mm for practical fabrication
    # Thinner webs cause distortion during welding
    web_thickness = max(8.0, web_thickness)

    # Flange width - typically d/3 to d/4
    flange_width = web_depth / 3

    # Check flange outstand limit:
    # (bf - tw)/(2*tf) should be < 8.4*epsilon for compact section
    max_outstand = 8.4 * epsilon * flange_thickness
    max_flange_width = 2 * max_outstand + web_thickness

    flange_width = min(flange_width, max_flange_width)
    flange_width = math.ceil(flange_width / 10) * 10  # Round to 10mm

    # Minimum flange width for practical considerations (welding access, stability)
    flange_width = max(200.0, flange_width)

    return web_depth, web_thickness, flange_width, flange_thickness


def calculate_section_properties(
    d_web: float,
    t_web: float,
    b_tf: float,
    t_tf: float,
    b_bf: float = None,
    t_bf: float = None,
    fy: float = 250.0,
) -> PlateGirderSection:
    """
    Calculate section properties for plate girder.

    Assumes doubly symmetric section if bottom flange not specified.
    Uses parallel axis theorem for moment of inertia calculation.

    Args:
        d_web: Web depth (clear between flanges) in mm
        t_web: Web thickness in mm
        b_tf: Top flange width in mm
        t_tf: Top flange thickness in mm
        b_bf: Bottom flange width (default = top flange) in mm
        t_bf: Bottom flange thickness (default = top flange) in mm
        fy: Yield strength in MPa (used for section classification)

    Returns:
        PlateGirderSection with all computed properties

    Example:
        >>> sec = calculate_section_properties(1500, 12, 400, 25)
        >>> sec.total_depth
        1550.0
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
    """
    Classify section as per IS 800:2007, Table 2.

    Classification determines the design approach:
    - Plastic: Can form plastic hinge, use Zp
    - Compact: Can reach yield stress, use Zp with reduced rotation capacity
    - Semi-compact: Local buckling may occur after yield, use Ze
    - Slender: Local buckling governs, use effective section properties

    The section class is governed by the MOST SLENDER element
    (either web or compression flange).

    Args:
        web_slenderness: d/tw ratio
        flange_slenderness: (b-tw)/(2*tf) ratio for outstand flange
        fy: Yield strength in MPa

    Returns:
        Section classification string

    Example:
        >>> classify_section(50, 5, 250)
        'plastic'
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
    """
    Calculate moment capacity as per IS 800:2007, Clause 8.2.

    Two checks are performed:
    1. Section capacity: Md = βb * Zp * fy / γm0 (laterally supported)
    2. Lateral-torsional buckling: Md = χLT * Zp * fy / γm1

    The governing (lower) capacity controls the design.

    Args:
        section: PlateGirderSection with computed properties
        fy: Yield strength (MPa)
        unbraced_length: Laterally unbraced length in mm
            (typically cross-beam spacing for bridge girders)
        effective_length_factor: K factor for LTB (1.0 for simply supported)

    Returns:
        Dictionary with moment capacities and intermediate values:
        - moment_capacity_section_kNm: Section plastic/elastic capacity
        - moment_capacity_ltb_kNm: Capacity considering LTB
        - moment_capacity_governing_kNm: Min of above (design capacity)
        - lambda_lt: Non-dimensional LTB slenderness
        - chi_lt: LTB reduction factor

    Reference: IS 800:2007, Clause 8.2.1 and 8.2.2
    """
    results = {}

    # ── Step 1: Plastic/elastic moment capacity (Clause 8.2.1.2) ──
    if section.section_class in ("plastic", "compact"):
        # Use plastic section modulus
        beta_b = 1.0  # For plastic/compact sections
        m_d = beta_b * section.plastic_section_modulus * fy / GAMMA_M0
    else:
        # Use elastic section modulus for semi-compact/slender
        z_elastic = min(section.section_modulus_top, section.section_modulus_bottom)
        m_d = z_elastic * fy / GAMMA_M0

    results["moment_capacity_section_kNm"] = m_d / 1e6  # N.mm to kN.m

    # ── Step 2: Lateral-torsional buckling check (Clause 8.2.2) ──
    if unbraced_length > 0:
        # Effective length for LTB
        l_lt = effective_length_factor * unbraced_length

        # Section dimensions
        h = section.total_depth
        i_y = section.moment_of_inertia_yy

        # Torsional constant (St. Venant) for open I-section
        # It ≈ Σ(bt³/3) for thin rectangles
        i_t = (
            section.top_flange_width * section.top_flange_thickness**3
            + section.bottom_flange_width * section.bottom_flange_thickness**3
            + section.web_depth * section.web_thickness**3
        ) / 3

        # Warping constant for symmetric I-section
        # Iw = Iy * h² / 4
        i_w = i_y * h**2 / 4

        # Elastic critical moment (Mcr) for uniform moment
        # Mcr = (π²EIy / Llt²) * √[(Iw/Iy) + (Llt²·G·It)/(π²·E·Iy)]
        term1 = math.pi**2 * E_STEEL * i_y / l_lt**2
        term2_inside = i_w / i_y + (l_lt**2 * G_STEEL * i_t) / (
            math.pi**2 * E_STEEL * i_y
        )

        # Guard against negative values due to numerical issues
        if term2_inside <= 0:
            m_cr = float("inf")
        else:
            m_cr = term1 * math.sqrt(term2_inside)

        results["critical_moment_kNm"] = m_cr / 1e6

        # Non-dimensional slenderness ratio
        # λLT = √(βb · Zp · fy / Mcr)
        lambda_lt = math.sqrt(section.plastic_section_modulus * fy / m_cr)
        results["lambda_lt"] = lambda_lt

        # Design bending strength (Clause 8.2.2)
        # Imperfection parameter αLT depends on section type
        # For h/bf <= 2: αLT = 0.21 (rolled), 0.49 (welded)
        # For h/bf > 2:  αLT = 0.34 (rolled), 0.76 (welded)
        # Plate girders are always welded sections
        if section.total_depth / section.top_flange_width <= 2:
            alpha_lt = 0.49  # Welded, h/bf <= 2
        else:
            alpha_lt = 0.76  # Welded, h/bf > 2

        # ΦLT = 0.5 * [1 + αLT(λLT - 0.2) + λLT²]
        phi_lt = 0.5 * (1 + alpha_lt * (lambda_lt - 0.2) + lambda_lt**2)

        # χLT = 1 / (ΦLT + √(ΦLT² - λLT²)) but χLT ≤ 1.0
        discriminant = phi_lt**2 - lambda_lt**2
        if discriminant <= 0:
            chi_lt = 1.0  # Very short unbraced length, no reduction
        else:
            chi_lt = min(1.0, 1.0 / (phi_lt + math.sqrt(discriminant)))

        results["alpha_lt"] = alpha_lt
        results["phi_lt"] = phi_lt
        results["chi_lt"] = chi_lt

        # Design moment considering LTB
        # Md = χLT * βb * Zp * fy / γm1
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
    stiffener_spacing: float = None,
) -> Dict[str, float]:
    """
    Calculate shear capacity as per IS 800:2007, Clause 8.4.

    Two methods depending on web slenderness:
    1. Plastic shear (d/tw ≤ 67ε): Full plastic shear capacity
    2. Post-critical method (d/tw > 67ε): Shear buckling governs

    For stiffened webs, tension field action can increase capacity.

    Args:
        section: PlateGirderSection object
        fy: Yield strength (MPa)
        stiffener_spacing: Spacing of transverse stiffeners (mm)
            None means unstiffened web

    Returns:
        Dictionary with shear capacities and intermediate checks:
        - plastic_shear_capacity_kN: Full plastic shear
        - design_shear_capacity_kN: Governing shear (may be reduced)
        - method: "plastic" or "post-critical"
        - buckling_check_required: True if d/tw > 67ε

    Reference: IS 800:2007, Clause 8.4.1 and 8.4.2
    """
    results = {}

    d = section.web_depth
    t_w = section.web_thickness

    # Shear area (Clause 8.4.1.1 - for welded I-section, Av = d * tw)
    a_v = d * t_w

    # Yield shear strength from von Mises criterion
    # τy = fy / √3
    f_yw = fy / math.sqrt(3)

    # Plastic shear capacity
    # Vp = Av * fyw / γm0
    v_p = a_v * f_yw / GAMMA_M0
    results["plastic_shear_capacity_kN"] = v_p / 1000

    # Web slenderness
    lambda_w = d / t_w
    epsilon = calculate_epsilon(fy)
    results["web_slenderness"] = lambda_w
    results["epsilon"] = epsilon

    # Clause 8.4.2: If d/tw ≤ 67ε, no shear buckling check needed
    critical_slenderness = 67 * epsilon

    if lambda_w <= critical_slenderness:
        # Stocky web - full plastic shear capacity
        results["design_shear_capacity_kN"] = results["plastic_shear_capacity_kN"]
        results["method"] = "plastic"
        results["buckling_check_required"] = False
    else:
        # Slender web - shear buckling governs
        results["buckling_check_required"] = True

        # Shear buckling coefficient kv (Clause 8.4.2.2)
        if stiffener_spacing is None or stiffener_spacing > d:
            # Unstiffened web or very wide stiffener spacing
            k_v = 5.35
            results["stiffening"] = "unstiffened"
        else:
            # Stiffened web: kv = 5.35 + 4/(c/d)²
            c = stiffener_spacing
            ratio = c / d
            k_v = 5.35 + 4.0 / ratio**2
            results["stiffening"] = f"stiffened at {c:.0f}mm"

        results["k_v"] = k_v

        # Elastic critical shear stress
        # τcr,e = kv * π²E / [12(1-ν²)] * (tw/d)²
        poisson = 0.3  # Poisson's ratio for steel
        tau_cr_e = (
            k_v * math.pi**2 * E_STEEL / (12 * (1 - poisson**2)) * (t_w / d) ** 2
        )
        results["tau_cr_elastic"] = tau_cr_e

        # Non-dimensional web slenderness for shear
        # λw = √(fyw / τcr,e)
        lambda_w_shear = math.sqrt(f_yw / tau_cr_e) if tau_cr_e > 0 else 999.0
        results["lambda_w_shear"] = lambda_w_shear

        # Shear buckling strength τb (Clause 8.4.2.2, Table 14)
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
    """
    Check deflection under serviceability loads.

    Maximum deflection for simply supported beam under UDL:
        δ = 5wL⁴ / (384EI)

    For point load at midspan:
        δ = PL³ / (48EI)

    Allowable deflection: L/600 for highway bridges (IRC:24-2010).

    Args:
        span: Effective span in mm
        moment_of_inertia: I_xx in mm⁴
        total_udl_sls: Total serviceability UDL in N/mm (kN/m * 1000)
        max_point_load_sls: Maximum point load at midspan in N

    Returns:
        Dictionary with deflection values and pass/fail
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
    """
    Check web bearing (crippling) at support as per IS 800:2007, Cl. 8.7.4.

    Web crippling can occur at concentrated load or reaction points.
    A bearing stiffener is required if the web bearing capacity is exceeded.

    Args:
        section: PlateGirderSection
        fy: Yield strength (MPa)
        bearing_length: Length of stiff bearing at support (mm)
        reaction: Support reaction force (kN)

    Returns:
        Dictionary with bearing capacity and check result
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
    """
    Complete plate girder design workflow.

    Steps:
    1. Calculate initial sizing (or use user-provided dimensions)
    2. Compute section properties (area, I, Z, classification)
    3. Estimate dead loads (self-weight + superimposed)
    4. Check moment capacity (section + LTB)
    5. Check shear capacity (plastic or post-critical)
    6. Check deflection (SLS)
    7. Generate summary with pass/fail status

    Args:
        input_data: PlateGirderInput with all design parameters

    Returns:
        Complete design results dictionary with:
        - input: Echoed input parameters
        - initial_dimensions: Web/flange sizes
        - section_properties: Area, I, Z, class
        - dead_loads: Self-weight and superimposed
        - moment_capacity: Md with all checks
        - shear_capacity: Vd with all checks
        - deflection: Serviceability check
        - status: "completed" or "failed"
        - warnings: List of advisory messages
        - errors: List of critical issues

    Example:
        >>> inp = PlateGirderInput(
        ...     project_name="Test", bridge_name="B1",
        ...     effective_span=30000, girder_spacing=3000)
        >>> result = design_plate_girder(inp)
        >>> result["status"]
        'completed'
    """
    results = {
        "input": input_data.model_dump(),
        "status": "in_progress",
        "warnings": [],
        "errors": [],
    }

    fy = input_data.get_yield_strength()
    # fu reserved for future connection design checks
    fu = input_data.get_ultimate_strength()  # noqa: F841
    span_mm = input_data.effective_span
    span_m = span_mm / 1000

    # ── Step 1: Initial sizing or use provided dimensions ──
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

    # ── Step 2: Section properties ──
    section = calculate_section_properties(d_web, t_web, b_f, t_f, fy=fy)

    # Re-classify with actual fy (initial classification used 250)
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

    # ── Step 3: Dead load estimation ──
    girder_self_weight = section.weight_per_meter  # kN/m per girder

    # Deck slab weight (assuming 200mm thick RCC slab, 25 kN/m³)
    deck_thickness_m = 0.200  # typical 200mm deck slab
    deck_width_per_girder = input_data.girder_spacing / 1000  # m
    deck_weight = 25.0 * deck_thickness_m * deck_width_per_girder  # kN/m

    # Wearing coat (bituminous, ~22 kN/m³)
    wearing_coat_m = input_data.wearing_coat_thickness / 1000
    wearing_coat_weight = 22.0 * wearing_coat_m * deck_width_per_girder  # kN/m

    # Cross beams (estimate 5% of girder weight)
    cross_beam_weight = 0.05 * girder_self_weight

    # Crash barrier / parapet (given as UDL)
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

    # ── Step 4: Design moments and shears (simplified UDL approximation) ──
    # Dead load BM at midspan: wL²/8
    w_dead = total_dead_load + total_superimposed  # kN/m
    bm_dead = w_dead * span_m**2 / 8  # kN.m
    sf_dead = w_dead * span_m / 2      # kN (at support)

    results["dead_load_effects"] = {
        "total_udl_kN_m": round(w_dead, 2),
        "midspan_moment_kNm": round(bm_dead, 2),
        "support_shear_kN": round(sf_dead, 2),
    }

    # ── Step 4b: Live load effects (moving load analysis) ──
    bm_live = 0.0
    sf_live = 0.0
    try:
        live_results = analyze_plate_girder(input_data)
        results["live_load_analysis"] = {
            k: round(v, 3) if isinstance(v, float) else v
            for k, v in live_results.items()
        }
        # Approximate girder distribution factor
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

    # ── Step 4c: Factored design forces (ULS) ──
    # IRC:6-2017 Table 1 — γ_DL=1.35, γ_LL=1.50
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

    # ── Step 5: Moment capacity check ──
    # For bridge girders, lateral bracing is at cross-beam locations
    # Assume unbraced length = girder spacing (cross-beam spacing)
    unbraced_length = input_data.girder_spacing
    moment_results = calculate_moment_capacity(section, fy, unbraced_length)
    results["moment_capacity"] = moment_results

    # ── Step 6: Shear capacity check ──
    shear_results = calculate_shear_capacity(section, fy)
    results["shear_capacity"] = shear_results

    # ── Step 7: Deflection check ──
    # SLS deflection (unfactored dead load only for now)
    w_sls = w_dead  # kN/m, unfactored for SLS
    w_sls_N_per_mm = w_sls  # kN/m = N/mm (1 kN/m = 1 N/mm)
    deflection_results = check_deflection(
        span_mm, section.moment_of_inertia_xx, w_sls_N_per_mm
    )
    results["deflection"] = deflection_results

    # ── Warnings and diagnostics ──
    epsilon = calculate_epsilon(fy)

    if section.web_slenderness > 200 * epsilon:
        results["warnings"].append(
            f"Web slenderness d/tw = {section.web_slenderness:.1f} exceeds 200ε "
            f"= {200 * epsilon:.1f}. Intermediate transverse stiffeners required."
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

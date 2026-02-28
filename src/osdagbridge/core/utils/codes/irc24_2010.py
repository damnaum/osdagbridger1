"""
IRC:24-2010 — Standard Specifications for Road Bridges
Section V: Steel Road Bridges (Limit State Method)

Provides deflection limits, bearing stiffener checks, and web panel design.
Reference: IRC:24-2010
"""


def get_deflection_limit(span: float, load_type: str = "live") -> float:
    """Get allowable deflection limit for steel bridge girders.

    Args:
        span: Effective span in mm
        load_type: 'live' for live load only, 'total' for total load

    Returns:
        Allowable deflection in mm

    Reference: IRC:24-2010, Clause 504.5
    """
    if load_type == "live":
        return span / 600  # L/600 for live load deflection
    return span / 400  # L/400 for total deflection


def get_web_panel_shear_capacity(
    d: float, tw: float, fy: float, c: float, gamma_m0: float = 1.10
) -> float:
    """Simple post-critical shear capacity of an unstiffened web panel.

    Uses IS 800:2007 Clause 8.4.2 simplified approach.

    Args:
        d: Web depth in mm
        tw: Web thickness in mm
        fy: Yield strength in MPa
        c: Stiffener spacing in mm (use span if no stiffeners)
        gamma_m0: Partial safety factor

    Returns:
        Design shear capacity in kN
    """
    import math

    tau_cr_e = get_elastic_shear_buckling_stress(d, tw, c)
    lambda_w = (
        math.sqrt(fy / (math.sqrt(3) * tau_cr_e)) if tau_cr_e > 0 else 999
    )
    if lambda_w <= 0.8:
        tau_b = fy / math.sqrt(3)
    elif lambda_w <= 1.2:
        tau_b = (1 - 0.8 * (lambda_w - 0.8)) * fy / math.sqrt(3)
    else:
        tau_b = fy / (math.sqrt(3) * lambda_w ** 2)
    return d * tw * tau_b / (gamma_m0 * 1000)  # kN


def get_elastic_shear_buckling_stress(
    d: float, tw: float, c: float
) -> float:
    """Elastic critical shear stress of web panel.

    Args:
        d: Web depth in mm
        tw: Web thickness in mm
        c: Stiffener spacing in mm

    Returns:
        Elastic critical shear stress in MPa

    Reference: IS 800:2007, Clause 8.4.2.2
    """
    import math

    if c <= 0 or d <= 0 or tw <= 0:
        return 0.0
    ratio = c / d
    if ratio < 1:
        kv = 4.0 + 5.35 / ratio ** 2
    else:
        kv = 5.35 + 4.0 / ratio ** 2
    E = 200_000.0  # MPa
    nu = 0.3
    tau_cr = kv * math.pi ** 2 * E / (12 * (1 - nu ** 2) * (d / tw) ** 2)
    return tau_cr


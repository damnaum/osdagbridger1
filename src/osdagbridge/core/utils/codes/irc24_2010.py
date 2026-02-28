"""
IRC:24-2010 — Steel Road Bridges (Limit State Method).

Deflection limits, web-panel shear, and elastic buckling stress
per IS 800:2007 Cl. 8.4.2.
"""


def get_deflection_limit(span: float, load_type: str = "live") -> float:
    """Allowable deflection for a steel bridge girder (Cl. 504.5)."""
    if load_type == "live":
        return span / 600  # L/600 for live load deflection
    return span / 400  # L/400 for total deflection


def get_web_panel_shear_capacity(
    d: float, tw: float, fy: float, c: float, gamma_m0: float = 1.10
) -> float:
    """Post-critical shear capacity of an unstiffened web panel (kN)."""
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
    """Elastic critical shear stress τ_cr of a web panel (MPa)."""
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


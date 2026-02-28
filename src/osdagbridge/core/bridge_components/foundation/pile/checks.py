"""Pile capacity checks.

Simplified static-formula approach for bored cast-in-situ piles
in cohesive soil (IS 2911 Part 1/Sec 2).
"""
from .geometry import PileGeometry


def axial_capacity(
    pile: PileGeometry,
    cu: float = 50.0,
    nc: float = 9.0,
    alpha: float = 0.45,
    factor_of_safety: float = 2.5,
) -> dict:
    """Estimate safe axial bearing capacity.

    Uses IS 2911 (Part 1/Sec 2) — static formula for bored piles
    in cohesive soil.

    Q_ult = α·cu·As  +  Nc·cu·Ab
    Q_safe = Q_ult / FoS

    Args:
        pile: PileGeometry instance.
        cu: Undrained cohesion of soil (kPa).
        nc: Bearing capacity factor (default 9).
        alpha: Adhesion factor for shaft friction (default 0.45).
        factor_of_safety: FoS (default 2.5).

    Returns:
        dict with ultimate and safe capacities in kN.
    """
    # Convert to consistent SI (m, kN)
    area_m2 = pile.cross_section_area * 1e-6
    shaft_area_m2 = pile.surface_area_embedded * 1e-6

    q_shaft = alpha * cu * shaft_area_m2       # kN
    q_base = nc * cu * area_m2                 # kN
    q_ult = q_shaft + q_base
    q_safe = q_ult / factor_of_safety

    return {
        "shaft_capacity_kN": round(q_shaft, 1),
        "base_capacity_kN": round(q_base, 1),
        "ultimate_capacity_kN": round(q_ult, 1),
        "safe_capacity_kN": round(q_safe, 1),
        "factor_of_safety": factor_of_safety,
    }


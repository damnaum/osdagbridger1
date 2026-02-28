"""Static-formula pile capacity (IS 2911 Part 1/Sec 2).

Only cohesive soil for now — granular layers need additional work.
"""
from .geometry import PileGeometry


def axial_capacity(
    pile: PileGeometry,
    cu: float = 50.0,
    nc: float = 9.0,
    alpha: float = 0.45,
    factor_of_safety: float = 2.5,
) -> dict:
    """Safe bearing capacity via shaft friction + end bearing."""
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


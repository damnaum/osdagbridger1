"""Basic pier slenderness & axial checks (IS 456).

Seismic detailing is out of scope for now.
"""
import math

from .geometry import PierGeometry


def check_slenderness(pier: PierGeometry, effective_length_factor: float = 1.0) -> dict:
    """Slenderness ratio and short/long classification."""
    if pier.shape == "circular":
        radius_of_gyration = pier.breadth / 4  # r = D/4 for circle
    else:
        radius_of_gyration = pier.breadth / math.sqrt(12)

    effective_length = effective_length_factor * pier.height
    slenderness = effective_length / radius_of_gyration

    return {
        "slenderness_ratio": round(slenderness, 2),
        "radius_of_gyration_mm": round(radius_of_gyration, 2),
        "classification": "short" if slenderness < 12 else "long",
        "limit_short": 12,
    }


def check_axial_capacity(
    pier: PierGeometry,
    fck: float = 30.0,
    axial_load_kN: float = 0.0,
) -> dict:
    """Quick axial capacity estimate (IS 456 Cl. 39.3, ignoring rebar)."""
    area_mm2 = pier.cross_section_area
    # Simplified: Pu = 0.4 * fck * Ac (ignoring steel contribution)
    capacity_n = 0.4 * fck * area_mm2
    capacity_kn = capacity_n / 1000

    return {
        "axial_capacity_kN": round(capacity_kn, 1),
        "applied_load_kN": axial_load_kN,
        "utilisation": round(axial_load_kN / capacity_kn, 3) if capacity_kn > 0 else 0,
        "ok": axial_load_kN <= capacity_kn,
    }


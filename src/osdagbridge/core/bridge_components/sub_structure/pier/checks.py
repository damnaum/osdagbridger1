"""Pier capacity checks.

Basic axial and slenderness checks for RC piers. Full seismic
design is out of scope for v0.1.
"""
import math

from .geometry import PierGeometry


def check_slenderness(pier: PierGeometry, effective_length_factor: float = 1.0) -> dict:
    """Check pier slenderness ratio.

    Args:
        pier: PierGeometry instance.
        effective_length_factor: K factor (1.0 for pinned-pinned).

    Returns:
        dict with slenderness ratio, classification, and limit.
    """
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
    """Simplified axial capacity check for RC pier (IS 456 Clause 39.3).

    Args:
        pier: PierGeometry.
        fck: Characteristic concrete strength (MPa).
        axial_load_kN: Applied axial load (kN).

    Returns:
        dict with capacity and utilisation.
    """
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


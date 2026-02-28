"""Unit conversion utilities for bridge engineering.

All internal calculations use: mm, kN, MPa, kN·m
These helpers convert to/from common external units.
"""


def m_to_mm(value: float) -> float:
    """Convert meters to millimeters."""
    return value * 1000.0


def mm_to_m(value: float) -> float:
    """Convert millimeters to meters."""
    return value / 1000.0


def kn_to_n(value: float) -> float:
    """Convert kilonewtons to newtons."""
    return value * 1000.0


def n_to_kn(value: float) -> float:
    """Convert newtons to kilonewtons."""
    return value / 1000.0


def knm_to_nmm(value: float) -> float:
    """Convert kN·m to N·mm (for stress calculations)."""
    return value * 1e6


def nmm_to_knm(value: float) -> float:
    """Convert N·mm to kN·m."""
    return value / 1e6


def mpa_to_kn_per_m2(value: float) -> float:
    """Convert MPa to kN/m²."""
    return value * 1000.0


def deg_to_rad(value: float) -> float:
    """Convert degrees to radians."""
    import math
    return value * math.pi / 180.0


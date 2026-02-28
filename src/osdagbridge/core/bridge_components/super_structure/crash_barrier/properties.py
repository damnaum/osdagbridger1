"""Crash barrier mechanical properties.

Provides default UDL values used in bridge dead-load estimates.
"""

from __future__ import annotations

# Typical crash barrier self-weight UDL (kN/m) — IRC Type P-3
DEFAULT_BARRIER_UDL = 10.0  # kN/m per side


def barrier_udl(height_mm: float = 900.0) -> float:
    """Estimate barrier UDL from height (kN/m)."""
    # Rough linear interpolation
    return (height_mm / 900.0) * DEFAULT_BARRIER_UDL

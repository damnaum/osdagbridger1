"""Native lightweight beam solver for simply supported spans.

Implements equilibrium-based shear/moment and numerical double-integration
for deflection.  Sufficient for preliminary design — use OpenSees or
OspGrillage for detailed analysis.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


def solve_simply_supported_beam(
    span: float,
    point_loads: Optional[List[Tuple[float, float]]] = None,
    udl: float = 0.0,
    EI: float = 1.0,
    num_points: int = 201,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Solve a simply supported beam under given loading.

    Args:
        span: Beam span in mm
        point_loads: List of (position_mm, force_kN) tuples
        udl: Uniformly distributed load in kN/mm
        EI: Flexural rigidity in N·mm²
        num_points: Number of output points along span

    Returns:
        Tuple of (positions, shear_force, bending_moment, deflection) arrays
        positions in mm, SF in kN, BM in kN·mm, deflection in mm
    """
    if point_loads is None:
        point_loads = []

    x = np.linspace(0, span, num_points)
    sf = np.zeros_like(x)
    bm = np.zeros_like(x)
    deflection = np.zeros_like(x)

    # Reaction at left support (sum moments about right)
    ra = 0.0
    for pos, load in point_loads:
        ra += load * (span - pos) / span
    ra += udl * span / 2

    # rb is implicit: sum(loads) + udl*span - ra

    for i, xi in enumerate(x):
        # Shear force
        v = ra - udl * xi
        for pos, load in point_loads:
            if xi >= pos:
                v -= load
        sf[i] = v

        # Bending moment
        m = ra * xi - udl * xi ** 2 / 2
        for pos, load in point_loads:
            if xi >= pos:
                m -= load * (xi - pos)
        bm[i] = m

    # Deflection by double-integration of M/EI using trapezoidal rule,
    # enforcing zero deflection at both supports (x=0 and x=L).
    if EI > 0:
        dx = span / (num_points - 1)
        curvature = bm / EI  # 1/mm

        # First integration → slope (up to an unknown constant C1)
        slope = np.zeros_like(x)
        for i in range(1, num_points):
            slope[i] = slope[i - 1] + 0.5 * (curvature[i - 1] + curvature[i]) * dx

        # Second integration → deflection (up to C1*x + C2)
        raw_defl = np.zeros_like(x)
        for i in range(1, num_points):
            raw_defl[i] = raw_defl[i - 1] + 0.5 * (slope[i - 1] + slope[i]) * dx

        # Boundary conditions: deflection = 0 at x = 0 and x = L
        # raw_defl already has raw_defl[0] = 0, subtract linear ramp to
        # force raw_defl[-1] = 0.
        correction = np.linspace(0, raw_defl[-1], num_points)
        deflection = raw_defl - correction

    return x, sf, bm, deflection


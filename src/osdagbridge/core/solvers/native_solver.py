"""Native lightweight beam solver for simply supported spans.

Implements direct stiffness method for single-span beams.
Sufficient for preliminary design — use OpenSees/OspGrillage for detailed analysis.
"""
import numpy as np
from typing import Tuple


def solve_simply_supported_beam(
    span: float,
    point_loads: list = None,
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

    rb = sum(p[1] for p in point_loads) + udl * span - ra  # noqa: F841

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

    # Deflection by numerical double integration (trapezoidal rule) of M/EI
    if EI > 0:
        dx = span / (num_points - 1)
        curvature = bm / EI  # 1/mm

        # First integration: slope
        slope = np.cumsum(curvature) * dx

        # Second integration: deflection
        deflection = np.cumsum(slope) * dx

        # Apply boundary conditions (zero deflection at supports)
        deflection -= np.linspace(deflection[0], deflection[-1], num_points)

    return x, sf, bm, deflection


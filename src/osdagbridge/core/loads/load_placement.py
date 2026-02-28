"""Load placement utilities for multi-lane bridge analysis.

Determines transverse placement of vehicles on the bridge deck
and calculates the distribution to individual girders using
Courbon's method (rigid deck assumption).

Reference:
    Courbon's theory for transverse load distribution in beam bridges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class LanePlacement:
    """Transverse position of a vehicle lane on the bridge deck.

    Attributes:
        lane_number: Lane index (1-based).
        eccentricity: Distance from bridge deck centroid (mm).
            Positive = towards right looking in traffic direction.
        vehicle_type: IRC vehicle designation ('CLASS_A', 'CLASS_70R', etc.).
    """

    lane_number: int
    eccentricity: float  # mm from bridge centerline
    vehicle_type: str


def calculate_girder_distribution(
    girder_spacing: float,
    num_girders: int,
    lane_placements: List[LanePlacement],
) -> List[float]:
    """Calculate distribution factors for each girder using Courbon's method.

    Courbon's method assumes a rigid deck and gives the reaction on each
    girder *i* as:

        R_i = (P / n) * [1 + (n * Σe_j * x_i) / (P * Σx_k²)]

    where
        P  = total number of unit loads (= number of lanes loaded),
        n  = number of girders,
        e_j = eccentricity of lane *j*,
        x_i = position of girder *i* from deck centroid,
        Σx_k² = sum of squared girder positions.

    Args:
        girder_spacing: C/c spacing of girders in mm.
        num_girders: Number of main girders.
        lane_placements: List of lane eccentricities.

    Returns:
        List of distribution factors for each girder.  The sum of all
        factors equals the number of lanes loaded.

    Raises:
        ValueError: If *num_girders* < 1 or *girder_spacing* <= 0.
    """
    if num_girders < 1:
        raise ValueError("num_girders must be >= 1")
    if girder_spacing <= 0:
        raise ValueError("girder_spacing must be > 0")
    if not lane_placements:
        return [0.0] * num_girders

    # Girder positions relative to deck centroid
    total_width = (num_girders - 1) * girder_spacing
    x_positions = [
        i * girder_spacing - total_width / 2 for i in range(num_girders)
    ]

    sum_x_sq = sum(x ** 2 for x in x_positions)

    num_lanes = len(lane_placements)

    # Sum of eccentricities of all loaded lanes
    sum_eccentricity = sum(lp.eccentricity for lp in lane_placements)

    factors: List[float] = []
    for x_i in x_positions:
        if sum_x_sq > 0:
            # Courbon's formula
            factor = (num_lanes / num_girders) * (
                1.0 + num_girders * sum_eccentricity * x_i / (num_lanes * sum_x_sq)
            )
        else:
            # Single girder or all girders coincide at centroid
            factor = num_lanes / num_girders
        # Negative distribution factor is physically meaningless
        factors.append(max(0.0, factor))

    return factors


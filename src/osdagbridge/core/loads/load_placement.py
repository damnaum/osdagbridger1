"""Load placement utilities for multi-lane bridge analysis.

Determines transverse placement of vehicles on the bridge deck
and calculates the distribution to individual girders.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class LanePlacement:
    """Transverse position of a vehicle lane on the bridge deck."""

    lane_number: int
    eccentricity: float  # mm from bridge centerline
    vehicle_type: str


def calculate_girder_distribution(
    girder_spacing: float,
    num_girders: int,
    lane_placements: List[LanePlacement],
) -> List[float]:
    """Calculate distribution factors for each girder using Courbon's method.

    Courbon's method assumes rigid deck and gives reaction on each girder as:
        Ri = (P/n) * [1 + (n * ei * xi) / Σ(xi²)]

    Args:
        girder_spacing: C/c spacing of girders in mm
        num_girders: Number of main girders
        lane_placements: List of lane eccentricities

    Returns:
        List of distribution factors for each girder (sum should equal num_lanes)
    """
    # Girder positions relative to deck centroid
    total_width = (num_girders - 1) * girder_spacing
    x_positions = [
        i * girder_spacing - total_width / 2 for i in range(num_girders)
    ]

    sum_x_sq = sum(x ** 2 for x in x_positions)

    total_load = len(lane_placements)  # Unit load per lane
    total_eccentricity = sum(lp.eccentricity for lp in lane_placements)

    factors = []
    for x_i in x_positions:
        if sum_x_sq > 0:
            factor = (total_load / num_girders) * (
                1
                + num_girders
                * total_eccentricity
                * x_i
                / (total_load * sum_x_sq)
            )
        else:
            factor = total_load / num_girders
        factors.append(max(0.0, factor))

    return factors


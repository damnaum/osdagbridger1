"""Transverse load distribution — Courbon's theory.

Figures out how much load each girder picks up when vehicles
are placed at various eccentricities on the deck.  Assumes
the slab is rigid enough to qualify as a Courbon's distribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class LanePlacement:
    """One loaded lane's transverse position on the deck.

    ``eccentricity`` is measured from the deck centreline (mm);
    positive = right-hand side looking in the direction of traffic.
    """

    lane_number: int
    eccentricity: float  # mm from bridge centerline
    vehicle_type: str


def calculate_girder_distribution(
    girder_spacing: float,
    num_girders: int,
    lane_placements: List[LanePlacement],
) -> List[float]:
    """Courbon's reaction-distribution factors for each girder.

    For *n* girders at spacing *s*, the method treats the deck as
    perfectly rigid and distributes the total unit reaction by:

        R_i = (P / n) [1 + n · Σe_j · x_i / (P · Σx_k²)]

    Returned factors sum to the number of loaded lanes.
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


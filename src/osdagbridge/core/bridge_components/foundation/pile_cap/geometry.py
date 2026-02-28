"""Rectangular pile cap for typical 2/4/6-pile groups."""
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PileCapGeometry:
    """Rectangular pile cap — defaults to a 4-pile layout at 3D spacing."""
    length: float = 4000.0
    width: float = 4000.0
    depth: float = 1500.0
    pile_diameter: float = 1200.0
    pile_positions: List[Tuple[float, float]] = None

    def __post_init__(self):
        if self.pile_positions is None:
            # Default: 4-pile group at corners with 3D spacing
            s = 3 * self.pile_diameter
            self.pile_positions = [
                (-s / 2, -s / 2),
                (s / 2, -s / 2),
                (-s / 2, s / 2),
                (s / 2, s / 2),
            ]

    @property
    def num_piles(self) -> int:
        return len(self.pile_positions)

    @property
    def plan_area(self) -> float:
        """Plan area (mm²)."""
        return self.length * self.width

    @property
    def volume(self) -> float:
        """Concrete volume (mm³)."""
        return self.plan_area * self.depth

    @property
    def self_weight(self) -> float:
        """Self-weight (kN), density = 25 kN/m³."""
        return self.volume * 1e-9 * 25.0


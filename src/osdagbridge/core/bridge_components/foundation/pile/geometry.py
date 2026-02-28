"""Pile geometry calculations.

Supports circular bored cast-in-situ piles (most common for
highway bridge foundations in India).
"""
import math
from dataclasses import dataclass


@dataclass
class PileGeometry:
    """Single pile geometry.

    Attributes:
        diameter: Pile diameter (mm).
        length: Total pile length (mm).
        embedment_depth: Depth below ground level (mm).
    """
    diameter: float = 1200.0
    length: float = 20_000.0
    embedment_depth: float = 18_000.0

    @property
    def cross_section_area(self) -> float:
        """Cross-sectional area (mm²)."""
        return math.pi * (self.diameter / 2) ** 2

    @property
    def perimeter(self) -> float:
        """Perimeter for shaft friction calculation (mm)."""
        return math.pi * self.diameter

    @property
    def volume(self) -> float:
        """Concrete volume (mm³)."""
        return self.cross_section_area * self.length

    @property
    def surface_area_embedded(self) -> float:
        """Embedded shaft surface area (mm²) for friction capacity."""
        return self.perimeter * self.embedment_depth


"""Bored cast-in-situ pile geometry."""
import math
from dataclasses import dataclass


@dataclass
class PileGeometry:
    """Single circular pile (mm)."""
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


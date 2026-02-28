"""Pier geometry calculations.

Supports rectangular and circular pier cross-sections with height,
breadth / diameter, and cap-level offsets.
"""
from dataclasses import dataclass
import math
from typing import Literal


@dataclass
class PierGeometry:
    """Geometry of a single bridge pier.

    Attributes:
        shape: "rectangular" or "circular".
        height: Clear height of pier (mm).
        breadth: Breadth (mm, for rectangular) or diameter (mm, for circular).
        depth: Depth along traffic direction (mm, rectangular only).
    """
    shape: Literal["rectangular", "circular"] = "rectangular"
    height: float = 5000.0
    breadth: float = 1500.0
    depth: float = 1000.0

    @property
    def cross_section_area(self) -> float:
        """Cross-sectional area (mm²)."""
        if self.shape == "circular":
            return math.pi * (self.breadth / 2) ** 2
        return self.breadth * self.depth

    @property
    def volume(self) -> float:
        """Volume of pier shaft (mm³)."""
        return self.cross_section_area * self.height

    @property
    def self_weight(self) -> float:
        """Self-weight (kN), assuming RCC density 25 kN/m³."""
        return self.volume * 1e-9 * 25.0

    @property
    def moment_of_inertia_transverse(self) -> float:
        """I about transverse axis (mm⁴) for stability checks."""
        if self.shape == "circular":
            r = self.breadth / 2
            return math.pi * r**4 / 4
        return self.depth * self.breadth**3 / 12


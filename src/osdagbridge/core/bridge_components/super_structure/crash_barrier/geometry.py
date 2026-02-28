"""Standard IRC crash barrier (NJ / F-shape) profile."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CrashBarrierGeometry:
    """Simplified trapezoidal barrier cross-section."""

    height: float = 900.0
    base_width: float = 475.0
    top_width: float = 200.0

    @property
    def average_width(self) -> float:
        return (self.base_width + self.top_width) / 2

    @property
    def cross_section_area(self) -> float:
        """Approximate trapezoidal area (mm\u00b2)."""
        return self.average_width * self.height

    @property
    def self_weight_per_m(self) -> float:
        """Self-weight per meter length (kN/m), density 25 kN/m\u00b3."""
        return self.cross_section_area * 1e-6 * 25.0

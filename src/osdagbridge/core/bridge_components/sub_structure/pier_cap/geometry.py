"""Pier cap (bearing shelf) geometry.

Distributes girder reactions into the pier shaft.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PierCapGeometry:
    """Hammerhead-style RCC pier cap (mm)."""

    total_length: float = 10_000.0
    width: float = 1500.0
    depth: float = 1200.0

    @property
    def plan_area(self) -> float:
        """Plan area (mm\u00b2)."""
        return self.total_length * self.width

    @property
    def volume(self) -> float:
        """Approximate volume (mm\u00b3)."""
        return self.plan_area * self.depth

    @property
    def self_weight_kN(self) -> float:
        """Self-weight assuming RC density 25 kN/m\u00b3."""
        return self.volume * 1e-9 * 25.0

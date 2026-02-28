"""Pedestal geometry calculations.

Pedestals sit between bearing plates and the pier cap and transfer
concentrated girder reactions into the pier cap.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PedestalGeometry:
    """Rectangular RCC pedestal.

    Attributes:
        length: Along traffic direction (mm).
        width: Transverse to traffic (mm).
        height: Pedestal height (mm).
    """

    length: float = 600.0
    width: float = 600.0
    height: float = 300.0

    @property
    def plan_area(self) -> float:
        """Plan area (mm\u00b2)."""
        return self.length * self.width

    @property
    def volume(self) -> float:
        """Volume (mm\u00b3)."""
        return self.plan_area * self.height

    @property
    def self_weight_kN(self) -> float:
        """Self-weight assuming RC density 25 kN/m\u00b3."""
        return self.volume * 1e-9 * 25.0

"""Deck slab geometry.

Helper dataclass for RCC bridge deck slab dimensional parameters.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DeckGeometry:
    """RCC deck slab geometry.

    Attributes:
        thickness: Slab thickness (mm).
        overall_width: Full carriageway + footpath width (mm).
        cantilever_overhang: Overhang beyond outer girder (mm).
    """

    thickness: float = 220.0
    overall_width: float = 12_000.0
    cantilever_overhang: float = 1500.0

    @property
    def plan_area_per_m(self) -> float:
        """Plan area per meter span (mm\u00b2/mm)."""
        return self.overall_width * 1.0  # per mm span

"""Deck slab property calculations.

Provides geometry and material properties for RCC bridge deck slabs
shared across bridge types.
"""
from dataclasses import dataclass


@dataclass
class DeckSlab:
    """RCC deck slab parameters.

    Attributes:
        thickness: Slab thickness in mm (typical 200–250 mm).
        width: Tributary width per girder in mm.
        concrete_grade: e.g. "M30", "M35".
        density: Concrete density in kN/m³ (default 25.0).
    """
    thickness: float
    width: float
    concrete_grade: str = "M30"
    density: float = 25.0

    @property
    def self_weight(self) -> float:
        """Self-weight per unit length per girder (kN/m)."""
        return self.density * (self.thickness / 1000) * (self.width / 1000)

    @property
    def modular_ratio(self) -> float:
        """Short-term modular ratio m = Es / Ec.

        Uses approximate Ec from IRC:22-2015 Table 1.
        """
        grade_num = int(self.concrete_grade.replace("M", ""))
        ec = 5000 * (grade_num ** 0.5)  # MPa (IS 456 approximation)
        return 200_000 / ec  # Es / Ec


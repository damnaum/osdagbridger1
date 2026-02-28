"""RCC deck-slab properties used in dead-load and composite calculations."""
from dataclasses import dataclass


@dataclass
class DeckSlab:
    """Deck slab — typical thickness 200–250 mm."""
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


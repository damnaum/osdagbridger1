"""
Plate girder input & section data.

Dimensions in mm, loads in kN unless noted.
Steel grades per IS 2062; design methodology IS 800:2007;
live-load specs from IRC:6-2017.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class SteelGrade(str, Enum):
    """Indian structural steel grades (IS 2062)."""
    E250A = "E250A"   # Fe 410 W A  — fy = 250 MPa
    E250B = "E250B"   # Fe 410 W B  — fy = 250 MPa
    E300 = "E300"     # Fe 440      — fy = 300 MPa
    E350 = "E350"     # Fe 490      — fy = 350 MPa
    E410 = "E410"     # Fe 540      — fy = 410 MPa
    E450 = "E450"     # Fe 570      — fy = 450 MPa


class BridgeSpanType(str, Enum):
    """Span configuration."""
    SIMPLY_SUPPORTED = "simply_supported"
    CONTINUOUS_2_SPAN = "continuous_2_span"
    CONTINUOUS_3_SPAN = "continuous_3_span"


class PlateGirderInput(BaseModel):
    """Everything needed to kick off a plate girder design.

    Dimensions in mm, loads in kN/m unless noted otherwise.
    Leave web/flange sizes as ``None`` to let the auto-sizer pick them.
    """

    # --- project identification ---
    project_name: str = Field(..., min_length=1, max_length=200)
    bridge_name: str = Field(..., min_length=1, max_length=100)
    chainage: Optional[str] = None

    # --- geometry ---
    effective_span: float = Field(..., gt=0, le=150000, description="Effective span in mm")
    span_type: BridgeSpanType = BridgeSpanType.SIMPLY_SUPPORTED

    # --- cross-section ---
    carriageway_width: float = Field(7500, gt=0, description="Clear carriageway width (mm)")
    num_lanes: int = Field(2, ge=1, le=8)
    footpath_width: float = Field(0, ge=0, description="Footpath width each side (mm)")

    # --- girders ---
    num_girders: int = Field(2, ge=2, le=10)
    girder_spacing: float = Field(..., gt=0, description="C/c spacing of girders (mm)")

    # --- materials ---
    steel_grade: SteelGrade = SteelGrade.E250A
    concrete_grade: str = Field("M30", pattern=r"^M[0-9]{2}$")

    # --- initial girder plate sizes (auto-calc if None) ---
    web_depth: Optional[float] = Field(None, gt=0, description="Web plate depth (mm)")
    web_thickness: Optional[float] = Field(None, gt=0, description="Web plate thickness (mm)")
    flange_width: Optional[float] = Field(None, gt=0, description="Flange plate width (mm)")
    flange_thickness: Optional[float] = Field(None, gt=0, description="Flange plate thickness (mm)")

    # --- loading ---
    live_load_class: Literal["CLASS_A", "CLASS_70R", "CLASS_AA"] = "CLASS_A"
    num_lanes_loaded: int = Field(2, ge=1)

    # --- superimposed dead loads ---
    wearing_coat_thickness: float = Field(75, ge=0, description="Wearing coat thickness (mm)")
    crash_barrier_load: float = Field(10.0, ge=0, description="Crash barrier UDL (kN/m)")

    # --- seismic (optional) ---
    include_seismic: bool = False
    seismic_zone: Optional[Literal["II", "III", "IV", "V"]] = None

    @field_validator("effective_span")
    @classmethod
    def validate_span(cls, v):
        """Plate girders rarely go beyond 60 m; past that, look at
        box girder or cable-stayed alternatives."""
        if v > 60000:
            raise ValueError(
                f"Span {v / 1000:.1f}m exceeds typical plate girder limit of 60m. "
                "Consider box girder or cable-stayed design."
            )
        return v

    @field_validator("web_depth")
    @classmethod
    def validate_web_depth(cls, v, info):
        """Catch obviously shallow webs early."""
        if v is not None:
            span = info.data.get("effective_span")
            if span and v < span / 25:
                raise ValueError(
                    f"Web depth {v}mm is too shallow for span {span}mm. "
                    f"Minimum recommended: {span / 15:.0f}mm (span/15)"
                )
        return v

    def get_yield_strength(self) -> float:
        """fy in MPa (IS 2062 Table 2, thickness ≤ 20 mm)."""
        fy_map = {
            SteelGrade.E250A: 250.0,
            SteelGrade.E250B: 250.0,
            SteelGrade.E300: 300.0,
            SteelGrade.E350: 350.0,
            SteelGrade.E410: 410.0,
            SteelGrade.E450: 450.0,
        }
        return fy_map[self.steel_grade]

    def get_ultimate_strength(self) -> float:
        """fu in MPa (IS 2062 Table 2)."""
        fu_map = {
            SteelGrade.E250A: 410.0,
            SteelGrade.E250B: 410.0,
            SteelGrade.E300: 440.0,
            SteelGrade.E350: 490.0,
            SteelGrade.E410: 540.0,
            SteelGrade.E450: 570.0,
        }
        return fu_map[self.steel_grade]

    def get_youngs_modulus(self) -> float:
        """E in MPa — same for all structural steel grades."""
        return 200_000.0

    def get_density_steel(self) -> float:
        """Steel density in kN/m³."""
        return 78.5


@dataclass
class PlateGirderSection:
    """Computed cross-section properties ready for design checks."""

    # plate dimensions (mm)
    web_depth: float             # mm - clear depth between flanges
    web_thickness: float         # mm
    top_flange_width: float      # mm
    top_flange_thickness: float  # mm
    bottom_flange_width: float   # mm
    bottom_flange_thickness: float

    # derived quantities
    total_depth: float
    area: float                       # mm²
    moment_of_inertia_xx: float       # mm⁴ (strong axis)
    moment_of_inertia_yy: float       # mm⁴ (weak axis)
    section_modulus_top: float         # mm³
    section_modulus_bottom: float      # mm³
    centroid_from_bottom: float        # mm
    plastic_section_modulus: float     # mm³

    # IS 800 classification
    section_class: Literal["plastic", "compact", "semi-compact", "slender"]
    web_slenderness: float             # d/tw
    flange_slenderness: float          # outstand ratio

    @property
    def weight_per_meter(self) -> float:
        """Girder weight per running metre (kN/m)."""
        return self.area * 1e-6 * 78.5

    @property
    def shape_factor(self) -> float:
        """Zp / Ze ratio."""
        z_el = min(self.section_modulus_top, self.section_modulus_bottom)
        return self.plastic_section_modulus / z_el if z_el > 0 else 1.0

"""
Plate Girder Bridge Data Transfer Object (DTO)

Contains all input parameters needed for plate girder bridge design.
Uses Pydantic for validation and serialization.
Dimensions in mm, loads in kN unless otherwise noted.

Reference codes:
    - IS 2062 for steel grades
    - IS 800:2007 for design methodology
    - IRC:6-2017 for loading standards
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class SteelGrade(str, Enum):
    """Standard Indian steel grades as per IS 2062."""
    E250A = "E250A"  # Fe 410 W A, fy = 250 MPa
    E250B = "E250B"  # Fe 410 W B, fy = 250 MPa
    E300 = "E300"    # Fe 440, fy = 300 MPa
    E350 = "E350"    # Fe 490, fy = 350 MPa
    E410 = "E410"    # Fe 540, fy = 410 MPa
    E450 = "E450"    # Fe 570, fy = 450 MPa


class BridgeSpanType(str, Enum):
    """Bridge span configuration."""
    SIMPLY_SUPPORTED = "simply_supported"
    CONTINUOUS_2_SPAN = "continuous_2_span"
    CONTINUOUS_3_SPAN = "continuous_3_span"


class PlateGirderInput(BaseModel):
    """
    Input parameters for plate girder bridge design.

    All dimensions in mm unless specified otherwise.
    All loads in kN or kN/m unless specified otherwise.

    Example:
        >>> inp = PlateGirderInput(
        ...     project_name="NH-44 ROB",
        ...     bridge_name="Km 245+500",
        ...     effective_span=30000,
        ...     girder_spacing=3000,
        ... )
    """

    # Project identification
    project_name: str = Field(..., min_length=1, max_length=200)
    bridge_name: str = Field(..., min_length=1, max_length=100)
    chainage: Optional[str] = None  # e.g., "km 45+300"

    # Geometry - Span
    effective_span: float = Field(..., gt=0, le=150000, description="Effective span in mm")
    span_type: BridgeSpanType = BridgeSpanType.SIMPLY_SUPPORTED

    # Geometry - Cross section
    carriageway_width: float = Field(7500, gt=0, description="Clear carriageway width (mm)")
    num_lanes: int = Field(2, ge=1, le=8)
    footpath_width: float = Field(0, ge=0, description="Footpath width each side (mm)")

    # Girder configuration
    num_girders: int = Field(2, ge=2, le=10, description="Number of main girders")
    girder_spacing: float = Field(..., gt=0, description="C/c spacing of girders (mm)")

    # Material properties
    steel_grade: SteelGrade = SteelGrade.E250A
    concrete_grade: str = Field("M30", pattern=r"^M[0-9]{2}$")  # For deck slab

    # Initial girder dimensions (can be auto-calculated if None)
    web_depth: Optional[float] = Field(None, gt=0, description="Web plate depth (mm)")
    web_thickness: Optional[float] = Field(None, gt=0, description="Web plate thickness (mm)")
    flange_width: Optional[float] = Field(None, gt=0, description="Flange plate width (mm)")
    flange_thickness: Optional[float] = Field(None, gt=0, description="Flange plate thickness (mm)")

    # Loading specification
    live_load_class: Literal["CLASS_A", "CLASS_70R", "CLASS_AA"] = "CLASS_A"
    num_lanes_loaded: int = Field(2, ge=1)

    # Additional dead loads
    wearing_coat_thickness: float = Field(75, ge=0, description="Wearing coat thickness (mm)")
    crash_barrier_load: float = Field(10.0, ge=0, description="Crash barrier UDL (kN/m)")

    # Design parameters
    include_seismic: bool = False
    seismic_zone: Optional[Literal["II", "III", "IV", "V"]] = None

    @field_validator("effective_span")
    @classmethod
    def validate_span(cls, v):
        """Check span is within practical limits for plate girders."""
        if v > 60000:  # 60m
            raise ValueError(
                f"Span {v / 1000:.1f}m exceeds typical plate girder limit of 60m. "
                "Consider box girder or cable-stayed design."
            )
        return v

    @field_validator("web_depth")
    @classmethod
    def validate_web_depth(cls, v, info):
        """Validate web depth against span if both are provided."""
        if v is not None:
            span = info.data.get("effective_span")
            if span and v < span / 25:
                raise ValueError(
                    f"Web depth {v}mm is too shallow for span {span}mm. "
                    f"Minimum recommended: {span / 15:.0f}mm (span/15)"
                )
        return v

    def get_yield_strength(self) -> float:
        """
        Get yield strength (fy) for the selected steel grade in MPa.

        As per IS 2062:2011 Table 2 for nominal thickness <= 20mm.
        For thicker plates, slight reduction applies (not implemented yet).
        """
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
        """
        Get ultimate tensile strength (fu) in MPa.

        As per IS 2062:2011 Table 2.
        """
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
        """Young's modulus of steel in MPa (constant for all grades)."""
        return 200000.0

    def get_density_steel(self) -> float:
        """Density of steel in kN/m³."""
        return 78.5


@dataclass
class PlateGirderSection:
    """
    Computed plate girder section properties.

    Stores both dimensions and derived cross-sectional properties
    calculated from those dimensions. This is the output of
    section property calculation, used as input for design checks.
    """

    # Dimensions
    web_depth: float             # mm - clear depth between flanges
    web_thickness: float         # mm
    top_flange_width: float      # mm
    top_flange_thickness: float  # mm
    bottom_flange_width: float   # mm
    bottom_flange_thickness: float  # mm

    # Computed properties
    total_depth: float              # mm
    area: float                     # mm²
    moment_of_inertia_xx: float     # mm⁴ (about strong axis)
    moment_of_inertia_yy: float     # mm⁴ (about weak axis)
    section_modulus_top: float       # mm³ (elastic, at top fiber)
    section_modulus_bottom: float    # mm³ (elastic, at bottom fiber)
    centroid_from_bottom: float     # mm
    plastic_section_modulus: float  # mm³

    # Classification per IS 800:2007 Table 2
    section_class: Literal["plastic", "compact", "semi-compact", "slender"]
    web_slenderness: float      # d/tw ratio
    flange_slenderness: float   # (b - tw)/(2*tf) outstand ratio

    @property
    def weight_per_meter(self) -> float:
        """Weight of girder per unit length in kN/m (density = 78.5 kN/m³)."""
        area_m2 = self.area * 1e-6  # mm² to m²
        return area_m2 * 78.5  # kN/m³ * m² = kN/m

    @property
    def shape_factor(self) -> float:
        """Ratio of plastic to elastic section modulus (Zp/Ze)."""
        z_elastic = min(self.section_modulus_top, self.section_modulus_bottom)
        if z_elastic > 0:
            return self.plastic_section_modulus / z_elastic
        return 1.0

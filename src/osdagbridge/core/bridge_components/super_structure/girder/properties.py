"""Section-property helpers for standard I-shaped steel girders."""
from dataclasses import dataclass


@dataclass
class IGirderGeometry:
    """Dimensions of an I-shaped girder (all in mm)."""
    web_depth: float
    web_thickness: float
    top_flange_width: float
    top_flange_thickness: float
    bottom_flange_width: float
    bottom_flange_thickness: float

    @property
    def total_depth(self) -> float:
        return self.web_depth + self.top_flange_thickness + self.bottom_flange_thickness


def area(geom: IGirderGeometry) -> float:
    """Cross-sectional area of the I-section (mm²)."""
    a_web = geom.web_depth * geom.web_thickness
    a_tf = geom.top_flange_width * geom.top_flange_thickness
    a_bf = geom.bottom_flange_width * geom.bottom_flange_thickness
    return a_web + a_tf + a_bf


def moment_of_inertia_xx(geom: IGirderGeometry) -> float:
    """Strong-axis I_xx via parallel-axis theorem (mm⁴)."""
    a_web = geom.web_depth * geom.web_thickness
    a_tf = geom.top_flange_width * geom.top_flange_thickness
    a_bf = geom.bottom_flange_width * geom.bottom_flange_thickness
    total_a = a_web + a_tf + a_bf

    y_bf = geom.bottom_flange_thickness / 2
    y_web = geom.bottom_flange_thickness + geom.web_depth / 2
    y_tf = geom.bottom_flange_thickness + geom.web_depth + geom.top_flange_thickness / 2

    y_bar = (a_bf * y_bf + a_web * y_web + a_tf * y_tf) / total_a

    i_web = geom.web_thickness * geom.web_depth**3 / 12 + a_web * (y_web - y_bar)**2
    i_tf = geom.top_flange_width * geom.top_flange_thickness**3 / 12 + a_tf * (y_tf - y_bar)**2
    i_bf = geom.bottom_flange_width * geom.bottom_flange_thickness**3 / 12 + a_bf * (y_bf - y_bar)**2

    return i_web + i_tf + i_bf


def weight_per_meter(geom: IGirderGeometry, density: float = 78.5) -> float:
    """Self-weight per metre run (kN/m), default density 78.5 kN/m³."""
    return area(geom) * 1e-6 * density


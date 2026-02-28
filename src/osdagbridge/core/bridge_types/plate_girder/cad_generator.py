"""CAD geometry generator for plate girder bridges.

Generates 2D cross-section coordinates for visualization.
Full 3D CAD (PythonOCC) requires the 'cad' optional dependency.
"""
from typing import List, Tuple

from .dto import PlateGirderSection


def generate_cross_section_coords(
    section: PlateGirderSection,
) -> List[Tuple[float, float]]:
    """Generate 2D coordinates for plate girder cross-section outline.

    Args:
        section: PlateGirderSection with dimensions

    Returns:
        List of (x, y) coordinates forming closed polygon (mm)
    """
    hw = section.web_depth
    tw = section.web_thickness
    bf_top = section.top_flange_width
    tf_top = section.top_flange_thickness
    bf_bot = section.bottom_flange_width
    tf_bot = section.bottom_flange_thickness

    coords = [
        (-bf_bot / 2, 0),
        (bf_bot / 2, 0),
        (bf_bot / 2, tf_bot),
        (tw / 2, tf_bot),
        (tw / 2, tf_bot + hw),
        (bf_top / 2, tf_bot + hw),
        (bf_top / 2, tf_bot + hw + tf_top),
        (-bf_top / 2, tf_bot + hw + tf_top),
        (-bf_top / 2, tf_bot + hw),
        (-tw / 2, tf_bot + hw),
        (-tw / 2, tf_bot),
        (-bf_bot / 2, tf_bot),
        (-bf_bot / 2, 0),  # Close polygon
    ]
    return coords


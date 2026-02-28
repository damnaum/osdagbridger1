"""2-D cross-section outline for plate-girder visualisation.

Full 3-D output via PythonOCC needs the ``cad`` extra.
"""
from typing import List, Tuple

from .dto import PlateGirderSection


def generate_cross_section_coords(
    section: PlateGirderSection,
) -> List[Tuple[float, float]]:
    """Closed polygon (x, y) for the I-section outline (mm)."""
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


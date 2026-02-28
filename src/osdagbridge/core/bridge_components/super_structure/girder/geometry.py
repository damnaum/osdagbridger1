"""Quick factory for doubly-symmetric I-girders."""

from __future__ import annotations

from .properties import IGirderGeometry


def make_symmetric_girder(
    web_depth: float,
    web_thickness: float,
    flange_width: float,
    flange_thickness: float,
) -> IGirderGeometry:
    """Build an IGirderGeometry with equal top/bottom flanges."""
    return IGirderGeometry(
        web_depth=web_depth,
        web_thickness=web_thickness,
        top_flange_width=flange_width,
        top_flange_thickness=flange_thickness,
        bottom_flange_width=flange_width,
        bottom_flange_thickness=flange_thickness,
    )

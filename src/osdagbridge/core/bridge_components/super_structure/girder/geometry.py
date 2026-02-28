"""Parametric I-girder geometry builder.

Provides a convenience factory for creating ``IGirderGeometry``
objects from minimal parameters.
"""

from __future__ import annotations

from .properties import IGirderGeometry


def make_symmetric_girder(
    web_depth: float,
    web_thickness: float,
    flange_width: float,
    flange_thickness: float,
) -> IGirderGeometry:
    """Create a doubly-symmetric I-girder.

    Args:
        web_depth: Clear web depth (mm).
        web_thickness: Web plate thickness (mm).
        flange_width: Flange width (mm) — same top & bottom.
        flange_thickness: Flange thickness (mm) — same top & bottom.

    Returns:
        IGirderGeometry instance.
    """
    return IGirderGeometry(
        web_depth=web_depth,
        web_thickness=web_thickness,
        top_flange_width=flange_width,
        top_flange_thickness=flange_thickness,
        bottom_flange_width=flange_width,
        bottom_flange_thickness=flange_thickness,
    )

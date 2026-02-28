"""Box-girder input model (placeholder).

Mirrors the pattern of ``plate_girder.dto.PlateGirderInput``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BoxGirderInput(BaseModel):
    """Box-girder input — all mm / kN unless noted."""

    project_name: str = Field(..., min_length=1, max_length=200)
    bridge_name: str = Field(..., min_length=1, max_length=100)
    effective_span: float = Field(..., gt=0, le=200_000, description="mm")
    box_width: float = Field(..., gt=0, description="Overall box width (mm)")
    box_depth: float = Field(..., gt=0, description="Overall box depth (mm)")
    num_cells: int = Field(1, ge=1, le=4, description="Number of cells")
    web_thickness: Optional[float] = Field(None, gt=0)
    top_flange_thickness: Optional[float] = Field(None, gt=0)
    bottom_flange_thickness: Optional[float] = Field(None, gt=0)

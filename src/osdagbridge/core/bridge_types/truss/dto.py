"""Truss Bridge Data Transfer Object (stub)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TrussType(str):
    PRATT = "pratt"
    WARREN = "warren"
    HOWE = "howe"
    K_TRUSS = "k_truss"


class TrussBridgeInput(BaseModel):
    """Input parameters for truss bridge design (stub).

    All dimensions in mm, loads in kN unless specified.
    """

    project_name: str = Field(..., min_length=1, max_length=200)
    bridge_name: str = Field(..., min_length=1, max_length=100)
    effective_span: float = Field(..., gt=0, le=300_000, description="mm")
    truss_type: Literal["pratt", "warren", "howe", "k_truss"] = "pratt"
    truss_depth: Optional[float] = Field(None, gt=0, description="mm")
    num_panels: int = Field(8, ge=4, le=30)
    top_chord_section: Optional[str] = None
    bottom_chord_section: Optional[str] = None

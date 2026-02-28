"""Plate Girder Bridge Design Module.

Provides complete design workflow for steel plate girder bridges
as per IS 800:2007 and IRC:24-2010.
"""
from .designer import (
    calculate_epsilon,
    calculate_moment_capacity,
    calculate_section_properties,
    calculate_shear_capacity,
    classify_section,
    design_plate_girder,
    initial_sizing,
)
from .dto import BridgeSpanType, PlateGirderInput, PlateGirderSection, SteelGrade

__all__ = [
    "BridgeSpanType",
    "PlateGirderInput",
    "PlateGirderSection",
    "SteelGrade",
    "calculate_epsilon",
    "calculate_moment_capacity",
    "calculate_section_properties",
    "calculate_shear_capacity",
    "classify_section",
    "design_plate_girder",
    "initial_sizing",
]


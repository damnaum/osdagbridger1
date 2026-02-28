"""Plate girder structural analysis orchestrator.

Coordinates between load computation and solver to produce
internal force diagrams (SFD, BMD) for design checks.
"""
from typing import Any, Dict

from ...loads.moving_load import analyze_moving_load
from ...loads.vehicle import get_vehicle_by_name
from ...utils.codes.irc6_2017 import VehicleType, get_impact_factor
from .dto import PlateGirderInput


def analyze_plate_girder(input_data: PlateGirderInput) -> Dict[str, Any]:
    """Run full analysis for a plate girder bridge.

    Steps:
    1. Get vehicle load from input specification
    2. Calculate impact factor based on span and bridge type
    3. Run moving load analysis for max BM and SF
    4. Return envelope of results

    Args:
        input_data: PlateGirderInput with geometry and loading

    Returns:
        Dictionary with analysis results including max_moment, max_shear, etc.
    """
    span_m = input_data.effective_span / 1000  # mm to m

    vehicle = get_vehicle_by_name(input_data.live_load_class)

    vehicle_type_map = {
        "CLASS_A": VehicleType.CLASS_A,
        "CLASS_70R": VehicleType.CLASS_70R_WHEELED,
        "CLASS_AA": VehicleType.CLASS_AA_TRACKED,
    }
    vt = vehicle_type_map.get(
        input_data.live_load_class, VehicleType.CLASS_A
    )

    impact = get_impact_factor("steel", span_m, vt)

    results = analyze_moving_load(span_m, vehicle, impact_factor=impact)
    results["span_m"] = span_m
    results["impact_factor"] = impact
    results["vehicle_type"] = input_data.live_load_class

    return results


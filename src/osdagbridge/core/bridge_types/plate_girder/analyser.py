"""Analysis orchestrator for plate-girder bridges.

Pulls together vehicle loads, impact factors, and the moving-load
solver to produce the BM/SF envelopes the designer needs.
"""
from typing import Any, Dict

from ...loads.moving_load import analyze_moving_load
from ...loads.vehicle import get_vehicle_by_name
from ...utils.codes.irc6_2017 import VehicleType, get_impact_factor
from .dto import PlateGirderInput


def analyze_plate_girder(input_data: PlateGirderInput) -> Dict[str, Any]:
    """Full moving-load analysis for a simply-supported plate girder.

    Returns a dict with ``max_moment``, ``max_shear``, ``impact_factor``,
    etc. — everything the designer picks up downstream.
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


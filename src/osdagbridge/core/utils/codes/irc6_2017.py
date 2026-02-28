"""
IRC:6-2017 Vehicle Loading Module
Standard Specifications for Road Bridges - Section II (Loads)

This module provides vehicle load definitions for bridge design including:
- Class A Loading (Standard two-lane loading)
- Class B Loading (Single lane loading)
- Class AA Loading (Heavy loading - Tracked/Wheeled)
- Class 70R Loading (Special heavy vehicle)

Reference: IRC:6-2017, Annexure A
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

import numpy as np


class VehicleType(Enum):
    """IRC vehicle classification types."""
    CLASS_A = "class_a"
    CLASS_B = "class_b"
    CLASS_AA_TRACKED = "class_aa_tracked"
    CLASS_AA_WHEELED = "class_aa_wheeled"
    CLASS_70R_TRACKED = "class_70r_tracked"
    CLASS_70R_WHEELED = "class_70r_wheeled"
    CLASS_70R_BOGIE = "class_70r_bogie"


@dataclass
class AxleLoad:
    """Single axle load definition."""
    load: float  # kN
    position: float  # m from front of vehicle
    contact_width: float = 0.25  # m (tire contact width)
    contact_length: float = 0.50  # m (along traffic direction)


@dataclass
class VehicleLoad:
    """Complete vehicle load configuration."""
    vehicle_type: VehicleType
    axles: List[AxleLoad]
    total_length: float  # m
    min_spacing_same_lane: float  # m (between successive vehicles)
    ground_contact_area: Tuple[float, float] = (0.25, 0.50)  # width x length in m

    @property
    def total_load(self) -> float:
        """Total vehicle weight in kN."""
        return sum(axle.load for axle in self.axles)

    @property
    def axle_positions(self) -> np.ndarray:
        """Array of axle positions from vehicle front."""
        return np.array([axle.position for axle in self.axles])

    @property
    def axle_loads(self) -> np.ndarray:
        """Array of axle loads in kN."""
        return np.array([axle.load for axle in self.axles])


def get_class_a_train() -> VehicleLoad:
    """
    IRC Class A loading train configuration.

    Standard two-lane bridge loading for highways and permanent bridges.
    Total train length: approximately 20.3m

    Axle arrangement (from front):
    - 2 front axles: 27 kN each, spaced 1.1m apart
    - Gap of 3.2m
    - 2 middle axles: 114 kN each, spaced 1.2m apart
    - Gap of 4.3m
    - 4 rear axles: 68 kN each, spaced 3.0m apart

    Returns:
        VehicleLoad object for Class A train

    Reference: IRC:6-2017, Annexure A, Fig. 1
    """
    axles = [
        # Front axle group (27 kN each)
        AxleLoad(load=27.0, position=0.0),
        AxleLoad(load=27.0, position=1.1),
        # Middle axle group (114 kN each)
        AxleLoad(load=114.0, position=1.1 + 3.2),
        AxleLoad(load=114.0, position=1.1 + 3.2 + 1.2),
        # Rear axle group (68 kN each)
        AxleLoad(load=68.0, position=1.1 + 3.2 + 1.2 + 4.3),
        AxleLoad(load=68.0, position=1.1 + 3.2 + 1.2 + 4.3 + 3.0),
        AxleLoad(load=68.0, position=1.1 + 3.2 + 1.2 + 4.3 + 6.0),
        AxleLoad(load=68.0, position=1.1 + 3.2 + 1.2 + 4.3 + 9.0),
    ]

    return VehicleLoad(
        vehicle_type=VehicleType.CLASS_A,
        axles=axles,
        total_length=20.3,
        min_spacing_same_lane=18.5,  # IRC specifies 18.5m gap minimum
    )


def get_class_b_train() -> VehicleLoad:
    """
    IRC Class B loading train configuration.

    Lighter loading for minor roads and temporary bridges.
    Same axle arrangement as Class A but with lighter axle weights.

    Axle arrangement (from front):
    - 2 front axles: 16 kN each, spaced 1.1m apart
    - Gap of 3.2m
    - 2 middle axles: 68 kN each, spaced 1.2m apart
    - Gap of 4.3m
    - 4 rear axles: 41 kN each, spaced 3.0m apart

    Returns:
        VehicleLoad object for Class B train

    Reference: IRC:6-2017, Annexure A, Fig. 2
    """
    axles = [
        # Front axle group (16 kN each)
        AxleLoad(load=16.0, position=0.0),
        AxleLoad(load=16.0, position=1.1),
        # Middle axle group (68 kN each)
        AxleLoad(load=68.0, position=1.1 + 3.2),
        AxleLoad(load=68.0, position=1.1 + 3.2 + 1.2),
        # Rear axle group (41 kN each)
        AxleLoad(load=41.0, position=1.1 + 3.2 + 1.2 + 4.3),
        AxleLoad(load=41.0, position=1.1 + 3.2 + 1.2 + 4.3 + 3.0),
        AxleLoad(load=41.0, position=1.1 + 3.2 + 1.2 + 4.3 + 6.0),
        AxleLoad(load=41.0, position=1.1 + 3.2 + 1.2 + 4.3 + 9.0),
    ]

    return VehicleLoad(
        vehicle_type=VehicleType.CLASS_B,
        axles=axles,
        total_length=20.3,
        min_spacing_same_lane=18.5,
    )


def get_class_aa_tracked() -> VehicleLoad:
    """
    IRC Class AA Tracked vehicle (tank-type loading).

    Two track pads, each 3.6m long x 0.85m wide.
    Total load: 700 kN distributed over two tracks.
    Used for bridges on National Highways and State Highways.

    Reference: IRC:6-2017, Annexure A, Fig. 3
    """
    # Tracked vehicles modeled as distributed load over track length
    # Represented as equivalent concentrated loads for analysis
    track_load = 350.0  # kN per track (total 700 kN)
    track_length = 3.6  # m

    # Model as 5 equivalent point loads per track
    num_points = 5
    point_spacing = track_length / (num_points - 1)
    point_load = track_load / num_points  # 70 kN each

    axles = []
    for i in range(num_points):
        axles.append(AxleLoad(load=point_load, position=i * point_spacing))

    return VehicleLoad(
        vehicle_type=VehicleType.CLASS_AA_TRACKED,
        axles=axles,
        total_length=7.2,
        min_spacing_same_lane=30.0,
        ground_contact_area=(3.6, 0.85),  # Track dimensions
    )


def get_class_aa_wheeled() -> VehicleLoad:
    """
    IRC Class AA Wheeled vehicle loading.

    Heavy wheeled vehicle with total load 400 kN.
    4 axles with varying loads.

    Reference: IRC:6-2017, Annexure A, Fig. 3A
    """
    axles = [
        AxleLoad(load=62.5, position=0.0),
        AxleLoad(load=62.5, position=1.2),
        AxleLoad(load=125.0, position=1.2 + 2.79),
        AxleLoad(load=125.0, position=1.2 + 2.79 + 1.2),
    ]

    return VehicleLoad(
        vehicle_type=VehicleType.CLASS_AA_WHEELED,
        axles=axles,
        total_length=8.19,
        min_spacing_same_lane=30.0,
        ground_contact_area=(0.30, 0.15),
    )


def get_class_70r_wheeled() -> VehicleLoad:
    """
    IRC Class 70R Wheeled vehicle configuration.

    Heavy vehicle loading for National Highways and important bridges.
    7-axle configuration with total load ~1000 kN.

    Axle arrangement (from front):
    - 2 steering axles: 80 kN each, spaced 1.37m
    - Gap of 4.57m to bogie
    - 5 bogie axles: 170 kN each (approx), spaced 1.37m each

    Returns:
        VehicleLoad object for 70R wheeled vehicle

    Reference: IRC:6-2017, Annexure A, Fig. 5
    """
    # Steering axles (front)
    front_axle_load = 80.0  # kN each

    # Bogie axle loads (rear) - distributed ~170 kN per axle
    bogie_axle_load = 170.0  # kN each

    axles = [
        # Steering axles
        AxleLoad(load=front_axle_load, position=0.0),
        AxleLoad(load=front_axle_load, position=1.37),
        # Bogie axles (5 nos)
        AxleLoad(load=bogie_axle_load, position=1.37 + 4.57),
        AxleLoad(load=bogie_axle_load, position=1.37 + 4.57 + 1.37),
        AxleLoad(load=bogie_axle_load, position=1.37 + 4.57 + 2.74),
        AxleLoad(load=bogie_axle_load, position=1.37 + 4.57 + 4.11),
        AxleLoad(load=bogie_axle_load, position=1.37 + 4.57 + 5.48),
    ]

    return VehicleLoad(
        vehicle_type=VehicleType.CLASS_70R_WHEELED,
        axles=axles,
        total_length=15.22,
        min_spacing_same_lane=30.0,  # 30m min between 70R vehicles
        ground_contact_area=(0.86, 0.263),  # Different contact for heavy vehicle
    )


def get_class_70r_tracked() -> VehicleLoad:
    """
    IRC Class 70R Tracked vehicle (tank-type loading).

    Two track pads, each 4.57m long x 0.85m wide.
    Total load: 700 kN distributed over two tracks.

    Reference: IRC:6-2017, Annexure A, Fig. 4
    """
    # Tracked vehicles modeled as distributed load over track length
    track_load = 350.0  # kN per track
    track_length = 4.57  # m

    # Model as 5 equivalent point loads per track
    num_points = 5
    point_spacing = track_length / (num_points - 1)
    point_load = track_load / num_points

    axles = []
    for i in range(num_points):
        axles.append(AxleLoad(load=point_load, position=i * point_spacing))

    return VehicleLoad(
        vehicle_type=VehicleType.CLASS_70R_TRACKED,
        axles=axles,
        total_length=7.92,
        min_spacing_same_lane=30.0,
        ground_contact_area=(4.57, 0.85),  # Track dimensions
    )


def get_class_70r_bogie() -> VehicleLoad:
    """
    IRC Class 70R Bogie loading.

    Two axles, each 200 kN, spaced 1.22m apart.
    Total load: 400 kN on bogie.

    Reference: IRC:6-2017, Annexure A, Fig. 6
    """
    axles = [
        AxleLoad(load=200.0, position=0.0, contact_width=0.38, contact_length=0.15),
        AxleLoad(load=200.0, position=1.22, contact_width=0.38, contact_length=0.15),
    ]

    return VehicleLoad(
        vehicle_type=VehicleType.CLASS_70R_BOGIE,
        axles=axles,
        total_length=4.87,
        min_spacing_same_lane=30.0,
        ground_contact_area=(0.38, 0.15),
    )


def get_impact_factor(bridge_type: str, span: float, vehicle_type: VehicleType) -> float:
    """
    Calculate impact factor (dynamic amplification) as per IRC:6-2017.

    The impact factor accounts for dynamic effects of moving vehicles.
    Applied as a multiplier on live load, e.g., 1.25 means 25% increase.

    Args:
        bridge_type: "steel", "concrete", or "composite"
        span: Effective span in meters
        vehicle_type: Type of vehicle loading

    Returns:
        Impact factor (multiplier, e.g., 1.25 means 25% increase)

    Reference: IRC:6-2017, Clause 211.2

    Example:
        >>> get_impact_factor("steel", 10.0, VehicleType.CLASS_A)
        1.383  # approximately
    """
    # For Class A and Class B loading
    if vehicle_type in (VehicleType.CLASS_A, VehicleType.CLASS_B):
        if bridge_type == "steel":
            # I = 9 / (13.5 + L) for steel bridges
            impact = 9.0 / (13.5 + span)
        elif bridge_type == "concrete":
            # I = 4.5 / (6 + L) for RCC bridges
            impact = 4.5 / (6.0 + span)
        else:  # composite
            # Use average of steel and concrete formulas
            impact = (9.0 / (13.5 + span) + 4.5 / (6.0 + span)) / 2

    # For Class AA and 70R loading
    elif vehicle_type in (
        VehicleType.CLASS_70R_WHEELED,
        VehicleType.CLASS_70R_TRACKED,
        VehicleType.CLASS_70R_BOGIE,
        VehicleType.CLASS_AA_WHEELED,
        VehicleType.CLASS_AA_TRACKED,
    ):
        if span <= 9.0:
            # For spans up to 9m
            if vehicle_type in (VehicleType.CLASS_70R_TRACKED, VehicleType.CLASS_AA_TRACKED):
                impact = 0.25  # 25% for tracked vehicles
            else:
                impact = 0.25  # 25% for wheeled vehicles <= 9m
        else:
            # For spans > 9m, linearly reduce to 10% at 45m
            if vehicle_type in (VehicleType.CLASS_70R_TRACKED, VehicleType.CLASS_AA_TRACKED):
                # Tracked: 25% at 9m, reducing to 10% at 45m+
                impact = max(0.10, 0.25 - (span - 9.0) * (0.15 / 36.0))
            else:
                # Wheeled: 25% at 9m, reducing to 10% at 45m+
                impact = max(0.10, 0.25 - (span - 9.0) * (0.15 / 36.0))

    else:
        impact = 0.20  # Default 20% for unspecified types

    # Impact factor should not be less than 10%
    return 1.0 + max(impact, 0.10)


def get_lane_distribution_factor(num_lanes: int) -> float:
    """
    Get lane reduction factor for multi-lane loading.

    When multiple lanes are loaded simultaneously, a reduction
    factor applies since full loading on all lanes is unlikely.

    Args:
        num_lanes: Number of lanes loaded

    Returns:
        Reduction factor (multiplier)

    Reference: IRC:6-2017, Clause 208.3
    """
    lane_factors = {
        1: 1.0,
        2: 1.0,   # No reduction for 2 lanes
        3: 0.9,   # 10% reduction for 3 lanes
        4: 0.75,  # 25% reduction for 4 lanes
    }
    # For more than 4 lanes, use 0.75
    return lane_factors.get(num_lanes, 0.75)


def get_congestion_factor(span: float) -> float:
    """
    Get congestion factor for long-span bridges.

    For spans greater than certain limits, increase in live load
    due to traffic congestion should be considered.

    Args:
        span: Effective span in meters

    Returns:
        Congestion factor (>=1.0)

    Reference: IRC:6-2017, Clause 209
    """
    if span <= 10.0:
        return 1.0
    elif span <= 40.0:
        # Linear interpolation from 1.0 at 10m to 1.15 at 40m
        return 1.0 + 0.15 * (span - 10.0) / 30.0
    else:
        return 1.15


# Convenience function to get all standard vehicles
def get_all_vehicle_types() -> Dict[str, VehicleLoad]:
    """Return dictionary of all IRC vehicle configurations."""
    return {
        "class_a": get_class_a_train(),
        "class_b": get_class_b_train(),
        "class_aa_tracked": get_class_aa_tracked(),
        "class_aa_wheeled": get_class_aa_wheeled(),
        "class_70r_wheeled": get_class_70r_wheeled(),
        "class_70r_tracked": get_class_70r_tracked(),
        "class_70r_bogie": get_class_70r_bogie(),
    }


# Keep backward-compatible alias
def get_vehicle_loads() -> list:
    """Legacy function returning list of all vehicle configurations."""
    return list(get_all_vehicle_types().values())

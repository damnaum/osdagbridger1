"""
IRC:6-2017 vehicle loads (Section II — Loads & Stresses).

Defines the standard truck/train configurations that Indian highway
bridges are designed for: Class A, Class B, Class AA (tracked/wheeled)
and the heavy Class 70R series.

Axle spacings and weights are straight out of the IRC blue book,
Annexure A.  Impact factors from Clause 211.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

import numpy as np


class VehicleType(Enum):
    """IRC vehicle classes."""
    CLASS_A = "class_a"
    CLASS_B = "class_b"
    CLASS_AA_TRACKED = "class_aa_tracked"
    CLASS_AA_WHEELED = "class_aa_wheeled"
    CLASS_70R_TRACKED = "class_70r_tracked"
    CLASS_70R_WHEELED = "class_70r_wheeled"
    CLASS_70R_BOGIE = "class_70r_bogie"


@dataclass
class AxleLoad:
    """One axle: load (kN), position from vehicle front (m)."""
    load: float
    position: float
    contact_width: float = 0.25    # tyre contact patch (m)
    contact_length: float = 0.50


@dataclass
class VehicleLoad:
    """Full vehicle configuration with all axles."""
    vehicle_type: VehicleType
    axles: List[AxleLoad]
    total_length: float                               # m
    min_spacing_same_lane: float                      # m
    ground_contact_area: Tuple[float, float] = (0.25, 0.50)  # w × l  (m)

    @property
    def total_load(self) -> float:
        """Sum of all axle loads (kN)."""
        return sum(a.load for a in self.axles)

    @property
    def axle_positions(self) -> np.ndarray:
        return np.array([a.position for a in self.axles])

    @property
    def axle_loads(self) -> np.ndarray:
        return np.array([a.load for a in self.axles])


def get_class_a_train() -> VehicleLoad:
    """IRC Class A loading train.

    Standard two-lane highway loading — 8 axles spread over ~20 m:
      2 × 27 kN (front), 2 × 114 kN (tandem), 4 × 68 kN (rear bogie).
    Ref: IRC:6-2017, Annexure A, Fig. 1.
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
    """IRC Class B train — lighter loading for minor roads.

    Same axle layout as Class A but scaled-down weights.
    Ref: IRC:6-2017, Annexure A, Fig. 2.
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
    """Class AA tracked (tank-type), 700 kN over two 3.6 m pads.

    Modelled as 5 equivalent point loads per pad for analysis.
    Ref: IRC:6-2017, Annexure A, Fig. 3.
    """
    # tracked vehicle — distributed over track length;
    # split into 5 point loads for the IL sweep
    track_load = 350.0   # kN per track (700 kN total)
    track_length = 3.6   # m

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
    """Class AA wheeled, 400 kN on 4 axles.

    Ref: IRC:6-2017, Annexure A, Fig. 3A.
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
    """Class 70R wheeled — the big one for NH bridges.

    7 axles, ~1010 kN total: 2 steering (80 kN ea.) + 5 bogie (170 kN ea.).
    Ref: IRC:6-2017, Annexure A, Fig. 5.
    """
    # steering + bogie
    front_axle_load = 80.0     # kN
    bogie_axle_load = 170.0    # kN

    axles = [
        # steering
        AxleLoad(load=front_axle_load, position=0.0),
        AxleLoad(load=front_axle_load, position=1.37),
        # bogie (5 nos)
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
        min_spacing_same_lane=30.0,
        ground_contact_area=(0.86, 0.263),
    )


def get_class_70r_tracked() -> VehicleLoad:
    """Class 70R tracked, 700 kN on 4.57 m pads.

    Ref: IRC:6-2017, Annexure A, Fig. 4.
    """
    track_load = 350.0    # kN per track
    track_length = 4.57   # m

    # 5 equivalent point loads per track
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
    """Class 70R bogie — two 200 kN axles, 1.22 m apart.

    Ref: IRC:6-2017, Annexure A, Fig. 6.
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
    """Impact (dynamic amplification) per IRC:6-2017, Cl. 211.2.

    Returns the multiplier (e.g. 1.25 → 25 % increase).
    Steel bridges get a bigger hit than concrete because they're
    lighter and more flexible.
    """
    # Class A / B — formula-based
    if vehicle_type in (VehicleType.CLASS_A, VehicleType.CLASS_B):
        if bridge_type == "steel":
            impact = 9.0 / (13.5 + span)             # I = 9 / (13.5 + L)
        elif bridge_type == "concrete":
            impact = 4.5 / (6.0 + span)              # I = 4.5 / (6 + L)
        else:
            # composite — use average of steel & concrete
            impact = (9.0 / (13.5 + span) + 4.5 / (6.0 + span)) / 2

    # Class AA / 70R
    elif vehicle_type in (
        VehicleType.CLASS_70R_WHEELED,
        VehicleType.CLASS_70R_TRACKED,
        VehicleType.CLASS_70R_BOGIE,
        VehicleType.CLASS_AA_WHEELED,
        VehicleType.CLASS_AA_TRACKED,
    ):
        if span <= 9.0:
            if vehicle_type in (VehicleType.CLASS_70R_TRACKED, VehicleType.CLASS_AA_TRACKED):
                impact = 0.25
            else:
                impact = 0.25
        else:
            # linear reduction: 25% at 9 m → 10% at 45 m
            if vehicle_type in (VehicleType.CLASS_70R_TRACKED, VehicleType.CLASS_AA_TRACKED):
                # Tracked: 25% at 9m, reducing to 10% at 45m+
                impact = max(0.10, 0.25 - (span - 9.0) * (0.15 / 36.0))
            else:
                # Wheeled: 25% at 9m, reducing to 10% at 45m+
                impact = max(0.10, 0.25 - (span - 9.0) * (0.15 / 36.0))

    else:
        impact = 0.20  # fallback

    # never below 10 %
    return 1.0 + max(impact, 0.10)


def get_lane_distribution_factor(num_lanes: int) -> float:
    """Multi-lane reduction (IRC:6-2017 Cl. 208.3).

    Full loading on all lanes simultaneously is unlikely; the
    code allows a reduction for 3+ lanes.
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
    """Congestion surcharge for long-span bridges (IRC:6 Cl. 209).

    1.0 up to 10 m, linearly increasing to 1.15 at 40 m.
    """
    if span <= 10.0:
        return 1.0
    elif span <= 40.0:
        # Linear interpolation from 1.0 at 10m to 1.15 at 40m
        return 1.0 + 0.15 * (span - 10.0) / 30.0
    else:
        return 1.15


def get_all_vehicle_types() -> Dict[str, VehicleLoad]:
    """All IRC vehicle configs as a dict."""
    return {
        "class_a": get_class_a_train(),
        "class_b": get_class_b_train(),
        "class_aa_tracked": get_class_aa_tracked(),
        "class_aa_wheeled": get_class_aa_wheeled(),
        "class_70r_wheeled": get_class_70r_wheeled(),
        "class_70r_tracked": get_class_70r_tracked(),
        "class_70r_bogie": get_class_70r_bogie(),
    }


def get_vehicle_loads() -> list:
    """Compat shim — returns list of all vehicle configs."""
    return list(get_all_vehicle_types().values())

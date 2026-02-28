"""Vehicle load wrapper providing convenience functions."""
from ..utils.codes.irc6_2017 import (
    VehicleLoad,
    get_class_a_train,
    get_class_b_train,
    get_class_70r_wheeled,
    get_class_70r_tracked,
    get_class_70r_bogie,
    get_class_aa_tracked,
    get_class_aa_wheeled,
)


def get_vehicle_by_name(name: str) -> VehicleLoad:
    """Get a vehicle load configuration by its string name.

    Args:
        name: One of 'CLASS_A', 'CLASS_B', 'CLASS_70R', 'CLASS_AA', etc.

    Returns:
        VehicleLoad object

    Raises:
        ValueError: If vehicle name is not recognized
    """
    mapping = {
        "CLASS_A": get_class_a_train,
        "CLASS_B": get_class_b_train,
        "CLASS_70R": get_class_70r_wheeled,
        "CLASS_70R_WHEELED": get_class_70r_wheeled,
        "CLASS_70R_TRACKED": get_class_70r_tracked,
        "CLASS_70R_BOGIE": get_class_70r_bogie,
        "CLASS_AA": get_class_aa_tracked,
        "CLASS_AA_TRACKED": get_class_aa_tracked,
        "CLASS_AA_WHEELED": get_class_aa_wheeled,
    }
    factory = mapping.get(name.upper())
    if factory is None:
        raise ValueError(
            f"Unknown vehicle type '{name}'. Valid: {list(mapping.keys())}"
        )
    return factory()


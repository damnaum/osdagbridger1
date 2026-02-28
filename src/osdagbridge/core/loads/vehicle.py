"""Convenience wrapper to look up an IRC vehicle by its string name."""
from ..utils.codes.irc6_2017 import (
    VehicleLoad,
    get_class_70r_bogie,
    get_class_70r_tracked,
    get_class_70r_wheeled,
    get_class_a_train,
    get_class_aa_tracked,
    get_class_aa_wheeled,
    get_class_b_train,
)


def get_vehicle_by_name(name: str) -> VehicleLoad:
    """Return a ``VehicleLoad`` for the given IRC vehicle designation.

    Raises ``ValueError`` for unrecognised names.
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


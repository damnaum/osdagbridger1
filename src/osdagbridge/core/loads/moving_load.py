"""
Moving load analysis for simply-supported bridge girders.

Uses influence-line ordinates to sweep IRC vehicle trains across the
span and find the critical placement (max BM, max SF). The approach
is deliberately keep-it-simple: discrete step sweep, no closed-form
optimisation.  Good enough for preliminary design — detailed grillage
analysis is handled by the OpenSees/ospgrillage adapters.

Ref: Hibbeler, Structural Analysis, Ch. 6 ; IRC:6-2017 vehicle configs.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

from ..utils.codes.irc6_2017 import VehicleLoad


@dataclass
class InfluenceLine:
    """Discrete influence-line ordinates along the span."""
    positions: np.ndarray   # stations (m)
    ordinates: np.ndarray   # IL values
    span: float             # m
    quantity: str           # "moment" or "shear"
    location: float         # section from left support (m)


def generate_moment_influence_line(
    span: float,
    location: float,
    num_points: int = 201,
) -> InfluenceLine:
    """Moment IL for a simply supported beam at a given section.

    For unit load at *x*, the BM at section *a* on span *L* is:
      x·(L−a)/L  if x ≤ a
      a·(L−x)/L  if x > a

    Peaks at x = a with ordinate a(L−a)/L.
    """
    x = np.linspace(0, span, num_points)
    ordinates = np.where(
        x <= location,
        x * (span - location) / span,
        location * (span - x) / span,
    )

    return InfluenceLine(
        positions=x,
        ordinates=ordinates,
        span=span,
        quantity="moment",
        location=location,
    )


def generate_shear_influence_line(
    span: float,
    location: float,
    num_points: int = 201,
    side: str = "left",
) -> InfluenceLine:
    """Shear-force IL for a simply supported beam.

    The IL has unit discontinuity at the section.  *side* controls
    which convention we use (left / right of the cut).
    """
    x = np.linspace(0, span, num_points)
    ordinates = np.zeros_like(x)

    for i, xi in enumerate(x):
        if xi < location:
            # load left of section
            if side == "right":
                ordinates[i] = -xi / span
            else:
                ordinates[i] = (span - xi) / span
        elif xi > location:
            # load right of section
            if side == "right":
                ordinates[i] = (span - xi) / span
            else:
                ordinates[i] = -xi / span
        else:
            # at section — take the unfavourable value
            ordinates[i] = (span - location) / span

    return InfluenceLine(
        positions=x,
        ordinates=ordinates,
        span=span,
        quantity="shear",
        location=location,
    )


def calculate_load_effect_from_il(
    il: InfluenceLine,
    vehicle: VehicleLoad,
    vehicle_position: float,
) -> float:
    """Superposition: Effect = Σ P_i · η_i for axles on the span."""
    total_effect = 0.0

    for axle in vehicle.axles:
        axle_pos = vehicle_position + axle.position

        if 0 <= axle_pos <= il.span:
            # interpolate IL ordinate
            il_ordinate = np.interp(axle_pos, il.positions, il.ordinates)
            total_effect += axle.load * il_ordinate

    return total_effect


def find_critical_vehicle_position(
    il: InfluenceLine,
    vehicle: VehicleLoad,
    step_size: float = 0.1,
) -> Tuple[float, float]:
    """Brute-force sweep to find the placement that maximises the
    load effect.  Returns (position_of_front, max_effect).
    """
    # vehicle can be partially or fully on span
    start_pos = -vehicle.total_length
    end_pos = il.span + step_size

    positions = np.arange(start_pos, end_pos, step_size)
    max_effect = 0.0
    critical_pos = 0.0

    for pos in positions:
        effect = calculate_load_effect_from_il(il, vehicle, pos)
        if effect > max_effect:
            max_effect = effect
            critical_pos = pos

    return critical_pos, max_effect


def find_absolute_max_moment(
    span: float,
    vehicle: VehicleLoad,
    num_sections: int = 21,
    step_size: float = 0.1,
) -> Tuple[float, float, float]:
    """Search between 0.3 L and 0.7 L for the absolute max BM.

    Returns (max_moment, section_location, vehicle_front_pos).
    """
    max_moment = 0.0
    moment_location = span / 2
    vehicle_pos = 0.0

    # max BM is usually between 0.3L and 0.7L for standard trains
    for section_loc in np.linspace(0.3 * span, 0.7 * span, num_sections):
        il_moment = generate_moment_influence_line(span, section_loc)
        crit_pos, moment = find_critical_vehicle_position(
            il_moment, vehicle, step_size
        )
        if moment > max_moment:
            max_moment = moment
            moment_location = section_loc
            vehicle_pos = crit_pos

    return max_moment, moment_location, vehicle_pos


def analyze_moving_load(
    span: float,
    vehicle: VehicleLoad,
    impact_factor: float = 1.0,
) -> Dict[str, float]:
    """Full moving-load envelope for a simply-supported span.

    Finds max midspan BM, absolute max BM, and max support shears
    then applies the impact factor.
    """
    results = {}

    # -- midspan moment --
    il_moment_mid = generate_moment_influence_line(span, span / 2)
    crit_pos_moment, max_moment_mid = find_critical_vehicle_position(
        il_moment_mid, vehicle
    )

    results["max_moment_midspan_kNm"] = max_moment_mid * impact_factor
    results["critical_position_moment_m"] = crit_pos_moment

    # -- absolute max moment (sweep along span) --
    max_moment_overall, max_moment_location, _ = find_absolute_max_moment(
        span, vehicle
    )

    results["absolute_max_moment_kNm"] = max_moment_overall * impact_factor
    results["absolute_max_moment_location_m"] = max_moment_location

    # -- max shear at left support --
    # heavy axles near support give max shear
    il_shear_left = generate_shear_influence_line(span, 0.01, side="right")
    _, max_shear_left = find_critical_vehicle_position(il_shear_left, vehicle)

    results["max_shear_left_kN"] = max_shear_left * impact_factor

    # -- max shear at right support --
    il_shear_right = generate_shear_influence_line(span, span - 0.01, side="left")
    _, max_shear_right = find_critical_vehicle_position(il_shear_right, vehicle)

    results["max_shear_right_kN"] = max_shear_right * impact_factor

    # governing shear (symmetric span → roughly equal)
    results["max_shear_kN"] = max(
        results["max_shear_left_kN"], results["max_shear_right_kN"]
    )

    return results

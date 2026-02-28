"""
Moving Load Analysis for Bridge Girders

Implements influence line based analysis for determining:
- Maximum bending moment and its position along span
- Maximum shear force at supports and critical sections
- Critical vehicle placement using Muller-Breslau principle

The approach sweeps each IRC vehicle load train across the span,
evaluating influence line ordinates at each position to find the
worst-case load effect.

Reference:
    Structural Analysis by Hibbeler, Ch. 6 (Influence Lines)
    IRC:6-2017 for vehicle configurations
"""

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

from ..utils.codes.irc6_2017 import VehicleLoad


@dataclass
class InfluenceLine:
    """
    Influence line ordinates at discrete points along the span.

    An influence line shows the variation of a particular response
    (moment, shear, reaction) at a FIXED section as a unit load
    moves across the span.
    """
    positions: np.ndarray   # Positions along span (m)
    ordinates: np.ndarray   # IL ordinates at each position
    span: float             # Total span (m)
    quantity: str           # "moment" or "shear"
    location: float         # Section where quantity is measured (m from left)


def generate_moment_influence_line(
    span: float,
    location: float,
    num_points: int = 201,
) -> InfluenceLine:
    """
    Generate moment influence line for simply supported beam.

    For a unit load P=1 at position x on a simply supported beam
    of span L, the bending moment at section 'a' is:

        M(a) = x·(L - a)/L    for x ≤ a  (load to left of section)
        M(a) = a·(L - x)/L    for x > a  (load to right of section)

    The IL peaks at x = a with ordinate = a·(L-a)/L

    Args:
        span: Beam span in meters
        location: Section where moment is measured (m from left support)
        num_points: Number of discrete points for IL

    Returns:
        InfluenceLine object with moment IL ordinates

    Example:
        >>> il = generate_moment_influence_line(30, 15)
        >>> il.ordinates.max()  # Peak at midspan
        7.5
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
    """
    Generate shear force influence line for simply supported beam.

    For a unit load P=1 at position x, shear at section 'a':

    Right side convention (positive shear = clockwise rotation):
        V = -(x/L)        for x < a  (load left of section)
        V = (L-x)/L       for x ≥ a  (load at or right of section)

    The IL has a discontinuity at x = a (jump of magnitude 1.0).

    Args:
        span: Beam span in meters
        location: Section where shear is measured (m from left)
        num_points: Number of discrete points
        side: "left" for shear just left of location,
              "right" for just right of location

    Returns:
        InfluenceLine object
    """
    x = np.linspace(0, span, num_points)
    ordinates = np.zeros_like(x)

    for i, xi in enumerate(x):
        if xi < location:
            # Load is to the left of the section
            if side == "right":
                ordinates[i] = -xi / span
            else:
                ordinates[i] = (span - xi) / span
        elif xi > location:
            # Load is to the right of the section
            if side == "right":
                ordinates[i] = (span - xi) / span
            else:
                ordinates[i] = -xi / span
        else:
            # Load exactly at section - take the unfavourable (larger) value
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
    """
    Calculate load effect (moment or shear) from influence line.

    Uses superposition principle:
        Effect = Σ(Pi × ηi)
    where Pi is the axle load and ηi is the influence line ordinate
    at the axle's position.

    Only axles physically ON the span contribute (0 ≤ x ≤ L).

    Args:
        il: Influence line object
        vehicle: VehicleLoad with axle configuration
        vehicle_position: Position of vehicle front from left support (m)

    Returns:
        Total load effect (kN·m for moment, kN for shear)
    """
    total_effect = 0.0

    for axle in vehicle.axles:
        # Absolute position of this axle on the span
        axle_pos = vehicle_position + axle.position

        # Only count axle if it's on the span
        if 0 <= axle_pos <= il.span:
            # Interpolate IL ordinate at axle position
            il_ordinate = np.interp(axle_pos, il.positions, il.ordinates)
            total_effect += axle.load * il_ordinate

    return total_effect


def find_critical_vehicle_position(
    il: InfluenceLine,
    vehicle: VehicleLoad,
    step_size: float = 0.1,
) -> Tuple[float, float]:
    """
    Find vehicle position that maximizes the load effect.

    Sweeps the vehicle from fully off-span (left) to fully off-span (right),
    computing the load effect at each step.

    Args:
        il: Influence line
        vehicle: VehicleLoad configuration
        step_size: Position increment in meters (smaller = more accurate)

    Returns:
        Tuple of (critical_position, maximum_effect)
        critical_position: Front of vehicle from left support (m)
    """
    # Vehicle can start before span (partially on) to fully past
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
    """
    Find absolute maximum bending moment anywhere on the span.

    Checks multiple sections along the span (typically between 0.3L
    and 0.7L where maximum moment occurs for most load patterns).

    Args:
        span: Span in meters
        vehicle: VehicleLoad configuration
        num_sections: Number of sections to check
        step_size: Vehicle sweep step size

    Returns:
        Tuple of (max_moment_kNm, moment_location_m, vehicle_position_m)
    """
    max_moment = 0.0
    moment_location = span / 2
    vehicle_pos = 0.0

    # For simply supported beams, max moment occurs between 0.3L and 0.7L
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
    """
    Complete moving load analysis for a simply supported span.

    Finds:
    - Maximum midspan moment and critical vehicle position
    - Absolute maximum moment (searching along span)
    - Maximum shear at both supports
    - All results multiplied by impact factor

    Args:
        span: Span length in meters
        vehicle: VehicleLoad configuration
        impact_factor: Dynamic amplification factor (e.g., 1.25 for 25% impact)

    Returns:
        Dictionary with all analysis results:
        - max_moment_midspan_kNm: Max BM at midspan
        - absolute_max_moment_kNm: Max BM anywhere on span
        - absolute_max_moment_location_m: Section where max BM occurs
        - max_shear_kN: Maximum shear at supports
        - critical_position_moment_m: Vehicle front position for max moment

    Example:
        >>> from osdagbridge.core.utils.codes.irc6_2017 import get_class_a_train
        >>> vehicle = get_class_a_train()
        >>> results = analyze_moving_load(30.0, vehicle, impact_factor=1.383)
        >>> results["absolute_max_moment_kNm"]  # Will be > 0
    """
    results = {}

    # ── Maximum midspan moment ──
    il_moment_mid = generate_moment_influence_line(span, span / 2)
    crit_pos_moment, max_moment_mid = find_critical_vehicle_position(
        il_moment_mid, vehicle
    )

    results["max_moment_midspan_kNm"] = max_moment_mid * impact_factor
    results["critical_position_moment_m"] = crit_pos_moment

    # ── Absolute maximum moment (search along span) ──
    max_moment_overall, max_moment_location, _ = find_absolute_max_moment(
        span, vehicle
    )

    results["absolute_max_moment_kNm"] = max_moment_overall * impact_factor
    results["absolute_max_moment_location_m"] = max_moment_location

    # ── Maximum shear at left support ──
    # Shear is maximum when heavy axles are near the support
    il_shear_left = generate_shear_influence_line(span, 0.01, side="right")
    _, max_shear_left = find_critical_vehicle_position(il_shear_left, vehicle)

    results["max_shear_left_kN"] = max_shear_left * impact_factor

    # ── Maximum shear at right support ──
    il_shear_right = generate_shear_influence_line(span, span - 0.01, side="left")
    _, max_shear_right = find_critical_vehicle_position(il_shear_right, vehicle)

    results["max_shear_right_kN"] = max_shear_right * impact_factor

    # Governing shear (symmetric span → should be approximately equal)
    results["max_shear_kN"] = max(
        results["max_shear_left_kN"], results["max_shear_right_kN"]
    )

    return results

"""
Load Combinations as per IRC:6-2017 and IS 800:2007

Implements limit state design load combinations for bridge structures.
Both Ultimate Limit State (ULS) and Serviceability Limit State (SLS)
combinations are covered with appropriate partial safety factors.

Reference:
    - IRC:6-2017, Table 1 to Table 6
    - IS 800:2007, Table 4
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class LimitState(Enum):
    """Limit state types for bridge design."""
    ULS_BASIC = "uls_basic"                     # Ultimate limit state - Basic combination
    ULS_SEISMIC = "uls_seismic"                 # ULS with seismic
    ULS_ACCIDENTAL = "uls_accidental"           # ULS with accidental loads
    SLS_RARE = "sls_rare"                       # Serviceability - rare combination
    SLS_FREQUENT = "sls_frequent"               # Serviceability - frequent
    SLS_QUASI_PERMANENT = "sls_quasi_permanent"  # Quasi-permanent


@dataclass
class PartialSafetyFactor:
    """
    Partial safety factors for different load types.

    γ_f values applied to characteristic loads to get design loads.
    ULS factors are typically > 1.0 (amplification).
    SLS factors are typically 1.0 (service-level check).
    """
    dead_load_favourable: float = 1.0
    dead_load_unfavourable: float = 1.35
    superimposed_dead_load: float = 1.35
    live_load: float = 1.50
    wind_load: float = 1.50
    temperature: float = 1.0
    seismic: float = 1.50
    earth_pressure: float = 1.50
    braking_force: float = 1.50
    centrifugal_force: float = 1.50

    def get_factored_load(self, load_type: str, characteristic_load: float) -> float:
        """
        Apply partial safety factor to a characteristic load.

        Args:
            load_type: One of 'dead', 'superimposed', 'live', 'wind',
                       'temperature', 'seismic', 'earth', 'braking', 'centrifugal'
            characteristic_load: Unfactored characteristic load value

        Returns:
            Factored design load
        """
        factor_map = {
            "dead_favourable": self.dead_load_favourable,
            "dead_unfavourable": self.dead_load_unfavourable,
            "dead": self.dead_load_unfavourable,  # default to unfavourable
            "superimposed": self.superimposed_dead_load,
            "live": self.live_load,
            "wind": self.wind_load,
            "temperature": self.temperature,
            "seismic": self.seismic,
            "earth": self.earth_pressure,
            "braking": self.braking_force,
            "centrifugal": self.centrifugal_force,
        }
        factor = factor_map.get(load_type, 1.0)
        return factor * characteristic_load


def get_uls_basic_factors() -> PartialSafetyFactor:
    """
    Get ULS basic combination partial safety factors.

    Basic combination: Dead + Superimposed Dead + Live + Wind (or Temperature)
    Seismic is NOT considered in basic combination.

    As per IS 800:2007 Table 4 and IRC:6-2017 Table 3.

    Returns:
        PartialSafetyFactor for ULS basic combination
    """
    return PartialSafetyFactor(
        dead_load_favourable=1.0,
        dead_load_unfavourable=1.35,
        superimposed_dead_load=1.35,
        live_load=1.50,
        wind_load=1.50,
        temperature=1.0,
        seismic=0.0,  # Not considered in basic combination
        earth_pressure=1.50,
        braking_force=1.50,
        centrifugal_force=1.50,
    )


def get_uls_seismic_factors() -> PartialSafetyFactor:
    """
    Get ULS seismic combination partial safety factors.

    Seismic combination: Dead + Superimposed Dead + Reduced Live + Seismic
    Wind is NOT combined with seismic (IRC:6-2017 Clause 219.5.2).

    Returns:
        PartialSafetyFactor for ULS seismic combination
    """
    return PartialSafetyFactor(
        dead_load_favourable=1.0,
        dead_load_unfavourable=1.35,
        superimposed_dead_load=1.35,
        live_load=0.75,    # Reduced live load with seismic
        wind_load=0.0,     # Not combined with seismic
        temperature=0.50,
        seismic=1.50,
        earth_pressure=1.0,
        braking_force=0.50,  # Reduced with seismic
        centrifugal_force=0.0,
    )


def get_uls_accidental_factors() -> PartialSafetyFactor:
    """
    Get ULS accidental combination partial safety factors.

    Accidental combination: For vehicle collision on parapets, etc.

    Returns:
        PartialSafetyFactor for ULS accidental combination
    """
    return PartialSafetyFactor(
        dead_load_favourable=1.0,
        dead_load_unfavourable=1.0,  # Reduced for accidental
        superimposed_dead_load=1.0,
        live_load=0.75,
        wind_load=0.0,
        temperature=0.50,
        seismic=0.0,
        earth_pressure=1.0,
        braking_force=0.75,
        centrifugal_force=0.0,
    )


def get_sls_rare_factors() -> PartialSafetyFactor:
    """
    Get SLS rare combination factors (all factors = 1.0).

    Rare combination used for checking stress limits and crack width.

    Returns:
        PartialSafetyFactor for SLS rare combination
    """
    return PartialSafetyFactor(
        dead_load_favourable=1.0,
        dead_load_unfavourable=1.0,
        superimposed_dead_load=1.0,
        live_load=1.0,
        wind_load=1.0,
        temperature=1.0,
        seismic=0.0,
        earth_pressure=1.0,
        braking_force=1.0,
        centrifugal_force=1.0,
    )


def get_sls_frequent_factors() -> PartialSafetyFactor:
    """
    Get SLS frequent combination factors.

    Used for checking deflection and vibration under regular traffic.
    Live load reduced to 75% of characteristic value.

    Returns:
        PartialSafetyFactor for SLS frequent combination
    """
    return PartialSafetyFactor(
        dead_load_favourable=1.0,
        dead_load_unfavourable=1.0,
        superimposed_dead_load=1.0,
        live_load=0.75,   # Frequent value
        wind_load=0.50,   # Reduced wind
        temperature=0.60,
        seismic=0.0,
        earth_pressure=1.0,
        braking_force=0.75,
        centrifugal_force=0.75,
    )


def get_sls_quasi_permanent_factors() -> PartialSafetyFactor:
    """
    Get SLS quasi-permanent combination factors.

    Used for long-term effects like creep and settlement.
    Only permanent and semi-permanent portions of variable loads considered.

    Returns:
        PartialSafetyFactor for SLS quasi-permanent combination
    """
    return PartialSafetyFactor(
        dead_load_favourable=1.0,
        dead_load_unfavourable=1.0,
        superimposed_dead_load=1.0,
        live_load=0.0,     # No live load in quasi-permanent
        wind_load=0.0,
        temperature=0.50,  # Only thermal gradient component
        seismic=0.0,
        earth_pressure=1.0,
        braking_force=0.0,
        centrifugal_force=0.0,
    )


def get_factors_for_limit_state(limit_state: LimitState) -> PartialSafetyFactor:
    """
    Get partial safety factors for a given limit state.

    Convenience function to retrieve appropriate factors based on
    the limit state being checked.

    Args:
        limit_state: LimitState enum value

    Returns:
        PartialSafetyFactor for the requested limit state
    """
    factors_map = {
        LimitState.ULS_BASIC: get_uls_basic_factors,
        LimitState.ULS_SEISMIC: get_uls_seismic_factors,
        LimitState.ULS_ACCIDENTAL: get_uls_accidental_factors,
        LimitState.SLS_RARE: get_sls_rare_factors,
        LimitState.SLS_FREQUENT: get_sls_frequent_factors,
        LimitState.SLS_QUASI_PERMANENT: get_sls_quasi_permanent_factors,
    }
    return factors_map[limit_state]()


@dataclass
class LoadCase:
    """
    Single load case with component loads.

    Stores characteristic (unfactored) loads for a bridge load case.
    Dead loads, superimposed dead loads, and various live loads.
    """
    name: str
    dead_load: float = 0.0          # kN or kN/m (self-weight of steel)
    superimposed_dead: float = 0.0  # kN or kN/m (wearing coat, railing, etc.)
    live_load: float = 0.0          # kN or kN/m (vehicle load)
    wind_load: float = 0.0          # kN or kN/m
    temperature_load: float = 0.0   # kN or kN/m
    seismic_load: float = 0.0       # kN or kN/m
    braking_load: float = 0.0       # kN (longitudinal)
    centrifugal_load: float = 0.0   # kN (for curved bridges)

    def get_factored_total(self, factors: PartialSafetyFactor) -> float:
        """
        Calculate total factored load for a given set of partial safety factors.

        Args:
            factors: PartialSafetyFactor for the target limit state

        Returns:
            Total factored load (sum of all factored components)
        """
        total = (
            factors.dead_load_unfavourable * self.dead_load
            + factors.superimposed_dead_load * self.superimposed_dead
            + factors.live_load * self.live_load
            + factors.wind_load * self.wind_load
            + factors.temperature * self.temperature_load
            + factors.seismic * self.seismic_load
            + factors.braking_force * self.braking_load
            + factors.centrifugal_force * self.centrifugal_load
        )
        return total

    def get_factored_breakdown(self, factors: PartialSafetyFactor) -> Dict[str, float]:
        """
        Get breakdown of factored loads by component.

        Args:
            factors: PartialSafetyFactor for the target limit state

        Returns:
            Dictionary mapping load type to factored value
        """
        return {
            "dead_load": factors.dead_load_unfavourable * self.dead_load,
            "superimposed_dead": factors.superimposed_dead_load * self.superimposed_dead,
            "live_load": factors.live_load * self.live_load,
            "wind_load": factors.wind_load * self.wind_load,
            "temperature": factors.temperature * self.temperature_load,
            "seismic": factors.seismic * self.seismic_load,
            "braking": factors.braking_force * self.braking_load,
            "centrifugal": factors.centrifugal_force * self.centrifugal_load,
        }


def generate_all_combinations(load_case: LoadCase) -> Dict[str, float]:
    """
    Generate factored totals for all limit state combinations.

    Useful for finding the governing (maximum) design load.

    Args:
        load_case: LoadCase with characteristic loads

    Returns:
        Dictionary mapping limit state name to factored total

    Example:
        >>> lc = LoadCase("midspan", dead_load=50, live_load=120)
        >>> combos = generate_all_combinations(lc)
        >>> max_combo = max(combos, key=combos.get)
    """
    results = {}
    for ls in LimitState:
        factors = get_factors_for_limit_state(ls)
        results[ls.value] = load_case.get_factored_total(factors)
    return results

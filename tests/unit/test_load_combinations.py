"""
Unit tests for load combinations module.

Tests verify:
- Partial safety factors match code values
- Load case factoring works correctly
- All limit state combinations produce expected results
"""

import pytest

from osdagbridge.core.utils.codes.load_combinations import (
    LimitState,
    LoadCase,
    PartialSafetyFactor,
    generate_all_combinations,
    get_factors_for_limit_state,
    get_sls_frequent_factors,
    get_sls_quasi_permanent_factors,
    get_sls_rare_factors,
    get_uls_basic_factors,
    get_uls_seismic_factors,
)


class TestPartialSafetyFactors:
    """Tests for partial safety factor values."""

    def test_uls_basic_dead_load(self):
        """ULS basic: Dead load unfavourable = 1.35."""
        f = get_uls_basic_factors()
        assert f.dead_load_unfavourable == 1.35

    def test_uls_basic_live_load(self):
        """ULS basic: Live load = 1.50."""
        f = get_uls_basic_factors()
        assert f.live_load == 1.50

    def test_uls_basic_no_seismic(self):
        """ULS basic: Seismic = 0 (not considered)."""
        f = get_uls_basic_factors()
        assert f.seismic == 0.0

    def test_uls_seismic_reduced_live(self):
        """ULS seismic: Live load reduced to 0.75."""
        f = get_uls_seismic_factors()
        assert f.live_load == 0.75

    def test_uls_seismic_no_wind(self):
        """ULS seismic: Wind = 0 (not combined with seismic)."""
        f = get_uls_seismic_factors()
        assert f.wind_load == 0.0

    def test_sls_rare_all_unity(self):
        """SLS rare: All variable load factors = 1.0."""
        f = get_sls_rare_factors()
        assert f.dead_load_unfavourable == 1.0
        assert f.live_load == 1.0
        assert f.wind_load == 1.0

    def test_sls_frequent_reduced_live(self):
        """SLS frequent: Live load reduced to 0.75."""
        f = get_sls_frequent_factors()
        assert f.live_load == 0.75

    def test_sls_quasi_permanent_no_live(self):
        """SLS quasi-permanent: No live load."""
        f = get_sls_quasi_permanent_factors()
        assert f.live_load == 0.0


class TestLoadCase:
    """Tests for LoadCase factoring."""

    def test_factored_total_uls(self):
        """Factored total for ULS basic combination."""
        lc = LoadCase(
            name="midspan",
            dead_load=50.0,
            live_load=100.0,
        )
        factors = get_uls_basic_factors()
        total = lc.get_factored_total(factors)
        expected = 1.35 * 50 + 1.50 * 100  # 67.5 + 150 = 217.5
        assert abs(total - expected) < 0.01

    def test_factored_total_sls(self):
        """Factored total for SLS rare should equal characteristic."""
        lc = LoadCase(
            name="midspan",
            dead_load=50.0,
            live_load=100.0,
        )
        factors = get_sls_rare_factors()
        total = lc.get_factored_total(factors)
        expected = 50 + 100  # All factors = 1.0
        assert abs(total - expected) < 0.01

    def test_factored_breakdown(self):
        """Breakdown should show individual factored components."""
        lc = LoadCase(
            name="test",
            dead_load=50.0,
            live_load=100.0,
            wind_load=20.0,
        )
        factors = get_uls_basic_factors()
        breakdown = lc.get_factored_breakdown(factors)

        assert abs(breakdown["dead_load"] - 67.5) < 0.01
        assert abs(breakdown["live_load"] - 150.0) < 0.01
        assert abs(breakdown["wind_load"] - 30.0) < 0.01


class TestGetFactorsForLimitState:
    """Tests for convenience function."""

    def test_returns_correct_type(self):
        """Should return PartialSafetyFactor for any valid limit state."""
        for ls in LimitState:
            f = get_factors_for_limit_state(ls)
            assert isinstance(f, PartialSafetyFactor)


class TestGenerateAllCombinations:
    """Tests for generating all combinations."""

    def test_all_limit_states_present(self):
        """Should have results for all 6 limit states."""
        lc = LoadCase(name="test", dead_load=50, live_load=100)
        combos = generate_all_combinations(lc)
        assert len(combos) == len(LimitState)

    def test_uls_higher_than_sls(self):
        """ULS basic total should be > SLS rare for same loads."""
        lc = LoadCase(name="test", dead_load=50, live_load=100)
        combos = generate_all_combinations(lc)
        assert combos["uls_basic"] > combos["sls_rare"]

    def test_quasi_permanent_lowest(self):
        """Quasi-permanent should give lowest total (no live load)."""
        lc = LoadCase(name="test", dead_load=50, live_load=100)
        combos = generate_all_combinations(lc)
        assert combos["sls_quasi_permanent"] <= combos["sls_rare"]

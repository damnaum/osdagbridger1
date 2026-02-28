"""
Unit tests for moving load analysis module.

Tests verify:
- Influence line generation (moment and shear)
- Load effect calculation from IL
- Critical vehicle position finding
- Complete moving load analysis results
"""

import math

import numpy as np
import pytest

from osdagbridge.core.loads.moving_load import (
    InfluenceLine,
    analyze_moving_load,
    calculate_load_effect_from_il,
    find_absolute_max_moment,
    find_critical_vehicle_position,
    generate_moment_influence_line,
    generate_shear_influence_line,
)
from osdagbridge.core.utils.codes.irc6_2017 import (
    AxleLoad,
    VehicleLoad,
    VehicleType,
    get_class_70r_wheeled,
    get_class_a_train,
)


class TestMomentInfluenceLine:
    """Tests for moment influence line generation."""

    def test_moment_il_zero_at_supports(self):
        """Moment IL should be zero at both supports."""
        il = generate_moment_influence_line(30, 15)
        assert abs(il.ordinates[0]) < 1e-10   # Left support
        assert abs(il.ordinates[-1]) < 1e-10  # Right support

    def test_moment_il_peak_at_location(self):
        """Moment IL peaks at the section location."""
        span = 30.0
        location = 15.0  # midspan
        il = generate_moment_influence_line(span, location)
        # Peak ordinate = a*(L-a)/L = 15*15/30 = 7.5
        peak = il.ordinates.max()
        expected = location * (span - location) / span
        assert abs(peak - expected) < 0.1

    def test_moment_il_non_negative(self):
        """Moment IL for simply supported beam is always non-negative."""
        il = generate_moment_influence_line(30, 10)
        assert np.all(il.ordinates >= -1e-10)

    def test_moment_il_quarter_point(self):
        """Test IL at quarter point."""
        span = 20.0
        location = 5.0  # L/4
        il = generate_moment_influence_line(span, location)
        # Peak = 5*15/20 = 3.75
        expected = 5.0 * 15.0 / 20.0
        assert abs(il.ordinates.max() - expected) < 0.1


class TestShearInfluenceLine:
    """Tests for shear influence line generation."""

    def test_shear_il_at_support(self):
        """Shear IL at left support should have max ordinate near 1.0."""
        il = generate_shear_influence_line(30, 0.01, side="right")
        # When load is at left support, V ≈ (L-0)/L ≈ 1.0
        assert il.ordinates.max() > 0.9

    def test_shear_il_changes_sign(self):
        """Shear IL should have both positive and negative values (at midspan)."""
        il = generate_shear_influence_line(30, 15, side="right")
        # Should have negative values when load is to the left
        assert il.ordinates.min() < 0

    def test_shear_il_discontinuity(self):
        """Shear IL has a jump at the section location."""
        il = generate_shear_influence_line(30, 15, side="right")
        # At x=15: ordinate should be (30-15)/30 = 0.5 (positive)
        # Just before x=15: ordinate should be -15/30 = -0.5
        # This is a jump of 1.0
        assert il.ordinates.max() > 0.4


class TestLoadEffectCalculation:
    """Tests for computing load effects from influence lines."""

    def test_single_axle_midspan(self):
        """Single axle at midspan of moment IL at midspan."""
        span = 20.0
        il = generate_moment_influence_line(span, 10.0)

        # Single 100 kN axle
        vehicle = VehicleLoad(
            vehicle_type=VehicleType.CLASS_A,
            axles=[AxleLoad(load=100.0, position=0.0)],
            total_length=0.5,
            min_spacing_same_lane=20.0,
        )

        # Place axle at midspan (vehicle front at x=10)
        effect = calculate_load_effect_from_il(il, vehicle, 10.0)
        # M = P * η = 100 * (10*10/20) = 100 * 5 = 500 kN.m
        expected = 100.0 * 10.0 * 10.0 / 20.0
        assert abs(effect - expected) < 1.0

    def test_axle_off_span(self):
        """Axle off the span should contribute zero."""
        span = 20.0
        il = generate_moment_influence_line(span, 10.0)

        vehicle = VehicleLoad(
            vehicle_type=VehicleType.CLASS_A,
            axles=[AxleLoad(load=100.0, position=0.0)],
            total_length=0.5,
            min_spacing_same_lane=20.0,
        )

        # Place axle before the span
        effect = calculate_load_effect_from_il(il, vehicle, -5.0)
        assert abs(effect) < 1e-10

    def test_two_axles(self):
        """Two axles should give sum of individual effects."""
        span = 20.0
        il = generate_moment_influence_line(span, 10.0)

        vehicle = VehicleLoad(
            vehicle_type=VehicleType.CLASS_A,
            axles=[
                AxleLoad(load=50.0, position=0.0),
                AxleLoad(load=50.0, position=2.0),
            ],
            total_length=2.5,
            min_spacing_same_lane=20.0,
        )

        # Place vehicle so first axle is at x=9, second at x=11
        effect = calculate_load_effect_from_il(il, vehicle, 9.0)
        # Both axles near midspan, each contributes ~50*5 = 250
        assert effect > 400  # Should be close to 500


class TestCriticalPosition:
    """Tests for finding critical vehicle position."""

    def test_critical_position_found(self):
        """Should find a position that gives positive moment."""
        span = 30.0
        il = generate_moment_influence_line(span, 15.0)
        vehicle = get_class_a_train()

        _crit_pos, max_effect = find_critical_vehicle_position(il, vehicle)
        assert max_effect > 0

    def test_critical_moment_reasonable(self):
        """Critical moment for Class A on 30m span should be in known range."""
        span = 30.0
        il = generate_moment_influence_line(span, 15.0)
        vehicle = get_class_a_train()

        _, max_moment = find_critical_vehicle_position(il, vehicle)
        # For 30m span with Class A, midspan moment should be ~1500-2500 kN.m
        assert 1000 < max_moment < 3000


class TestAbsoluteMaxMoment:
    """Tests for finding absolute maximum moment."""

    def test_max_moment_location_near_midspan(self):
        """Max moment location should be near midspan for symmetric loading."""
        vehicle = get_class_a_train()
        _max_m, location, _ = find_absolute_max_moment(30.0, vehicle)
        # Should be within 30% to 70% of span
        assert 9.0 < location < 21.0

    def test_max_moment_greater_than_zero(self):
        """Absolute max moment should be positive."""
        vehicle = get_class_a_train()
        max_m, _, _ = find_absolute_max_moment(30.0, vehicle)
        assert max_m > 0


class TestMovingLoadAnalysis:
    """Tests for the complete moving load analysis."""

    def test_analysis_returns_all_keys(self):
        """Analysis should return all expected result keys."""
        vehicle = get_class_a_train()
        results = analyze_moving_load(30.0, vehicle, 1.0)

        expected_keys = [
            "max_moment_midspan_kNm",
            "absolute_max_moment_kNm",
            "absolute_max_moment_location_m",
            "max_shear_left_kN",
            "max_shear_right_kN",
            "max_shear_kN",
        ]
        for key in expected_keys:
            assert key in results

    def test_analysis_positive_results(self):
        """All analysis results should be positive."""
        vehicle = get_class_a_train()
        results = analyze_moving_load(30.0, vehicle, 1.0)

        assert results["max_moment_midspan_kNm"] > 0
        assert results["absolute_max_moment_kNm"] > 0
        assert results["max_shear_kN"] > 0

    def test_impact_factor_amplifies(self):
        """Impact factor should amplify all results."""
        vehicle = get_class_a_train()
        results_no_impact = analyze_moving_load(30.0, vehicle, 1.0)
        results_with_impact = analyze_moving_load(30.0, vehicle, 1.25)

        ratio = (
            results_with_impact["max_moment_midspan_kNm"]
            / results_no_impact["max_moment_midspan_kNm"]
        )
        assert abs(ratio - 1.25) < 0.01

    def test_absolute_max_geq_midspan(self):
        """Absolute max moment should be >= midspan moment."""
        vehicle = get_class_a_train()
        results = analyze_moving_load(30.0, vehicle, 1.0)
        assert (
            results["absolute_max_moment_kNm"]
            >= results["max_moment_midspan_kNm"] - 1.0  # small tolerance
        )

    def test_70r_higher_than_class_a(self):
        """70R vehicle should produce higher effects than Class A."""
        class_a = get_class_a_train()
        class_70r = get_class_70r_wheeled()

        results_a = analyze_moving_load(30.0, class_a, 1.0)
        results_70r = analyze_moving_load(30.0, class_70r, 1.0)

        assert results_70r["max_shear_kN"] > results_a["max_shear_kN"]

    def test_longer_span_higher_moment(self):
        """Longer span should generally produce higher moment."""
        vehicle = get_class_a_train()
        results_20 = analyze_moving_load(20.0, vehicle, 1.0)
        results_40 = analyze_moving_load(40.0, vehicle, 1.0)

        assert (
            results_40["absolute_max_moment_kNm"]
            > results_20["absolute_max_moment_kNm"]
        )

"""
IRC:6-2017 vehicle-load tests.

Make sure axle configs, impact factors, lane factors,
and congestion factors match the code tables.
"""

import math

import pytest

from osdagbridge.core.utils.codes.irc6_2017 import (
    AxleLoad,
    VehicleLoad,
    VehicleType,
    get_all_vehicle_types,
    get_class_70r_bogie,
    get_class_70r_tracked,
    get_class_70r_wheeled,
    get_class_a_train,
    get_class_aa_tracked,
    get_class_aa_wheeled,
    get_class_b_train,
    get_congestion_factor,
    get_impact_factor,
    get_lane_distribution_factor,
    get_vehicle_loads,
)


class TestClassALoading:
    """Tests for IRC Class A vehicle loading."""

    def test_class_a_total_load(self):
        """Class A train total load should be 554 kN."""
        vehicle = get_class_a_train()
        # 2*27 + 2*114 + 4*68 = 54 + 228 + 272 = 554 kN
        assert abs(vehicle.total_load - 554.0) < 0.1

    def test_class_a_axle_count(self):
        """Class A train has 8 axles."""
        vehicle = get_class_a_train()
        assert len(vehicle.axles) == 8

    def test_class_a_front_axle_spacing(self):
        """First two axles spaced 1.1m apart."""
        vehicle = get_class_a_train()
        spacing = vehicle.axles[1].position - vehicle.axles[0].position
        assert abs(spacing - 1.1) < 0.01

    def test_class_a_middle_gap(self):
        """Gap between front and middle group is 3.2m."""
        vehicle = get_class_a_train()
        gap = vehicle.axles[2].position - vehicle.axles[1].position
        assert abs(gap - 3.2) < 0.01

    def test_class_a_middle_axle_spacing(self):
        """Middle axles (114 kN each) spaced 1.2m apart."""
        vehicle = get_class_a_train()
        spacing = vehicle.axles[3].position - vehicle.axles[2].position
        assert abs(spacing - 1.2) < 0.01

    def test_class_a_rear_axle_spacing(self):
        """Rear axles (68 kN each) spaced 3.0m apart."""
        vehicle = get_class_a_train()
        # Axles 4,5,6,7 are 68 kN axles
        for i in range(5, 8):
            spacing = vehicle.axles[i].position - vehicle.axles[i - 1].position
            assert abs(spacing - 3.0) < 0.01

    def test_class_a_min_spacing(self):
        """Minimum spacing between Class A trains is 18.5m."""
        vehicle = get_class_a_train()
        assert vehicle.min_spacing_same_lane == 18.5

    def test_class_a_vehicle_type(self):
        """Vehicle type should be CLASS_A."""
        vehicle = get_class_a_train()
        assert vehicle.vehicle_type == VehicleType.CLASS_A

    def test_class_a_front_axle_loads(self):
        """Front axles are 27 kN each."""
        vehicle = get_class_a_train()
        assert vehicle.axles[0].load == 27.0
        assert vehicle.axles[1].load == 27.0

    def test_class_a_middle_axle_loads(self):
        """Middle axles are 114 kN each."""
        vehicle = get_class_a_train()
        assert vehicle.axles[2].load == 114.0
        assert vehicle.axles[3].load == 114.0

    def test_class_a_rear_axle_loads(self):
        """Rear axles are 68 kN each."""
        vehicle = get_class_a_train()
        for i in range(4, 8):
            assert vehicle.axles[i].load == 68.0

    def test_class_a_axle_positions_array(self):
        """axle_positions property returns numpy array."""
        vehicle = get_class_a_train()
        positions = vehicle.axle_positions
        assert len(positions) == 8
        assert positions[0] == 0.0

    def test_class_a_axle_loads_array(self):
        """axle_loads property returns correct numpy array."""
        vehicle = get_class_a_train()
        loads = vehicle.axle_loads
        assert abs(loads.sum() - 554.0) < 0.1


class TestClassBLoading:
    """Tests for IRC Class B vehicle loading."""

    def test_class_b_total_load(self):
        """Class B train total load: 2*16 + 2*68 + 4*41 = 332 kN."""
        vehicle = get_class_b_train()
        expected = 2 * 16 + 2 * 68 + 4 * 41
        assert abs(vehicle.total_load - expected) < 0.1

    def test_class_b_is_lighter_than_class_a(self):
        """Class B should be lighter than Class A."""
        a = get_class_a_train()
        b = get_class_b_train()
        assert b.total_load < a.total_load


class TestClass70RLoading:
    """Tests for IRC Class 70R vehicle loading."""

    def test_70r_wheeled_total_load(self):
        """70R wheeled total load approximately 1000 kN."""
        vehicle = get_class_70r_wheeled()
        # 2*80 + 5*170 = 160 + 850 = 1010 kN (approximate)
        assert 950 < vehicle.total_load < 1050

    def test_70r_wheeled_axle_count(self):
        """70R wheeled has 7 axles."""
        vehicle = get_class_70r_wheeled()
        assert len(vehicle.axles) == 7

    def test_70r_wheeled_length(self):
        """70R wheeled vehicle length is 15.22m."""
        vehicle = get_class_70r_wheeled()
        assert abs(vehicle.total_length - 15.22) < 0.1

    def test_70r_wheeled_min_spacing(self):
        """70R vehicles need 30m minimum spacing."""
        vehicle = get_class_70r_wheeled()
        assert vehicle.min_spacing_same_lane == 30.0

    def test_70r_tracked_total_load(self):
        """70R tracked total load is 700 kN (one track = 350 kN)."""
        vehicle = get_class_70r_tracked()
        # Modeled as 5 point loads of 70 kN each = 350 kN
        assert abs(vehicle.total_load - 350.0) < 1.0

    def test_70r_tracked_equivalent_points(self):
        """70R tracked modeled as 5 equivalent point loads."""
        vehicle = get_class_70r_tracked()
        assert len(vehicle.axles) == 5

    def test_70r_bogie_total_load(self):
        """70R bogie total load is 400 kN."""
        vehicle = get_class_70r_bogie()
        assert abs(vehicle.total_load - 400.0) < 0.1

    def test_70r_bogie_axle_count(self):
        """70R bogie has 2 axles."""
        vehicle = get_class_70r_bogie()
        assert len(vehicle.axles) == 2


class TestClassAALoading:
    """Tests for IRC Class AA loading."""

    def test_aa_tracked_total_load(self):
        """AA tracked total is 350 kN (one track)."""
        vehicle = get_class_aa_tracked()
        assert abs(vehicle.total_load - 350.0) < 1.0

    def test_aa_wheeled_total_load(self):
        """AA wheeled total is ~400 kN (approx)."""
        vehicle = get_class_aa_wheeled()
        # 2*62.5 + 2*125 = 125 + 250 = 375 kN
        assert abs(vehicle.total_load - 375.0) < 1.0


class TestImpactFactor:
    """Tests for impact factor calculations."""

    def test_impact_factor_class_a_steel_short_span(self):
        """Impact factor for Class A on 10m steel span."""
        # I = 9/(13.5 + 10) = 9/23.5 ≈ 0.383
        impact = get_impact_factor("steel", 10.0, VehicleType.CLASS_A)
        expected = 1.0 + 9.0 / 23.5
        assert abs(impact - expected) < 0.01

    def test_impact_factor_class_a_concrete(self):
        """Impact factor for Class A on 20m concrete bridge."""
        # I = 4.5/(6 + 20) = 4.5/26 ≈ 0.173
        impact = get_impact_factor("concrete", 20.0, VehicleType.CLASS_A)
        expected = 1.0 + 4.5 / 26.0
        assert abs(impact - expected) < 0.01

    def test_impact_factor_class_a_steel_long_span(self):
        """Impact factor for Class A on 60m steel span."""
        impact = get_impact_factor("steel", 60.0, VehicleType.CLASS_A)
        expected = 1.0 + 9.0 / (13.5 + 60.0)
        assert abs(impact - expected) < 0.01

    def test_impact_factor_70r_short_span(self):
        """Impact factor for 70R on span <= 9m is 25%."""
        impact = get_impact_factor("steel", 8.0, VehicleType.CLASS_70R_WHEELED)
        assert abs(impact - 1.25) < 0.01

    def test_impact_factor_70r_tracked_short(self):
        """Impact factor for 70R tracked <= 9m is 25%."""
        impact = get_impact_factor("steel", 5.0, VehicleType.CLASS_70R_TRACKED)
        assert abs(impact - 1.25) < 0.01

    def test_impact_factor_70r_long_span(self):
        """Impact factor for 70R at 45m should be 10%."""
        impact = get_impact_factor("steel", 45.0, VehicleType.CLASS_70R_WHEELED)
        assert abs(impact - 1.10) < 0.01

    def test_impact_factor_minimum(self):
        """Impact factor should not be less than 10%."""
        # For very long spans, formula gives small values
        impact = get_impact_factor("steel", 100.0, VehicleType.CLASS_70R_WHEELED)
        assert impact >= 1.10

    def test_impact_factor_composite(self):
        """Impact factor for composite bridge (average of steel and concrete)."""
        impact = get_impact_factor("composite", 20.0, VehicleType.CLASS_A)
        steel_val = 9.0 / (13.5 + 20.0)
        concrete_val = 4.5 / (6.0 + 20.0)
        expected = 1.0 + (steel_val + concrete_val) / 2
        assert abs(impact - expected) < 0.01


class TestLaneDistribution:
    """Tests for lane reduction factors."""

    def test_single_lane(self):
        assert get_lane_distribution_factor(1) == 1.0

    def test_two_lanes(self):
        assert get_lane_distribution_factor(2) == 1.0

    def test_three_lanes(self):
        assert get_lane_distribution_factor(3) == 0.9

    def test_four_lanes(self):
        assert get_lane_distribution_factor(4) == 0.75

    def test_more_than_four(self):
        assert get_lane_distribution_factor(6) == 0.75


class TestCongestionFactor:
    """Tests for congestion factor."""

    def test_short_span(self):
        assert get_congestion_factor(5.0) == 1.0

    def test_medium_span(self):
        factor = get_congestion_factor(25.0)
        assert 1.0 < factor < 1.15

    def test_long_span(self):
        assert get_congestion_factor(50.0) == 1.15


class TestConvenienceFunctions:
    """Tests for convenience / utility functions."""

    def test_get_all_vehicle_types_count(self):
        """Should return all 7 vehicle types."""
        vehicles = get_all_vehicle_types()
        assert len(vehicles) == 7

    def test_get_all_vehicle_types_keys(self):
        """Should contain expected keys."""
        vehicles = get_all_vehicle_types()
        assert "class_a" in vehicles
        assert "class_70r_wheeled" in vehicles
        assert "class_70r_tracked" in vehicles

    def test_get_vehicle_loads_legacy(self):
        """Legacy function returns a non-empty list."""
        loads = get_vehicle_loads()
        assert len(loads) > 0
        assert all(isinstance(v, VehicleLoad) for v in loads)

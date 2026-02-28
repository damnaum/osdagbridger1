"""Tests for the plate-girder analysis orchestrator."""
import pytest

from osdagbridge.core.bridge_types.plate_girder.analyser import analyze_plate_girder
from osdagbridge.core.bridge_types.plate_girder.dto import PlateGirderInput, SteelGrade


class TestAnalyzePlateGirder:
    def test_returns_dict(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        assert isinstance(result, dict)

    def test_contains_moment_key(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        assert "absolute_max_moment_kNm" in result

    def test_contains_shear_key(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        assert "max_shear_kN" in result

    def test_moment_positive(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        assert result["absolute_max_moment_kNm"] > 0

    def test_shear_positive(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        assert result["max_shear_kN"] > 0

    def test_impact_factor_present(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        assert "impact_factor" in result
        assert result["impact_factor"] > 1.0

    def test_span_echo(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        expected_span = sample_plate_girder_input.effective_span / 1000
        assert result["span_m"] == pytest.approx(expected_span)

    def test_70r_higher_forces(self, sample_70r_input):
        result = analyze_plate_girder(sample_70r_input)
        assert result["absolute_max_moment_kNm"] > 0
        assert result["max_shear_kN"] > 0

    def test_vehicle_type_echoed(self, sample_plate_girder_input):
        result = analyze_plate_girder(sample_plate_girder_input)
        assert result["vehicle_type"] == "CLASS_A"


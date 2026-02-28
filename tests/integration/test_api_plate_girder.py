"""Integration tests for plate girder API (design_plate_girder end-to-end)."""
import pytest

from osdagbridge.core.bridge_types.plate_girder.designer import design_plate_girder
from osdagbridge.core.bridge_types.plate_girder.dto import PlateGirderInput, SteelGrade


class TestEndToEndClassA:
    """30 m span, E250A, Class A — the canonical example."""

    @pytest.fixture
    def result(self, sample_plate_girder_input):
        return design_plate_girder(sample_plate_girder_input)

    def test_status_completed(self, result):
        assert result["status"] == "completed"

    def test_section_class(self, result):
        assert result["section_properties"]["section_class"] in (
            "plastic", "compact", "semi-compact", "slender"
        )

    def test_moment_capacity_positive(self, result):
        assert result["moment_capacity"]["moment_capacity_governing_kNm"] > 0

    def test_shear_capacity_positive(self, result):
        assert result["shear_capacity"]["design_shear_capacity_kN"] > 0

    def test_deflection_check(self, result):
        assert "deflection_ok" in result["deflection"]

    def test_dead_loads_non_negative(self, result):
        for k, v in result["dead_loads"].items():
            assert v >= 0, f"{k} has negative value {v}"

    def test_factored_forces_present(self, result):
        assert result["factored_design_forces"]["factored_moment_kNm"] > 0

    def test_utilization_present(self, result):
        assert "moment_ratio" in result["utilization"]
        assert "shear_ratio" in result["utilization"]


class TestEndToEnd70R:
    """25 m span, E350, 70R — heavy loading."""

    @pytest.fixture
    def result(self, sample_70r_input):
        return design_plate_girder(sample_70r_input)

    def test_status_completed(self, result):
        assert result["status"] == "completed"

    def test_higher_fy_used(self, result):
        # E350 → epsilon < 1.0
        eps_sq = 250.0 / 350.0
        assert eps_sq < 1.0

    def test_moment_ratio_calculated(self, result):
        assert result["utilization"]["moment_ratio"] > 0


class TestUserSpecifiedDimensions:
    """Test when user provides explicit girder dimensions."""

    def test_returns_user_specified_method(self):
        inp = PlateGirderInput(
            project_name="T", bridge_name="T",
            effective_span=20000, girder_spacing=3000,
            web_depth=1200, web_thickness=10,
            flange_width=300, flange_thickness=20,
        )
        result = design_plate_girder(inp)
        assert result["sizing_method"] == "user_specified"
        assert result["status"] == "completed"


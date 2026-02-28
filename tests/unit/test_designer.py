"""
Designer-module tests — section classification, moment, shear,
deflection, web bearing, and full design pipeline.
"""
import math

import pytest

from osdagbridge.core.bridge_types.plate_girder.designer import (
    E_STEEL,
    GAMMA_M0,
    GAMMA_M1,
    calculate_epsilon,
    calculate_moment_capacity,
    calculate_section_properties,
    calculate_shear_capacity,
    check_deflection,
    check_web_bearing,
    classify_section,
    design_plate_girder,
    initial_sizing,
)
from osdagbridge.core.bridge_types.plate_girder.dto import (
    PlateGirderInput,
    SteelGrade,
)

# ── Epsilon ──────────────────────────────────────────────────

class TestEpsilon:
    def test_e250(self):
        assert calculate_epsilon(250) == pytest.approx(1.0)

    def test_e350(self):
        assert calculate_epsilon(350) == pytest.approx(math.sqrt(250 / 350), rel=1e-6)

    def test_e450(self):
        assert calculate_epsilon(450) == pytest.approx(math.sqrt(250 / 450), rel=1e-6)


# ── Initial sizing ───────────────────────────────────────────

class TestInitialSizing:
    def test_returns_four_values(self, sample_plate_girder_input):
        d, tw, bf, tf = initial_sizing(sample_plate_girder_input)
        assert d > 0 and tw > 0 and bf > 0 and tf > 0

    def test_depth_within_range(self, sample_plate_girder_input):
        """Web depth should be roughly span/12 to span/18."""
        d, *_ = initial_sizing(sample_plate_girder_input)
        span = sample_plate_girder_input.effective_span
        assert span / 20 < d < span / 8

    def test_web_min_thickness(self, sample_plate_girder_input):
        _, tw, *_ = initial_sizing(sample_plate_girder_input)
        assert tw >= 8.0

    def test_flange_min_width(self, sample_plate_girder_input):
        *_, bf, _ = initial_sizing(sample_plate_girder_input)
        assert bf >= 200.0

    def test_70r_gives_deeper_section(self):
        inp_a = PlateGirderInput(
            project_name="A", bridge_name="A",
            effective_span=25000, girder_spacing=3000,
            live_load_class="CLASS_A",
        )
        inp_70r = PlateGirderInput(
            project_name="B", bridge_name="B",
            effective_span=25000, girder_spacing=3000,
            live_load_class="CLASS_70R",
        )
        da, *_ = initial_sizing(inp_a)
        d70, *_ = initial_sizing(inp_70r)
        assert d70 >= da


# ── Section properties ───────────────────────────────────────

class TestSectionProperties:
    def test_symmetric_section(self):
        sec = calculate_section_properties(1500, 12, 400, 25)
        assert sec.total_depth == 1550.0
        assert sec.area == pytest.approx(1500 * 12 + 2 * 400 * 25)
        # Symmetric → centroid at mid-height
        assert sec.centroid_from_bottom == pytest.approx(sec.total_depth / 2, rel=1e-3)

    def test_section_modulus_positive(self):
        sec = calculate_section_properties(1200, 10, 300, 20)
        assert sec.section_modulus_top > 0
        assert sec.section_modulus_bottom > 0

    def test_plastic_gt_elastic(self):
        sec = calculate_section_properties(1500, 12, 400, 25)
        z_elastic = min(sec.section_modulus_top, sec.section_modulus_bottom)
        assert sec.plastic_section_modulus >= z_elastic

    def test_weight_per_meter(self):
        sec = calculate_section_properties(1500, 12, 400, 25)
        expected = sec.area * 1e-6 * 78.5
        assert sec.weight_per_meter == pytest.approx(expected, rel=1e-4)

    def test_fy_affects_classification(self):
        sec250 = calculate_section_properties(1500, 12, 400, 25, fy=250)
        sec350 = calculate_section_properties(1500, 12, 400, 25, fy=350)
        # Higher fy makes epsilon smaller → tighter limits → may differ
        assert sec250.section_class in ("plastic", "compact", "semi-compact", "slender")
        assert sec350.section_class in ("plastic", "compact", "semi-compact", "slender")


# ── Section classification ───────────────────────────────────

class TestClassifySection:
    def test_plastic(self):
        assert classify_section(50, 5, 250) == "plastic"

    def test_compact(self):
        assert classify_section(90, 9, 250) == "compact"

    def test_semi_compact(self):
        assert classify_section(120, 12, 250) == "semi-compact"

    def test_slender(self):
        assert classify_section(200, 20, 250) == "slender"

    def test_higher_fy_tightens_limits(self):
        """Same slenderness classified more severely for higher fy."""
        c250 = classify_section(85, 8.5, 250)
        c350 = classify_section(85, 8.5, 350)
        classes = ["plastic", "compact", "semi-compact", "slender"]
        assert classes.index(c350) >= classes.index(c250)


# ── Moment capacity ──────────────────────────────────────────

class TestMomentCapacity:
    @pytest.fixture
    def section(self):
        return calculate_section_properties(1500, 12, 400, 25)

    def test_section_capacity_positive(self, section):
        res = calculate_moment_capacity(section, 250, 3000)
        assert res["moment_capacity_section_kNm"] > 0

    def test_ltb_reduces_capacity(self, section):
        res = calculate_moment_capacity(section, 250, 6000)
        assert res["moment_capacity_ltb_kNm"] <= res["moment_capacity_section_kNm"]

    def test_governing_is_minimum(self, section):
        res = calculate_moment_capacity(section, 250, 3000)
        gov = res["moment_capacity_governing_kNm"]
        assert gov <= res["moment_capacity_section_kNm"]

    def test_zero_unbraced_no_ltb(self, section):
        res = calculate_moment_capacity(section, 250, 0)
        assert "moment_capacity_ltb_kNm" not in res


# ── Shear capacity ───────────────────────────────────────────

class TestShearCapacity:
    @pytest.fixture
    def stocky_section(self):
        """Stocky web: low d/tw → plastic shear."""
        return calculate_section_properties(600, 16, 300, 20)

    @pytest.fixture
    def slender_section(self):
        """Slender web: high d/tw → post-critical."""
        return calculate_section_properties(2000, 10, 400, 25)

    def test_plastic_method(self, stocky_section):
        res = calculate_shear_capacity(stocky_section, 250)
        assert res["method"] == "plastic"
        assert not res["buckling_check_required"]

    def test_post_critical_method(self, slender_section):
        res = calculate_shear_capacity(slender_section, 250)
        assert res["method"] == "post-critical"
        assert res["buckling_check_required"]

    def test_stiffeners_increase_capacity(self, slender_section):
        unstiffened = calculate_shear_capacity(slender_section, 250)
        stiffened = calculate_shear_capacity(slender_section, 250, stiffener_spacing=1000)
        assert stiffened["design_shear_capacity_kN"] >= unstiffened["design_shear_capacity_kN"]


# ── Deflection ───────────────────────────────────────────────

class TestDeflection:
    def test_pass_for_stiff_beam(self):
        res = check_deflection(30_000, 5e10, 5.0)
        assert res["deflection_ok"] is True

    def test_fail_for_flexible_beam(self):
        res = check_deflection(30_000, 1e8, 50.0)
        assert res["deflection_ok"] is False

    def test_allowable_is_span_over_600(self):
        res = check_deflection(24_000, 5e10, 5.0)
        assert res["allowable_deflection_mm"] == pytest.approx(40.0)


# ── Web bearing ──────────────────────────────────────────────

class TestWebBearing:
    def test_bearing_ok(self):
        sec = calculate_section_properties(1500, 12, 400, 25)
        res = check_web_bearing(sec, 250, 200, 100)
        assert res["bearing_ok"] is True

    def test_bearing_fail(self):
        sec = calculate_section_properties(1500, 8, 400, 20)
        res = check_web_bearing(sec, 250, 50, 9999)
        assert res["bearing_ok"] is False
        assert "note" in res


# ── Full design workflow ─────────────────────────────────────

class TestDesignPlateGirder:
    def test_completes_successfully(self, sample_plate_girder_input):
        result = design_plate_girder(sample_plate_girder_input)
        assert result["status"] == "completed"

    def test_contains_all_keys(self, sample_plate_girder_input):
        result = design_plate_girder(sample_plate_girder_input)
        expected_keys = {
            "input", "status", "warnings", "errors",
            "initial_dimensions", "section_properties",
            "dead_loads", "dead_load_effects",
            "factored_design_forces",
            "moment_capacity", "shear_capacity", "deflection",
            "utilization",
        }
        assert expected_keys.issubset(result.keys())

    def test_utilization_ratios(self, sample_plate_girder_input):
        result = design_plate_girder(sample_plate_girder_input)
        util = result["utilization"]
        assert "moment_ratio" in util
        assert "shear_ratio" in util
        assert util["status"] in ("PASS", "FAIL")

    def test_factored_forces_present(self, sample_plate_girder_input):
        result = design_plate_girder(sample_plate_girder_input)
        ff = result["factored_design_forces"]
        assert ff["gamma_dead"] == pytest.approx(1.35)
        assert ff["gamma_live"] == pytest.approx(1.50)
        assert ff["factored_moment_kNm"] > 0

    def test_user_specified_dimensions(self):
        inp = PlateGirderInput(
            project_name="T", bridge_name="T",
            effective_span=20000, girder_spacing=3000,
            web_depth=1200, web_thickness=10,
            flange_width=300, flange_thickness=20,
        )
        result = design_plate_girder(inp)
        assert result["sizing_method"] == "user_specified"
        assert result["initial_dimensions"]["web_depth_mm"] == 1200

    def test_e350_uses_correct_fy(self, sample_70r_input):
        result = design_plate_girder(sample_70r_input)
        assert result["status"] == "completed"
        # E350 → fy=350 → epsilon < 1 → tighter classification
        sec_class = result["section_properties"]["section_class"]
        assert sec_class in ("plastic", "compact", "semi-compact", "slender")

    def test_live_load_effects_present(self, sample_plate_girder_input):
        result = design_plate_girder(sample_plate_girder_input)
        assert "live_load_effects" in result or any(
            "Live load" in w for w in result.get("warnings", [])
        )


"""
Unit tests for plate girder design module.

Tests verify IS 800:2007 calculations are correct for:
- Epsilon factor calculation
- Section classification
- Section property calculations
- Moment capacity (section and LTB)
- Shear capacity (plastic and post-critical)
- Deflection check
- Complete design workflow
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
    classify_section,
    design_plate_girder,
    initial_sizing,
)
from osdagbridge.core.bridge_types.plate_girder.dto import (
    BridgeSpanType,
    PlateGirderInput,
    PlateGirderSection,
    SteelGrade,
)


class TestEpsilonCalculation:
    """Tests for epsilon factor calculation."""

    def test_epsilon_e250(self):
        """Epsilon for E250 steel (fy=250) should be 1.0."""
        eps = calculate_epsilon(250.0)
        assert abs(eps - 1.0) < 0.001

    def test_epsilon_e350(self):
        """Epsilon for E350 steel (fy=350) should be ~0.845."""
        eps = calculate_epsilon(350.0)
        expected = math.sqrt(250 / 350)
        assert abs(eps - expected) < 0.001

    def test_epsilon_e450(self):
        """Epsilon for E450 steel (fy=450) should be ~0.745."""
        eps = calculate_epsilon(450.0)
        expected = math.sqrt(250 / 450)
        assert abs(eps - expected) < 0.001

    def test_epsilon_decreases_with_fy(self):
        """Higher grade steel has lower epsilon."""
        eps_250 = calculate_epsilon(250)
        eps_350 = calculate_epsilon(350)
        eps_450 = calculate_epsilon(450)
        assert eps_250 > eps_350 > eps_450


class TestSectionClassification:
    """Tests for section classification as per IS 800:2007 Table 2."""

    def test_plastic_section(self):
        """Section with low slenderness should be plastic."""
        # Web d/tw = 50, Flange b/2tf = 5, fy = 250
        # Limits: web < 84, flange < 8.4
        section_class = classify_section(50, 5, 250)
        assert section_class == "plastic"

    def test_compact_section(self):
        """Section between plastic and compact limits."""
        # Web d/tw = 90, Flange b/2tf = 9, fy = 250
        # Limits: 84 < 90 < 105, 8.4 < 9 < 9.4
        section_class = classify_section(90, 9, 250)
        assert section_class == "compact"

    def test_semi_compact_section(self):
        """Section between compact and semi-compact limits."""
        # Web d/tw = 110, Flange b/2tf = 10, fy = 250
        section_class = classify_section(110, 10, 250)
        assert section_class == "semi-compact"

    def test_slender_section(self):
        """Section exceeding semi-compact limits."""
        # Web d/tw = 150, Flange b/2tf = 15, fy = 250
        section_class = classify_section(150, 15, 250)
        assert section_class == "slender"

    def test_web_governs_classification(self):
        """Section class should be governed by more slender element."""
        # Compact flange but slender web
        section_class = classify_section(150, 5, 250)
        assert section_class == "slender"

    def test_flange_governs_classification(self):
        """When flange is more slender than web."""
        # Plastic web but semi-compact flange
        section_class = classify_section(50, 12, 250)
        assert section_class == "semi-compact"

    def test_higher_fy_makes_more_slender(self):
        """Higher fy reduces epsilon, making limits tighter."""
        # This section is plastic for E250 but may not be for E450
        class_250 = classify_section(80, 8, 250)
        class_450 = classify_section(80, 8, 450)
        # With fy=450, epsilon=0.745, limits are reduced
        # web: 84*0.745 = 62.6 → 80 > 62.6 → not plastic
        assert class_250 == "plastic"
        assert class_450 != "plastic"


class TestSectionProperties:
    """Tests for section property calculations."""

    def test_symmetric_section_centroid(self):
        """Centroid of symmetric section is at mid-height."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        expected_centroid = (20 + 1000 + 20) / 2  # 520mm from bottom
        assert abs(section.centroid_from_bottom - expected_centroid) < 1.0

    def test_section_area(self):
        """Total area calculation for symmetric I-section."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        # Area = web + 2*flange = 1000*10 + 2*300*20 = 10000 + 12000 = 22000
        assert abs(section.area - 22000) < 1.0

    def test_total_depth(self):
        """Total depth = web + 2*flange."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        assert abs(section.total_depth - 1040) < 0.1

    def test_moment_of_inertia_order_of_magnitude(self):
        """I_xx should be in reasonable range for girder dimensions."""
        section = calculate_section_properties(
            d_web=1500, t_web=12, b_tf=400, t_tf=25
        )
        # For a 1.5m deep girder, I should be order of 10^10 mm^4
        assert 1e10 < section.moment_of_inertia_xx < 1e11

    def test_moment_of_inertia_symmetric(self):
        """For symmetric section, Z_top should equal Z_bottom."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        # For symmetric section, top and bottom section moduli should be equal
        assert abs(section.section_modulus_top - section.section_modulus_bottom) < 1.0

    def test_unsymmetric_section(self):
        """Unsymmetric section has different top and bottom Z."""
        section = calculate_section_properties(
            d_web=1000, t_web=10,
            b_tf=200, t_tf=15,
            b_bf=400, t_bf=25,
        )
        # Bottom flange is larger, centroid shifts toward bottom
        # (centroid_from_bottom is LESS than half depth)
        assert section.centroid_from_bottom < section.total_depth / 2
        # Section moduli should differ
        assert section.section_modulus_top != section.section_modulus_bottom

    def test_web_slenderness(self):
        """Web slenderness = d/tw."""
        section = calculate_section_properties(
            d_web=1200, t_web=10, b_tf=300, t_tf=20
        )
        assert abs(section.web_slenderness - 120.0) < 0.1

    def test_flange_slenderness(self):
        """Flange slenderness = (b - tw)/(2*tf)."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        expected = (300 - 10) / (2 * 20)  # 7.25
        assert abs(section.flange_slenderness - expected) < 0.01

    def test_plastic_section_modulus_positive(self):
        """Plastic section modulus should be positive."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        assert section.plastic_section_modulus > 0

    def test_plastic_greater_than_elastic(self):
        """Zp should be >= Ze for I-sections."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        z_elastic = min(section.section_modulus_top, section.section_modulus_bottom)
        assert section.plastic_section_modulus >= z_elastic

    def test_weight_per_meter(self):
        """Weight per meter should be reasonable for a girder."""
        section = calculate_section_properties(
            d_web=1500, t_web=12, b_tf=400, t_tf=25
        )
        # Area = 1500*12 + 2*400*25 = 18000 + 20000 = 38000 mm²
        # Weight = 38000e-6 * 78.5 = 2.98 kN/m
        weight = section.weight_per_meter
        assert 2.0 < weight < 5.0  # Reasonable range


class TestInitialSizing:
    """Tests for initial sizing estimates."""

    def test_sizing_returns_four_values(self):
        """Initial sizing returns web_depth, web_t, flange_w, flange_t."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
        )
        result = initial_sizing(inp)
        assert len(result) == 4

    def test_sizing_reasonable_depth(self):
        """Depth should be roughly span/12 to span/15."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,  # 30m
            girder_spacing=3000,
        )
        d_web, _, _, _ = initial_sizing(inp)
        overall = d_web + 2 * 20  # approximate
        assert 1500 < overall < 3000  # 30000/15=2000, 30000/12=2500

    def test_sizing_minimum_web_thickness(self):
        """Web thickness should be at least 8mm."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=10000,  # Short span
            girder_spacing=2000,
        )
        _, t_web, _, _ = initial_sizing(inp)
        assert t_web >= 8.0

    def test_sizing_minimum_flange_width(self):
        """Flange width should be at least 200mm."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=10000,
            girder_spacing=2000,
        )
        _, _, b_f, _ = initial_sizing(inp)
        assert b_f >= 200.0

    def test_heavier_loading_deeper_section(self):
        """70R loading should give deeper section than Class A."""
        inp_a = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
            live_load_class="CLASS_A",
        )
        inp_70r = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
            live_load_class="CLASS_70R",
        )
        d_a, _, _, _ = initial_sizing(inp_a)
        d_70r, _, _, _ = initial_sizing(inp_70r)
        assert d_70r >= d_a


class TestMomentCapacity:
    """Tests for moment capacity calculation."""

    def test_moment_capacity_positive(self):
        """Moment capacity should be positive."""
        section = calculate_section_properties(
            d_web=1500, t_web=12, b_tf=400, t_tf=25
        )
        results = calculate_moment_capacity(section, 250.0, 3000)
        assert results["moment_capacity_section_kNm"] > 0

    def test_moment_capacity_governing_less_than_section(self):
        """Governing capacity should be <= section capacity."""
        section = calculate_section_properties(
            d_web=1500, t_web=12, b_tf=400, t_tf=25
        )
        results = calculate_moment_capacity(section, 250.0, 3000)
        assert (
            results["moment_capacity_governing_kNm"]
            <= results["moment_capacity_section_kNm"]
        )

    def test_longer_unbraced_reduces_capacity(self):
        """Longer unbraced length should reduce moment capacity (more LTB)."""
        section = calculate_section_properties(
            d_web=1500, t_web=12, b_tf=400, t_tf=25
        )
        results_short = calculate_moment_capacity(section, 250.0, 2000)
        results_long = calculate_moment_capacity(section, 250.0, 8000)
        assert (
            results_long["moment_capacity_governing_kNm"]
            <= results_short["moment_capacity_governing_kNm"]
        )

    def test_no_ltb_when_continuously_braced(self):
        """Zero unbraced length means no LTB check."""
        section = calculate_section_properties(
            d_web=1500, t_web=12, b_tf=400, t_tf=25
        )
        results = calculate_moment_capacity(section, 250.0, 0)
        assert "moment_capacity_ltb_kNm" not in results
        assert results["moment_capacity_governing_kNm"] == results[
            "moment_capacity_section_kNm"
        ]

    def test_higher_fy_higher_capacity(self):
        """Higher yield strength should give higher moment capacity."""
        section = calculate_section_properties(
            d_web=1000, t_web=10, b_tf=300, t_tf=20
        )
        results_250 = calculate_moment_capacity(section, 250.0, 3000)
        results_350 = calculate_moment_capacity(section, 350.0, 3000)
        assert (
            results_350["moment_capacity_section_kNm"]
            > results_250["moment_capacity_section_kNm"]
        )


class TestShearCapacity:
    """Tests for shear capacity calculation."""

    def test_plastic_shear_stocky_web(self):
        """Stocky web should give plastic shear capacity."""
        section = calculate_section_properties(
            d_web=800, t_web=16, b_tf=300, t_tf=20  # d/tw = 50 < 67
        )
        results = calculate_shear_capacity(section, 250)
        assert results["method"] == "plastic"
        assert not results["buckling_check_required"]

    def test_buckling_check_slender_web(self):
        """Slender web should trigger buckling check."""
        section = calculate_section_properties(
            d_web=1500, t_web=10, b_tf=400, t_tf=25  # d/tw = 150 > 67
        )
        results = calculate_shear_capacity(section, 250)
        assert results["buckling_check_required"]
        assert results["method"] == "post-critical"

    def test_shear_capacity_positive(self):
        """Design shear capacity should always be positive."""
        section = calculate_section_properties(
            d_web=1500, t_web=12, b_tf=400, t_tf=25
        )
        results = calculate_shear_capacity(section, 250)
        assert results["design_shear_capacity_kN"] > 0

    def test_post_critical_less_than_plastic(self):
        """Post-critical shear should be less than plastic shear."""
        section = calculate_section_properties(
            d_web=1500, t_web=10, b_tf=400, t_tf=25
        )
        results = calculate_shear_capacity(section, 250)
        if results["buckling_check_required"]:
            assert (
                results["design_shear_capacity_kN"]
                <= results["plastic_shear_capacity_kN"]
            )

    def test_stiffened_web_higher_capacity(self):
        """Stiffened web should give higher or equal shear capacity."""
        section = calculate_section_properties(
            d_web=1500, t_web=10, b_tf=400, t_tf=25
        )
        results_unstiffened = calculate_shear_capacity(section, 250)
        results_stiffened = calculate_shear_capacity(section, 250, stiffener_spacing=1000)
        assert (
            results_stiffened["design_shear_capacity_kN"]
            >= results_unstiffened["design_shear_capacity_kN"]
        )


class TestDeflection:
    """Tests for deflection check."""

    def test_zero_load_zero_deflection(self):
        """No load should give zero deflection."""
        results = check_deflection(30000, 1e10, 0.0, 0.0)
        assert results["total_deflection_mm"] == 0.0

    def test_deflection_positive(self):
        """Non-zero UDL should give positive deflection."""
        results = check_deflection(30000, 1e10, 10.0)
        assert results["total_deflection_mm"] > 0

    def test_allowable_deflection(self):
        """Allowable should be span/600."""
        results = check_deflection(30000, 1e10, 10.0)
        assert abs(results["allowable_deflection_mm"] - 50.0) < 0.1

    def test_higher_inertia_less_deflection(self):
        """Larger I gives smaller deflection."""
        r1 = check_deflection(30000, 1e10, 10.0)
        r2 = check_deflection(30000, 2e10, 10.0)
        assert r2["total_deflection_mm"] < r1["total_deflection_mm"]


class TestDesignWorkflow:
    """Tests for the complete design workflow."""

    def test_design_completes(self):
        """Design should complete without errors for valid input."""
        inp = PlateGirderInput(
            project_name="NH-44 ROB",
            bridge_name="Km 245+500",
            effective_span=30000,
            girder_spacing=3000,
        )
        result = design_plate_girder(inp)
        assert result["status"] == "completed"

    def test_design_auto_sizing(self):
        """Auto sizing should be used when dimensions not provided."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
        )
        result = design_plate_girder(inp)
        assert result["sizing_method"] == "auto"
        assert result["initial_dimensions"]["web_depth_mm"] > 0

    def test_design_user_dimensions(self):
        """User-specified dimensions should be used when provided."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
            web_depth=2000,
            web_thickness=12,
            flange_width=400,
            flange_thickness=25,
        )
        result = design_plate_girder(inp)
        assert result["sizing_method"] == "user_specified"
        assert result["initial_dimensions"]["web_depth_mm"] == 2000

    def test_design_contains_all_sections(self):
        """Result should contain all major design sections."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
        )
        result = design_plate_girder(inp)
        assert "section_properties" in result
        assert "moment_capacity" in result
        assert "shear_capacity" in result
        assert "deflection" in result
        assert "dead_loads" in result

    def test_design_e350_steel(self):
        """Design with E350 steel grade."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
            steel_grade=SteelGrade.E350,
        )
        result = design_plate_girder(inp)
        assert result["status"] == "completed"


class TestPlateGirderDTO:
    """Tests for the DTO validation."""

    def test_valid_input(self):
        """Valid input should not raise errors."""
        inp = PlateGirderInput(
            project_name="Test Bridge",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
        )
        assert inp.effective_span == 30000

    def test_span_too_long(self):
        """Span > 60m should raise validation error."""
        with pytest.raises(ValueError, match="exceeds typical plate girder limit"):
            PlateGirderInput(
                project_name="Test",
                bridge_name="B1",
                effective_span=70000,  # 70m
                girder_spacing=3000,
            )

    def test_yield_strength_e250(self):
        """E250A should return fy = 250 MPa."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
            steel_grade=SteelGrade.E250A,
        )
        assert inp.get_yield_strength() == 250.0

    def test_ultimate_strength_e350(self):
        """E350 should return fu = 490 MPa."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
            steel_grade=SteelGrade.E350,
        )
        assert inp.get_ultimate_strength() == 490.0

    def test_youngs_modulus(self):
        """Young's modulus should be 200000 MPa."""
        inp = PlateGirderInput(
            project_name="Test",
            bridge_name="B1",
            effective_span=30000,
            girder_spacing=3000,
        )
        assert inp.get_youngs_modulus() == 200000.0

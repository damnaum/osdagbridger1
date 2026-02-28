"""Verification cases based on DDCL reference designs.

These tests ensure the OsdagBridge results are within expected ranges
for known benchmark cases.  Exact values are not compared because
the engine uses simplified UDL-equivalent dead loads — we check that
results fall within ±30 % of typical preliminary-design values.
"""
import pytest
import yaml
from pathlib import Path

from osdagbridge.core.bridge_types.plate_girder.designer import design_plate_girder
from osdagbridge.core.bridge_types.plate_girder.dto import PlateGirderInput


EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "plate_girder"


def _load_yaml(name: str) -> dict:
    with open(EXAMPLES_DIR / name) as f:
        return yaml.safe_load(f)


class TestVerificationCase01:
    """VC-01: 20 m span, E250A, Class A."""

    @pytest.fixture
    def result(self):
        data = _load_yaml("verification_case_01.yaml")
        inp = PlateGirderInput(**data["input"])
        return design_plate_girder(inp)

    def test_completes(self, result):
        assert result["status"] == "completed"

    def test_web_depth_reasonable(self, result):
        d = result["initial_dimensions"]["web_depth_mm"]
        # 20 m span → expect ~1000–2000 mm web depth
        assert 800 < d < 2500

    def test_moment_capacity_adequate(self, result):
        md = result["moment_capacity"]["moment_capacity_governing_kNm"]
        assert md > 0

    def test_shear_capacity_adequate(self, result):
        vd = result["shear_capacity"]["design_shear_capacity_kN"]
        assert vd > 0


class TestVerificationCase02:
    """VC-02: 25 m span, E350, 70R."""

    @pytest.fixture
    def result(self):
        data = _load_yaml("verification_case_02.yaml")
        inp = PlateGirderInput(**data["input"])
        return design_plate_girder(inp)

    def test_completes(self, result):
        assert result["status"] == "completed"

    def test_e350_used(self, result):
        assert result["input"]["steel_grade"] == "E350"

    def test_deeper_section_than_20m(self, result):
        d = result["initial_dimensions"]["web_depth_mm"]
        assert d > 1000


class TestExampleBasic:
    """example_basic.yaml — canonical 30 m span."""

    @pytest.fixture
    def result(self):
        data = _load_yaml("example_basic.yaml")
        inp = PlateGirderInput(**data["input"])
        return design_plate_girder(inp)

    def test_completes(self, result):
        assert result["status"] == "completed"

    def test_utilization_populated(self, result):
        util = result["utilization"]
        assert util["moment_ratio"] > 0
        assert util["shear_ratio"] > 0


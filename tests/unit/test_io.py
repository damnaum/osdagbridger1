"""Unit tests for YAML I/O and DTO validation.

Tests that PlateGirderInput correctly validates inputs
and that YAML round-tripping works.
"""
import pytest
import yaml
from pathlib import Path

from osdagbridge.core.bridge_types.plate_girder.dto import (
    PlateGirderInput,
    SteelGrade,
    BridgeSpanType,
)


class TestPlateGirderInputValidation:
    def test_minimal_valid_input(self):
        inp = PlateGirderInput(
            project_name="P", bridge_name="B",
            effective_span=20000, girder_spacing=3000,
        )
        assert inp.effective_span == 20000

    def test_rejects_zero_span(self):
        with pytest.raises(Exception):
            PlateGirderInput(
                project_name="P", bridge_name="B",
                effective_span=0, girder_spacing=3000,
            )

    def test_rejects_negative_span(self):
        with pytest.raises(Exception):
            PlateGirderInput(
                project_name="P", bridge_name="B",
                effective_span=-5000, girder_spacing=3000,
            )

    def test_rejects_span_over_max(self):
        with pytest.raises(Exception):
            PlateGirderInput(
                project_name="P", bridge_name="B",
                effective_span=200_000, girder_spacing=3000,
            )

    def test_steel_grade_enum(self):
        inp = PlateGirderInput(
            project_name="P", bridge_name="B",
            effective_span=20000, girder_spacing=3000,
            steel_grade="E350",
        )
        assert inp.steel_grade == SteelGrade.E350

    def test_yield_strength_lookup(self):
        inp = PlateGirderInput(
            project_name="P", bridge_name="B",
            effective_span=20000, girder_spacing=3000,
            steel_grade="E350",
        )
        assert inp.get_yield_strength() == 350.0

    def test_ultimate_strength_lookup(self):
        inp = PlateGirderInput(
            project_name="P", bridge_name="B",
            effective_span=20000, girder_spacing=3000,
            steel_grade="E350",
        )
        assert inp.get_ultimate_strength() == 490.0

    def test_youngs_modulus(self):
        inp = PlateGirderInput(
            project_name="P", bridge_name="B",
            effective_span=20000, girder_spacing=3000,
        )
        assert inp.get_youngs_modulus() == 200_000.0


class TestYamlRoundTrip:
    def test_load_example_yaml(self):
        """Ensure example YAML files can be loaded into the DTO."""
        example_path = (
            Path(__file__).resolve().parents[2]
            / "examples" / "plate_girder" / "example_basic.yaml"
        )
        if not example_path.exists():
            pytest.skip("Example YAML not found")
        with open(example_path) as f:
            data = yaml.safe_load(f)
        inp = PlateGirderInput(**data["input"])
        assert inp.effective_span == 30000

    def test_model_dump_roundtrip(self):
        inp = PlateGirderInput(
            project_name="P", bridge_name="B",
            effective_span=20000, girder_spacing=3000,
        )
        d = inp.model_dump()
        inp2 = PlateGirderInput(**d)
        assert inp2.effective_span == inp.effective_span


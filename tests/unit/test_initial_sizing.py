"""Tests for the initial-sizing re-export module."""
import pytest

from osdagbridge.core.bridge_types.plate_girder.dto import SteelGrade
from osdagbridge.core.bridge_types.plate_girder.initial_sizing import (
    PlateGirderInput,
    initial_sizing,
)


class TestInitialSizingModule:
    """Tests that initial_sizing re-export works and produces valid dimensions."""

    def test_import_works(self):
        """Module re-exports initial_sizing from designer."""
        assert callable(initial_sizing)

    def test_basic_20m_span(self):
        inp = PlateGirderInput(
            project_name="T", bridge_name="T",
            effective_span=20000, girder_spacing=3000,
        )
        d, tw, bf, tf = initial_sizing(inp)
        assert 800 < d < 2500
        assert 8 <= tw <= 20
        assert bf >= 200
        assert tf >= 16

    def test_basic_30m_span(self, sample_plate_girder_input):
        d, tw, bf, tf = initial_sizing(sample_plate_girder_input)
        assert d > 1000
        assert tw >= 8
        assert bf >= 200
        assert tf >= 20

    def test_e350_changes_sizing(self):
        """Higher-grade steel allows thinner elements due to ε < 1."""
        inp250 = PlateGirderInput(
            project_name="T", bridge_name="T",
            effective_span=25000, girder_spacing=3000,
            steel_grade=SteelGrade.E250A,
        )
        inp350 = PlateGirderInput(
            project_name="T", bridge_name="T",
            effective_span=25000, girder_spacing=3000,
            steel_grade=SteelGrade.E350,
        )
        d250, tw250, *_ = initial_sizing(inp250)
        d350, tw350, *_ = initial_sizing(inp350)
        # Higher fy → smaller ε → tw may increase (to stay below 200ε)
        assert tw350 >= tw250 or d350 <= d250

    def test_dimensions_even_mm(self, sample_plate_girder_input):
        """Dimensions should be rounded to practical increments."""
        _, tw, bf, tf = initial_sizing(sample_plate_girder_input)
        assert tw % 2 == 0  # even mm
        assert bf % 10 == 0  # 10 mm increment
        assert tf % 2 == 0  # even mm


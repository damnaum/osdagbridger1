"""Shared test fixtures for OsdagBridge test suite."""
import pytest

from osdagbridge.core.bridge_types.plate_girder.dto import PlateGirderInput, SteelGrade


@pytest.fixture
def sample_plate_girder_input():
    """Standard plate girder input for testing (30m span, Class A)."""
    return PlateGirderInput(
        project_name="Test Project",
        bridge_name="Test Bridge",
        effective_span=30000,
        girder_spacing=3000,
        num_girders=2,
        steel_grade=SteelGrade.E250A,
        live_load_class="CLASS_A",
    )


@pytest.fixture
def sample_70r_input():
    """Plate girder input with 70R loading for testing."""
    return PlateGirderInput(
        project_name="Test Project 70R",
        bridge_name="Test Bridge 70R",
        effective_span=25000,
        girder_spacing=3500,
        num_girders=3,
        steel_grade=SteelGrade.E350,
        live_load_class="CLASS_70R",
    )

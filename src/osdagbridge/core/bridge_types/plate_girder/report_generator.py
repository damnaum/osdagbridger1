"""Plate-girder-specific report generation (delegates to the shared generator)."""
from typing import Any, Dict

from ...reports.report_generator import generate_text_report


def generate_plate_girder_report(
    project_name: str,
    bridge_name: str,
    design_results: Dict[str, Any],
) -> str:
    """Produce a text report from ``design_plate_girder()`` output."""
    return generate_text_report(project_name, bridge_name, design_results)


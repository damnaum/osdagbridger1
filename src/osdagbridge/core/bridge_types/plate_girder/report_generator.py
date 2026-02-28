"""Report generator specific to plate girder design output."""
from typing import Any, Dict

from ...reports.report_generator import generate_text_report


def generate_plate_girder_report(
    project_name: str,
    bridge_name: str,
    design_results: Dict[str, Any],
) -> str:
    """Generate a formatted design report for plate girder bridge.

    Args:
        project_name: Project name
        bridge_name: Bridge name
        design_results: Output from design_plate_girder()

    Returns:
        Formatted report string
    """
    return generate_text_report(project_name, bridge_name, design_results)


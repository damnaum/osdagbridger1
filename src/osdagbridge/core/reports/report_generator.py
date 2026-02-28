"""Report generation for bridge design calculations.

Generates structured calculation reports in text format.
LaTeX/PDF generation requires the 'report' optional dependency.
"""
from typing import Dict, Any
from datetime import datetime


def generate_text_report(
    project_name: str,
    bridge_name: str,
    results: Dict[str, Any],
) -> str:
    """Generate a plain-text calculation report.

    Args:
        project_name: Name of the project
        bridge_name: Name of the bridge
        results: Dictionary of design results

    Returns:
        Formatted report string
    """
    lines = [
        "=" * 70,
        "OSDAGBRIDGE \u2014 DESIGN CALCULATION REPORT",
        "=" * 70,
        f"Project : {project_name}",
        f"Bridge  : {bridge_name}",
        f"Date    : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "-" * 70,
        "",
    ]

    for section_name, section_data in results.items():
        lines.append(f"## {section_name}")
        lines.append("-" * 40)
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                if isinstance(value, float):
                    lines.append(f"  {key:40s}: {value:>12.3f}")
                else:
                    lines.append(f"  {key:40s}: {value}")
        else:
            lines.append(f"  {section_data}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    return "\n".join(lines)


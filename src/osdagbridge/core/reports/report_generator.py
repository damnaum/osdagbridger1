"""Plain-text design report generation.

Keeps things basic intentionally — LaTeX / PDF output needs the
``report`` optional extra (pylatex).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def _format_value(value: object) -> str:
    """Format a single value for report display."""
    if isinstance(value, float):
        return f"{value:>12.3f}"
    return str(value)


def generate_text_report(
    project_name: str,
    bridge_name: str,
    results: Dict[str, Any],
) -> str:
    """Generate a plain-text calculation report.

    Args:
        project_name: Name of the project
        bridge_name: Name of the bridge
        results: Dictionary of design results from the designer

    Returns:
        Formatted report string
    """
    lines: List[str] = [
        "=" * 70,
        "OSDAGBRIDGE \u2014 DESIGN CALCULATION REPORT",
        "=" * 70,
        f"Project : {project_name}",
        f"Bridge  : {bridge_name}",
        f"Date    : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "-" * 70,
        "",
    ]

    # Sections to skip in the main loop (handled separately)
    skip_keys = {"input", "warnings", "errors"}

    for section_name, section_data in results.items():
        if section_name in skip_keys:
            continue
        lines.append(f"## {section_name}")
        lines.append("-" * 40)
        if isinstance(section_data, dict):
            for key, value in section_data.items():
                lines.append(f"  {key:40s}: {_format_value(value)}")
        elif isinstance(section_data, list):
            if section_data:
                for item in section_data:
                    lines.append(f"  - {item}")
            else:
                lines.append("  (none)")
        else:
            lines.append(f"  {_format_value(section_data)}")
        lines.append("")

    # Warnings
    warnings: List[str] = results.get("warnings", [])
    if warnings:
        lines.append("## WARNINGS")
        lines.append("-" * 40)
        for w in warnings:
            lines.append(f"  ! {w}")
        lines.append("")

    # Errors
    errors: List[str] = results.get("errors", [])
    if errors:
        lines.append("## ERRORS")
        lines.append("-" * 40)
        for e in errors:
            lines.append(f"  X {e}")
        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    return "\n".join(lines)


"""CLI command implementations."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import yaml

from osdagbridge.core.exceptions import OsdagError


def _load_yaml(input_file: str) -> dict:
    """Load and validate a YAML input file."""
    path = Path(input_file)
    if not path.exists():
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        print(f"Error: '{input_file}' does not contain a valid YAML mapping.", file=sys.stderr)
        sys.exit(1)
    return config


def _detect_bridge_type(config: dict) -> str:
    """Extract bridge type from config with a sensible default."""
    return config.get(
        "bridge_type", config.get("project", {}).get("type", "plate_girder")
    )


def _format_value(value: object) -> str:
    """Pretty-format a single result value for terminal output."""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def run_analysis(input_file: str, solver: str, output: Optional[str] = None) -> None:
    """Run analysis from a YAML input file."""
    config = _load_yaml(input_file)
    bridge_type = _detect_bridge_type(config)

    print(f"Running analysis on '{input_file}' with solver '{solver}'...")

    if bridge_type == "plate_girder":
        from osdagbridge.core.bridge_types.plate_girder.designer import (
            design_plate_girder,
        )
        from osdagbridge.core.bridge_types.plate_girder.dto import (
            PlateGirderInput,
        )

        try:
            inp = PlateGirderInput(**config.get("input", config))
            results = design_plate_girder(inp)
        except OsdagError as exc:
            print(f"Design error: {exc}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"Unexpected error: {exc}", file=sys.stderr)
            sys.exit(1)

        print("\n--- Analysis Results ---")
        for key, value in results.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {_format_value(v)}")
            elif isinstance(value, list):
                if value:
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
            else:
                print(f"  {key}: {_format_value(value)}")

        if output:
            Path(output).write_text(json.dumps(results, indent=2, default=str))
            print(f"\nResults saved to '{output}'")
    else:
        print(f"Bridge type '{bridge_type}' is not yet implemented.")
        sys.exit(1)


def run_report(input_file: str, output_file: str, fmt: str = "text") -> None:
    """Generate a design report from a YAML input file."""
    config = _load_yaml(input_file)
    bridge_type = _detect_bridge_type(config)

    if bridge_type == "plate_girder":
        from osdagbridge.core.bridge_types.plate_girder.designer import (
            design_plate_girder,
        )
        from osdagbridge.core.bridge_types.plate_girder.dto import PlateGirderInput
        from osdagbridge.core.reports.report_generator import generate_text_report

        try:
            inp = PlateGirderInput(**config.get("input", config))
            results = design_plate_girder(inp)
        except OsdagError as exc:
            print(f"Design error: {exc}", file=sys.stderr)
            sys.exit(1)

        if fmt == "text":
            report_text = generate_text_report(
                inp.project_name, inp.bridge_name, results
            )
            Path(output_file).write_text(report_text)
            print(f"Report written to '{output_file}'")
        else:
            print(f"Format '{fmt}' is not yet implemented. Use --format text.")
            sys.exit(1)
    else:
        print(f"Bridge type '{bridge_type}' is not yet supported.")
        sys.exit(1)


"""CLI command implementations."""
import sys
import yaml
from pathlib import Path


def run_analysis(input_file: str, solver: str, output: str = None):
    """Run analysis from a YAML input file."""
    path = Path(input_file)
    if not path.exists():
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        config = yaml.safe_load(f)

    print(f"Running analysis on '{input_file}' with solver '{solver}'...")

    # Detect bridge type and dispatch
    bridge_type = config.get(
        "bridge_type", config.get("project", {}).get("type", "plate_girder")
    )

    if bridge_type == "plate_girder":
        from osdagbridge.core.bridge_types.plate_girder.designer import (
            design_plate_girder,
        )
        from osdagbridge.core.bridge_types.plate_girder.dto import (
            PlateGirderInput,
        )

        inp = PlateGirderInput(**config.get("input", config))
        results = design_plate_girder(inp)

        print("\n--- Analysis Results ---")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            elif isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        if output:
            import json

            Path(output).write_text(json.dumps(results, indent=2, default=str))
            print(f"\nResults saved to '{output}'")
    else:
        print(f"Bridge type '{bridge_type}' is not yet implemented.")
        sys.exit(1)


def run_report(input_file: str, output_file: str, fmt: str = "text"):
    """Generate a design report from a YAML input file."""
    path = Path(input_file)
    if not path.exists():
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        config = yaml.safe_load(f)

    bridge_type = config.get(
        "bridge_type", config.get("project", {}).get("type", "plate_girder")
    )

    if bridge_type == "plate_girder":
        from osdagbridge.core.bridge_types.plate_girder.designer import (
            design_plate_girder,
        )
        from osdagbridge.core.bridge_types.plate_girder.dto import PlateGirderInput
        from osdagbridge.core.reports.report_generator import generate_text_report

        inp = PlateGirderInput(**config.get("input", config))
        results = design_plate_girder(inp)

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


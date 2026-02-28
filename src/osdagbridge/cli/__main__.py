"""CLI entrypoint for OsdagBridge."""
import argparse
import sys

from osdagbridge import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="osdagbridge",
        description="OsdagBridge \u2014 Steel Bridge Analysis & Design CLI",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Run structural analysis"
    )
    analyze_parser.add_argument("input_file", help="Path to YAML input file")
    analyze_parser.add_argument(
        "--solver",
        default="native",
        choices=["native", "opensees", "ospgrillage"],
    )
    analyze_parser.add_argument("--output", "-o", help="Output file path")

    # report command
    report_parser = subparsers.add_parser(
        "report", help="Generate design report"
    )
    report_parser.add_argument("input_file", help="Path to YAML input file")
    report_parser.add_argument("output_file", help="Output report file path")
    report_parser.add_argument(
        "--format", default="text", choices=["text", "latex"]
    )

    # info command
    subparsers.add_parser("info", help="Show software info and available modules")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "info":
        print(f"OsdagBridge v{__version__}")
        print("Modules: plate_girder, box_girder (stub), truss (stub)")
        print("Solvers: native, opensees (optional), ospgrillage (optional)")
        print("Codes  : IRC:6-2017, IRC:22-2015, IRC:24-2010, IS 800:2007")

    elif args.command == "analyze":
        from osdagbridge.cli.commands import run_analysis

        run_analysis(
            args.input_file, args.solver, getattr(args, "output", None)
        )

    elif args.command == "report":
        from osdagbridge.cli.commands import run_report

        run_report(args.input_file, args.output_file, args.format)


if __name__ == "__main__":
    main()


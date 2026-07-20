"""Command-line entry point for the sandbox demos."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jxops",
        description="Run sanitized operational demos for a fictional legacy MMO fleet.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    routes = subparsers.add_parser("routes", help="Validate and visualize map routes.")
    routes.add_argument("--demo", action="store_true", help="Run the built-in route demo.")
    routes.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/routes-demo.svg"),
        help="SVG output path (default: artifacts/routes-demo.svg).",
    )

    boot = subparsers.add_parser("boot", help="Run a headless boot simulation.")
    boot.add_argument("--mock", action="store_true", help="Use sanitized mock services.")

    incident = subparsers.add_parser("incident", help="Analyze an operational log.")
    incident.add_argument("--analyze", metavar="LOGFILE", help="Log file to analyze.")

    bots = subparsers.add_parser("bots", help="Run the bot population simulation.")
    bots.add_argument("--sim", action="store_true", help="Run the built-in simulation.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "routes":
        if not args.demo:
            parser.error("routes requires --demo")
        from jxops.routes import run_demo

        return run_demo(args.output)
    parser.error(f"The {args.command!r} capability has not been installed yet.")
    return 2

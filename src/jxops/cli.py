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
    boot.add_argument("--delay", type=float, default=0.08, help="Delay per boot stage.")

    incident = subparsers.add_parser("incident", help="Analyze an operational log.")
    incident.add_argument("--analyze", type=Path, metavar="LOGFILE", help="Log file to analyze.")
    incident.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/incident-report.md"),
        help="Markdown output path (default: artifacts/incident-report.md).",
    )

    bots = subparsers.add_parser("bots", help="Run the bot population simulation.")
    bots.add_argument("--sim", action="store_true", help="Run the built-in simulation.")
    bots.add_argument("--bots", type=int, default=12, help="Population size from 10 to 20.")
    bots.add_argument("--ticks", type=int, default=14, help="Number of simulation ticks.")
    bots.add_argument("--delay", type=float, default=0.12, help="Delay between animated ticks.")
    bots.add_argument(
        "--no-animate",
        action="store_true",
        help="Print frames without terminal cursor control.",
    )
    bots.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/bots-final.svg"),
        help="Final SVG path (default: artifacts/bots-final.svg).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "routes":
        if not args.demo:
            parser.error("routes requires --demo")
        from jxops.routes import run_demo

        return run_demo(args.output)
    if args.command == "boot":
        if not args.mock:
            parser.error("boot requires --mock")
        if args.delay < 0:
            parser.error("--delay cannot be negative")
        from jxops.boot import run_mock_boot

        return run_mock_boot(args.delay)
    if args.command == "incident":
        if args.analyze is None:
            parser.error("incident requires --analyze LOGFILE")
        from jxops.incident import run_analysis

        return run_analysis(args.analyze, args.output)
    if args.command == "bots":
        if not args.sim:
            parser.error("bots requires --sim")
        if not 10 <= args.bots <= 20:
            parser.error("--bots must be between 10 and 20")
        if args.ticks < 1:
            parser.error("--ticks must be positive")
        if args.delay < 0:
            parser.error("--delay cannot be negative")
        from jxops.bots import run_simulation

        return run_simulation(
            args.output,
            bot_count=args.bots,
            ticks=args.ticks,
            delay=args.delay,
            animate=not args.no_animate,
        )
    parser.error(f"The {args.command!r} capability has not been installed yet.")
    return 2

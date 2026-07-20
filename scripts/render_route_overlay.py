"""Render the video-ready route comparison from synthetic demo data."""

from __future__ import annotations

import argparse
from pathlib import Path

from jxops.routes import build_demo, render_overlay, validate_route


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/video-route-overlay.svg"),
        help="Destination SVG path.",
    )
    args = parser.parse_args()

    demo = build_demo()
    rejected = validate_route(demo.grid, demo.unsafe_route)
    accepted = validate_route(demo.grid, demo.safe_route)
    if rejected.valid or not accepted.valid:
        print("Route comparison precondition failed; overlay was not produced.")
        return 1

    output = render_overlay(demo, args.output)
    print(f"Rejected route: FAIL ({len(rejected.trap_hits)} trap tiles)")
    print(f"Validated route: PASS ({len(demo.safe_route)} steps)")
    print(f"Video overlay: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


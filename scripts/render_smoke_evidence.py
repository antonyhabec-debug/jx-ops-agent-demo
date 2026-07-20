"""Render captured smoke-test output as a terminal-style SVG."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path


def _read(path: Path) -> list[str]:
    return [line.rstrip() for line in path.read_text(encoding="utf-8-sig").splitlines()]


def _nonempty(lines: list[str]) -> list[str]:
    return [line for line in lines if line.strip()]


def _tail_from(lines: list[str], marker: str) -> list[str]:
    for index, line in enumerate(lines):
        if line.startswith(marker):
            return lines[index:]
    return lines[-5:]


def build_transcript(evidence_dir: Path) -> list[str]:
    environment = _nonempty(_read(evidence_dir / "environment.txt"))
    routes = _nonempty(_read(evidence_dir / "routes.txt"))
    incident = _nonempty(_read(evidence_dir / "incident.txt"))
    bots = _nonempty(_tail_from(_read(evidence_dir / "bots.txt"), "Simulation health:"))
    boot = _nonempty(_read(evidence_dir / "boot.txt"))

    return [
        "$ python --version",
        *environment,
        "",
        "$ jxops routes --demo",
        *routes,
        "",
        "$ jxops incident --analyze samples/incident-demo.log",
        *incident,
        "",
        "$ jxops bots --sim",
        *bots,
        "",
        "$ jxops boot --mock",
        *boot,
    ]


def render_svg(lines: list[str], output_path: Path) -> Path:
    font_size = 15
    line_height = 22
    width = 1220
    top = 72
    bottom = 30
    height = top + len(lines) * line_height + bottom
    text_nodes: list[str] = []

    for index, line in enumerate(lines):
        display = line if len(line) <= 132 else line[:129] + "..."
        color = "#86efac" if line.startswith("$") else "#dbeafe"
        if "FAIL" in line and "Rejected route" not in line:
            color = "#fca5a5"
        elif any(token in line for token in ("PASS", "HEALTHY", "INCIDENT")):
            color = "#fde68a"
        y = top + index * line_height
        text_nodes.append(
            f'<text x="28" y="{y}" fill="{color}" font-family="Consolas, monospace" '
            f'font-size="{font_size}">{escape(display)}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" rx="18" fill="#020617" />
  <rect width="100%" height="48" rx="18" fill="#172033" />
  <rect y="30" width="100%" height="18" fill="#172033" />
  <circle cx="24" cy="24" r="7" fill="#fb7185" />
  <circle cx="48" cy="24" r="7" fill="#fbbf24" />
  <circle cx="72" cy="24" r="7" fill="#4ade80" />
  <text x="610" y="29" text-anchor="middle" fill="#cbd5e1" font-family="Consolas, monospace" font-size="15">fresh venv / end-to-end smoke test</text>
  {''.join(text_nodes)}
</svg>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return output_path.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    transcript = build_transcript(args.evidence_dir)
    summary_path = args.evidence_dir / "smoke-summary.txt"
    summary_path.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    rendered = render_svg(transcript, args.output)
    print(f"Transcript lines: {len(transcript)}")
    print(f"Summary: {summary_path.resolve()}")
    print(f"Terminal SVG: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


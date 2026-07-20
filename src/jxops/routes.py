"""Route validation and SVG rendering for a synthetic tile map."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

Point = tuple[int, int]


@dataclass(frozen=True)
class GridMap:
    name: str
    width: int
    height: int
    traps: frozenset[Point]

    def contains(self, point: Point) -> bool:
        x, y = point
        return 0 <= x < self.width and 0 <= y < self.height


@dataclass(frozen=True)
class RouteValidation:
    valid: bool
    issues: tuple[str, ...]
    trap_hits: tuple[Point, ...]


@dataclass(frozen=True)
class RouteDemo:
    grid: GridMap
    unsafe_route: tuple[Point, ...]
    safe_route: tuple[Point, ...]


def validate_route(grid: GridMap, route: Iterable[Point]) -> RouteValidation:
    points = tuple(route)
    issues: list[str] = []
    trap_hits: list[Point] = []

    if not points:
        issues.append("route is empty")

    for index, point in enumerate(points):
        if not grid.contains(point):
            issues.append(f"step {index} is outside the map at {point}")
        if point in grid.traps:
            trap_hits.append(point)

    for index, (current, following) in enumerate(zip(points, points[1:])):
        distance = abs(current[0] - following[0]) + abs(current[1] - following[1])
        if distance != 1:
            issues.append(
                f"steps {index} and {index + 1} are not cardinal neighbors: "
                f"{current} -> {following}"
            )

    if trap_hits:
        formatted = ", ".join(f"({x},{y})" for x, y in trap_hits)
        issues.append(f"route crosses trap tiles: {formatted}")

    return RouteValidation(not issues, tuple(issues), tuple(trap_hits))


def build_demo() -> RouteDemo:
    traps = frozenset({(6, 4), (7, 4), (8, 4), (11, 6), (12, 6), (12, 7)})
    grid = GridMap(name="synthetic-sector-380", width=16, height=9, traps=traps)
    unsafe_route = tuple((x, 4) for x in range(1, 15))
    safe_route = (
        (1, 4),
        (1, 3),
        *((x, 3) for x in range(2, 15)),
        (14, 4),
    )
    return RouteDemo(grid=grid, unsafe_route=unsafe_route, safe_route=safe_route)


def _polyline(route: Iterable[Point], tile: int, margin: int) -> str:
    return " ".join(
        f"{margin + x * tile + tile / 2:.1f},{margin + y * tile + tile / 2:.1f}"
        for x, y in route
    )


def render_overlay(demo: RouteDemo, output_path: Path) -> Path:
    tile = 44
    margin = 34
    legend_height = 92
    width = demo.grid.width * tile + margin * 2
    height = demo.grid.height * tile + margin * 2 + legend_height
    old_points = _polyline(demo.unsafe_route, tile, margin)
    new_points = _polyline(demo.safe_route, tile, margin)

    cells: list[str] = []
    for y in range(demo.grid.height):
        for x in range(demo.grid.width):
            trap = (x, y) in demo.grid.traps
            fill = "#fed7aa" if trap else "#f8fafc"
            cells.append(
                f'<rect x="{margin + x * tile}" y="{margin + y * tile}" '
                f'width="{tile}" height="{tile}" fill="{fill}" '
                f'stroke="#cbd5e1" stroke-width="1" />'
            )
            if trap:
                cx = margin + x * tile + tile / 2
                cy = margin + y * tile + tile / 2
                cells.append(
                    f'<path d="M {cx - 10} {cy - 10} L {cx + 10} {cy + 10} '
                    f'M {cx + 10} {cy - 10} L {cx - 10} {cy + 10}" '
                    'stroke="#c2410c" stroke-width="4" stroke-linecap="round" />'
                )

    legend_y = margin + demo.grid.height * tile + 44
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#0f172a" />
  <text x="{margin}" y="24" fill="#e2e8f0" font-family="monospace" font-size="16" font-weight="700">TRAP-AWARE ROUTE VALIDATION / SYNTHETIC SECTOR 380</text>
  {''.join(cells)}
  <polyline points="{old_points}" fill="none" stroke="#dc2626" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" opacity="0.82" />
  <polyline points="{new_points}" fill="none" stroke="#16a34a" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" opacity="0.92" />
  <circle cx="{margin + 1 * tile + tile / 2}" cy="{margin + 4 * tile + tile / 2}" r="9" fill="#f8fafc" stroke="#0f172a" stroke-width="3" />
  <circle cx="{margin + 14 * tile + tile / 2}" cy="{margin + 4 * tile + tile / 2}" r="9" fill="#f8fafc" stroke="#0f172a" stroke-width="3" />
  <line x1="{margin}" y1="{legend_y}" x2="{margin + 42}" y2="{legend_y}" stroke="#dc2626" stroke-width="8" stroke-linecap="round" />
  <text x="{margin + 54}" y="{legend_y + 5}" fill="#fecaca" font-family="monospace" font-size="15">Rejected route: crosses three trap tiles</text>
  <line x1="{margin + 390}" y1="{legend_y}" x2="{margin + 432}" y2="{legend_y}" stroke="#16a34a" stroke-width="8" stroke-linecap="round" />
  <text x="{margin + 444}" y="{legend_y + 5}" fill="#bbf7d0" font-family="monospace" font-size="15">Validated detour</text>
</svg>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return output_path.resolve()


def run_demo(output_path: Path) -> int:
    demo = build_demo()
    unsafe = validate_route(demo.grid, demo.unsafe_route)
    safe = validate_route(demo.grid, demo.safe_route)
    rendered = render_overlay(demo, output_path)

    print("JX OPS / ROUTE VALIDATOR")
    print(f"Map: {demo.grid.name} ({demo.grid.width}x{demo.grid.height})")
    print(
        "Rejected route: FAIL - "
        f"{len(unsafe.trap_hits)} trap hits at {list(unsafe.trap_hits)}"
    )
    print(f"Candidate route: {'PASS' if safe.valid else 'FAIL'} - {len(demo.safe_route)} steps")
    print(f"SVG overlay: {rendered}")
    return 0 if not unsafe.valid and safe.valid else 1


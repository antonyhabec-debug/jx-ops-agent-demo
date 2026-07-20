"""Deterministic bot swarm simulation built on validated synthetic routes."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys
import time

from jxops.routes import GridMap, Point, build_demo, validate_route


class BotState(str, Enum):
    IDLE = "idle"
    ROUTE = "route"
    ENGAGE = "engage"
    REGROUP = "regroup"


@dataclass
class Bot:
    bot_id: int
    path_index: int
    state: BotState = BotState.IDLE
    state_ticks: int = 0

    @property
    def label(self) -> str:
        return f"B{self.bot_id:02d}"


@dataclass(frozen=True)
class AoiEvent:
    tick: int
    bot_label: str
    action: str
    zone: str

    def display(self) -> str:
        return f"t={self.tick:02d} AOI {self.action:<5} {self.bot_label} zone={self.zone}"


@dataclass(frozen=True)
class SimulationResult:
    bots: tuple[Bot, ...]
    events: tuple[AoiEvent, ...]
    ticks: int


def _zone_for(point: Point) -> str:
    x, _ = point
    if x < 5:
        return "west"
    if x < 10:
        return "center"
    return "east"


class SwarmSimulation:
    def __init__(self, grid: GridMap, route: tuple[Point, ...], bot_count: int = 12):
        if not 10 <= bot_count <= 20:
            raise ValueError("bot_count must be between 10 and 20")
        validation = validate_route(grid, route)
        if not validation.valid:
            raise ValueError(f"simulation route is invalid: {validation.issues}")
        self.grid = grid
        self.route = route
        self.bots = [
            Bot(bot_id=index + 1, path_index=(index * 2) % len(route))
            for index in range(bot_count)
        ]
        self.events: list[AoiEvent] = []

    def _transition(self, bot: Bot) -> None:
        bot.state_ticks = 0
        if bot.state == BotState.IDLE:
            bot.state = BotState.ROUTE
        elif bot.state == BotState.ROUTE:
            bot.state = BotState.ENGAGE
        elif bot.state == BotState.ENGAGE:
            bot.state = BotState.REGROUP
        else:
            bot.state = BotState.IDLE

    def _move_and_record(self, bot: Bot, next_index: int, tick: int) -> None:
        old_zone = _zone_for(self.route[bot.path_index])
        bot.path_index = next_index
        new_zone = _zone_for(self.route[bot.path_index])
        if new_zone != old_zone:
            self.events.append(AoiEvent(tick, bot.label, "leave", old_zone))
            self.events.append(AoiEvent(tick, bot.label, "enter", new_zone))

    def tick(self, tick_number: int) -> None:
        for bot in self.bots:
            bot.state_ticks += 1
            if bot.state == BotState.IDLE:
                if bot.state_ticks >= 1 + (bot.bot_id % 2):
                    self._transition(bot)
            elif bot.state == BotState.ROUTE:
                if bot.path_index < len(self.route) - 1:
                    self._move_and_record(bot, bot.path_index + 1, tick_number)
                else:
                    self._transition(bot)
            elif bot.state == BotState.ENGAGE:
                if bot.state_ticks >= 2:
                    self._transition(bot)
            elif bot.path_index > 0:
                self._move_and_record(bot, bot.path_index - 1, tick_number)
            else:
                self._transition(bot)

    def position(self, bot: Bot) -> Point:
        return self.route[bot.path_index]


def render_terminal(
    simulation: SwarmSimulation,
    tick_number: int,
    total_ticks: int,
    interactive: bool,
) -> None:
    occupancy: dict[Point, list[Bot]] = defaultdict(list)
    for bot in simulation.bots:
        occupancy[simulation.position(bot)].append(bot)

    route_tiles = set(simulation.route)
    rows: list[str] = []
    border = "+" + "-" * simulation.grid.width + "+"
    rows.append(border)
    for y in range(simulation.grid.height):
        cells: list[str] = []
        for x in range(simulation.grid.width):
            point = (x, y)
            occupants = occupancy.get(point, [])
            if len(occupants) > 1:
                cells.append("*")
            elif occupants:
                cells.append(format(occupants[0].bot_id % 16, "X"))
            elif point in simulation.grid.traps:
                cells.append("X")
            elif point in route_tiles:
                cells.append(".")
            else:
                cells.append(" ")
        rows.append("|" + "".join(cells) + "|")
    rows.append(border)

    counts = Counter(bot.state.value for bot in simulation.bots)
    states = " ".join(
        f"{state.value}={counts.get(state.value, 0):02d}" for state in BotState
    )
    recent = simulation.events[-4:]
    event_lines = [event.display() for event in recent]
    while len(event_lines) < 4:
        event_lines.insert(0, "-")

    frame = "\n".join(
        [
            f"JX OPS / BOT SWARM  tick {tick_number:02d}/{total_ticks:02d}",
            *rows,
            states,
            "Recent AOI events:",
            *event_lines,
            "Legend: 1-F=bot, *=stacked bots, X=trap, .=validated route",
        ]
    )
    if interactive:
        prefix = "\x1b[2J\x1b[H" if tick_number == 1 else "\x1b[H"
        print(prefix + frame, end="", flush=True)
    else:
        print(frame)
        print()


def render_final_svg(simulation: SwarmSimulation, output_path: Path) -> Path:
    tile = 46
    margin = 36
    footer = 100
    width = simulation.grid.width * tile + margin * 2
    height = simulation.grid.height * tile + margin * 2 + footer
    route_points = " ".join(
        f"{margin + x * tile + tile / 2},{margin + y * tile + tile / 2}"
        for x, y in simulation.route
    )

    cells: list[str] = []
    for y in range(simulation.grid.height):
        for x in range(simulation.grid.width):
            fill = "#7c2d12" if (x, y) in simulation.grid.traps else "#111827"
            cells.append(
                f'<rect x="{margin + x * tile}" y="{margin + y * tile}" '
                f'width="{tile}" height="{tile}" fill="{fill}" '
                'stroke="#334155" stroke-width="1" />'
            )

    bot_nodes: list[str] = []
    state_colors = {
        BotState.IDLE: "#94a3b8",
        BotState.ROUTE: "#22c55e",
        BotState.ENGAGE: "#f97316",
        BotState.REGROUP: "#38bdf8",
    }
    offsets: Counter[Point] = Counter()
    for bot in simulation.bots:
        x, y = simulation.position(bot)
        stack_index = offsets[(x, y)]
        offsets[(x, y)] += 1
        dx = (stack_index % 3 - 1) * 11
        dy = (stack_index // 3) * 11
        cx = margin + x * tile + tile / 2 + dx
        cy = margin + y * tile + tile / 2 + dy
        color = state_colors[bot.state]
        bot_nodes.append(
            f'<circle cx="{cx}" cy="{cy}" r="10" fill="{color}" '
            'stroke="#f8fafc" stroke-width="2" />'
        )
        bot_nodes.append(
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" fill="#0f172a" '
            f'font-family="monospace" font-size="9" font-weight="700">{bot.bot_id}</text>'
        )

    counts = Counter(bot.state.value for bot in simulation.bots)
    summary = " / ".join(f"{state.value}: {counts[state.value]}" for state in BotState)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#020617" />
  <text x="{margin}" y="25" fill="#e2e8f0" font-family="monospace" font-size="17" font-weight="700">VALIDATED-ROUTE BOT SWARM / FINAL FRAME</text>
  {''.join(cells)}
  <polyline points="{route_points}" fill="none" stroke="#22c55e" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" opacity="0.6" />
  {''.join(bot_nodes)}
  <text x="{margin}" y="{margin + simulation.grid.height * tile + 42}" fill="#cbd5e1" font-family="monospace" font-size="15">{summary}</text>
  <text x="{margin}" y="{margin + simulation.grid.height * tile + 70}" fill="#7dd3fc" font-family="monospace" font-size="14">AOI enter/leave events: {len(simulation.events)}</text>
</svg>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return output_path.resolve()


def run_simulation(
    output_path: Path,
    bot_count: int = 12,
    ticks: int = 14,
    delay: float = 0.12,
    animate: bool = True,
) -> int:
    demo = build_demo()
    validation = validate_route(demo.grid, demo.safe_route)
    if not validation.valid:
        print(f"Validated route precondition failed: {validation.issues}")
        return 1

    simulation = SwarmSimulation(demo.grid, demo.safe_route, bot_count)
    interactive = animate and sys.stdout.isatty()
    for tick_number in range(1, ticks + 1):
        simulation.tick(tick_number)
        render_terminal(simulation, tick_number, ticks, interactive)
        if interactive and delay:
            time.sleep(delay)
    if interactive:
        print()

    rendered = render_final_svg(simulation, output_path)
    counts = Counter(bot.state.value for bot in simulation.bots)
    print("Simulation health: PASS")
    print(f"Bots: {len(simulation.bots)} | Ticks: {ticks} | AOI events: {len(simulation.events)}")
    print("States: " + ", ".join(f"{name}={count}" for name, count in sorted(counts.items())))
    print(f"Final SVG: {rendered}")
    return 0

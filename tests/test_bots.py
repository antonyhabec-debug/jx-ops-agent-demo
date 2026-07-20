from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jxops.bots import SwarmSimulation, render_final_svg
from jxops.routes import build_demo


class BotSimulationTests(unittest.TestCase):
    def test_swarm_uses_only_validated_route_tiles(self) -> None:
        demo = build_demo()
        simulation = SwarmSimulation(demo.grid, demo.safe_route, bot_count=12)
        for tick in range(1, 11):
            simulation.tick(tick)

        route_tiles = set(demo.safe_route)
        self.assertTrue(all(simulation.position(bot) in route_tiles for bot in simulation.bots))
        self.assertGreater(len(simulation.events), 0)

    def test_population_limits_are_enforced(self) -> None:
        demo = build_demo()
        with self.assertRaises(ValueError):
            SwarmSimulation(demo.grid, demo.safe_route, bot_count=9)
        with self.assertRaises(ValueError):
            SwarmSimulation(demo.grid, demo.safe_route, bot_count=21)

    def test_final_svg_contains_bot_and_aoi_summary(self) -> None:
        demo = build_demo()
        simulation = SwarmSimulation(demo.grid, demo.safe_route, bot_count=10)
        simulation.tick(1)
        with TemporaryDirectory() as directory:
            output = Path(directory) / "bots.svg"
            render_final_svg(simulation, output)
            svg = output.read_text(encoding="utf-8")
        self.assertIn("BOT SWARM", svg)
        self.assertIn("AOI enter/leave events", svg)


if __name__ == "__main__":
    unittest.main()


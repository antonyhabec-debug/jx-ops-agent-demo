from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jxops.routes import GridMap, build_demo, render_overlay, validate_route


class RouteValidationTests(unittest.TestCase):
    def test_demo_rejects_old_route_and_accepts_detour(self) -> None:
        demo = build_demo()

        rejected = validate_route(demo.grid, demo.unsafe_route)
        accepted = validate_route(demo.grid, demo.safe_route)

        self.assertFalse(rejected.valid)
        self.assertEqual(3, len(rejected.trap_hits))
        self.assertTrue(accepted.valid)

    def test_non_neighbor_step_is_rejected(self) -> None:
        grid = GridMap("test", 4, 4, frozenset())
        result = validate_route(grid, ((0, 0), (2, 0)))
        self.assertFalse(result.valid)
        self.assertIn("not cardinal neighbors", result.issues[0])

    def test_svg_contains_both_route_colors(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "overlay.svg"
            render_overlay(build_demo(), output)
            svg = output.read_text(encoding="utf-8")
        self.assertIn("#dc2626", svg)
        self.assertIn("#16a34a", svg)


if __name__ == "__main__":
    unittest.main()


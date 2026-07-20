import unittest

from jxops.boot import BootStage, MockBootSession, run_mock_boot


class MockBootTests(unittest.TestCase):
    def test_full_order_reaches_healthy(self) -> None:
        session = MockBootSession()
        for stage in session.ordered_stages:
            session.advance(stage, elapsed_ms=1)
        self.assertTrue(session.healthy)

    def test_out_of_order_stage_is_rejected(self) -> None:
        session = MockBootSession()
        with self.assertRaises(RuntimeError):
            session.advance(BootStage.WORLD_SPAWN, elapsed_ms=1)

    def test_mock_boot_command_succeeds_without_delay(self) -> None:
        self.assertEqual(0, run_mock_boot(delay=0))


if __name__ == "__main__":
    unittest.main()


"""Headless mock boot state machine for a sanitized server lane."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import time


class BootStage(str, Enum):
    LOAD_CONFIG = "load-config"
    DATABASE_CHECK = "database-check"
    WORLD_SPAWN = "world-spawn"
    READY = "ready"


@dataclass(frozen=True)
class StageResult:
    stage: BootStage
    status: str
    detail: str
    elapsed_ms: int


class MockBootSession:
    ordered_stages = (
        BootStage.LOAD_CONFIG,
        BootStage.DATABASE_CHECK,
        BootStage.WORLD_SPAWN,
        BootStage.READY,
    )

    details = {
        BootStage.LOAD_CONFIG: "validated isolated demo configuration",
        BootStage.DATABASE_CHECK: "in-memory data adapter responded",
        BootStage.WORLD_SPAWN: "synthetic world and AOI index created",
        BootStage.READY: "health gate accepted the mock lane",
    }

    def __init__(self) -> None:
        self.results: list[StageResult] = []

    def advance(self, stage: BootStage, elapsed_ms: int) -> StageResult:
        expected_index = len(self.results)
        if expected_index >= len(self.ordered_stages):
            raise RuntimeError("boot session is already complete")
        expected = self.ordered_stages[expected_index]
        if stage != expected:
            raise RuntimeError(f"expected {expected.value}, received {stage.value}")
        result = StageResult(stage, "PASS", self.details[stage], elapsed_ms)
        self.results.append(result)
        return result

    @property
    def healthy(self) -> bool:
        return (
            len(self.results) == len(self.ordered_stages)
            and all(result.status == "PASS" for result in self.results)
            and self.results[-1].stage == BootStage.READY
        )


def _timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def run_mock_boot(delay: float = 0.08) -> int:
    session = MockBootSession()
    print("JX OPS / HEADLESS BOOT")
    print(f"{_timestamp()} INFO  lane=buildweek-sandbox mode=mock event=boot-start")

    for index, stage in enumerate(session.ordered_stages, start=1):
        started = time.perf_counter()
        if delay:
            time.sleep(delay)
        elapsed_ms = max(1, round((time.perf_counter() - started) * 1000))
        result = session.advance(stage, elapsed_ms)
        print(
            f"{_timestamp()} PASS  stage={result.stage.value:<14} "
            f"elapsed={result.elapsed_ms:03d}ms detail=\"{result.detail}\""
        )

    total_ms = sum(result.elapsed_ms for result in session.results)
    print("\nHEALTH SUMMARY")
    print("+----------------+--------+")
    print("| component      | status |")
    print("+----------------+--------+")
    print("| config         | PASS   |")
    print("| data-adapter   | PASS   |")
    print("| world          | PASS   |")
    print("| readiness      | PASS   |")
    print("+----------------+--------+")
    print(f"Overall: {'HEALTHY' if session.healthy else 'UNHEALTHY'} ({total_ms}ms)")
    return 0 if session.healthy else 1


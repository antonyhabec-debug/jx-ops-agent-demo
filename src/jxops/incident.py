"""Pattern-based incident analysis for sanitized operational logs."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

WARP_RE = re.compile(
    r"\bWARP\b.*\bactor=(?P<actor>[\w-]+).*\bfrom=(?P<source>[\w-]+).*\bto=(?P<target>[\w-]+)"
)
AOI_RE = re.compile(
    r"\bAOI\b.*\baction=(?P<action>enter|leave).*\bentity=(?P<entity>[\w-]+).*\bregion=(?P<region>[\w-]+)"
)


@dataclass(frozen=True)
class Finding:
    kind: str
    severity: str
    subject: str
    evidence_count: int
    summary: str


@dataclass(frozen=True)
class IncidentAnalysis:
    line_count: int
    findings: tuple[Finding, ...]


def analyze_lines(lines: list[str]) -> IncidentAnalysis:
    warps: dict[str, list[tuple[str, str]]] = defaultdict(list)
    aoi_counts: Counter[tuple[str, str, str]] = Counter()

    for line in lines:
        warp = WARP_RE.search(line)
        if warp:
            warps[warp.group("actor")].append(
                (warp.group("source"), warp.group("target"))
            )
        aoi = AOI_RE.search(line)
        if aoi:
            aoi_counts[(aoi.group("entity"), aoi.group("region"), aoi.group("action"))] += 1

    findings: list[Finding] = []
    for actor, transitions in sorted(warps.items()):
        if len(transitions) < 4:
            continue
        endpoints = {point for transition in transitions for point in transition}
        opposing_pairs = any((target, source) in transitions for source, target in transitions)
        if len(endpoints) == 2 and opposing_pairs:
            findings.append(
                Finding(
                    kind="warp-loop",
                    severity="critical",
                    subject=actor,
                    evidence_count=len(transitions),
                    summary=(
                        "Repeated corrective warps alternate across the same boundary, "
                        "indicating an invalid route crossing rather than random movement."
                    ),
                )
            )

    entity_regions = {(entity, region) for entity, region, _ in aoi_counts}
    for entity, region in sorted(entity_regions):
        enters = aoi_counts[(entity, region, "enter")]
        leaves = aoi_counts[(entity, region, "leave")]
        churn = enters + leaves
        if enters >= 3 and leaves >= 3:
            findings.append(
                Finding(
                    kind="region-churn",
                    severity="high",
                    subject=f"{entity}@{region}",
                    evidence_count=churn,
                    summary=(
                        "Balanced AOI enter/leave events repeat at one region boundary, "
                        "which would present as visibility flicker to nearby observers."
                    ),
                )
            )

    return IncidentAnalysis(line_count=len(lines), findings=tuple(findings))


def analyze_file(log_path: Path) -> IncidentAnalysis:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    return analyze_lines(lines)


def render_report(analysis: IncidentAnalysis, source_name: str) -> str:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    status = "INCIDENT CONFIRMED" if analysis.findings else "NO INCIDENT PATTERN FOUND"
    finding_rows = "\n".join(
        f"| {item.severity.upper()} | `{item.kind}` | `{item.subject}` | "
        f"{item.evidence_count} | {item.summary} |"
        for item in analysis.findings
    ) or "| INFO | `none` | - | 0 | No threshold was exceeded. |"

    root_causes: list[str] = []
    if any(item.kind == "warp-loop" for item in analysis.findings):
        root_causes.append(
            "1. **Route safety failure:** a movement path crosses a hazardous boundary. "
            "The recovery warp returns the actor to the opposite side, so the next route "
            "tick repeats the same invalid transition."
        )
    if any(item.kind == "region-churn" for item in analysis.findings):
        root_causes.append(
            "2. **AOI lifecycle instability:** repeated boundary oscillation removes and "
            "reintroduces the same entity. Observers receive alternating visibility state."
        )
    if not root_causes:
        root_causes.append("No root cause is asserted because the evidence thresholds were not met.")

    return f"""# Incident Analysis

**Status:** {status}  
**Source:** `{source_name}`  
**Generated:** {generated}  
**Lines examined:** {analysis.line_count}

## Evidence

| Severity | Pattern | Subject | Events | Interpretation |
| --- | --- | --- | ---: | --- |
{finding_rows}

## Root Cause

{chr(10).join(root_causes)}

## Bounded Remediation

- Reject routes that intersect hazardous tiles before actors enter the world.
- Keep recovery warps from immediately replaying the failed route segment.
- Debounce AOI removal during short-lived boundary oscillation.
- Change only movement validation and AOI lifecycle guards; protocol and persistence stay out of scope.

## Verification Plan

1. Replay the same synthetic route and require zero hazardous-tile intersections.
2. Run repeated movement ticks and require no opposing warp pair for one actor.
3. Observe the boundary region and require stable AOI membership after convergence.
4. Re-run this analyzer and require no critical or high findings.
"""


def run_analysis(log_path: Path, output_path: Path) -> int:
    if not log_path.is_file():
        print(f"Log file not found: {log_path}")
        return 2
    analysis = analyze_file(log_path)
    report = render_report(analysis, log_path.name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print("JX OPS / INCIDENT ANALYZER")
    print(f"Source: {log_path.resolve()}")
    print(f"Lines examined: {analysis.line_count}")
    for finding in analysis.findings:
        print(
            f"[{finding.severity.upper()}] {finding.kind}: {finding.subject} "
            f"({finding.evidence_count} events)"
        )
    print(f"Markdown report: {output_path.resolve()}")
    return 1 if not analysis.findings else 0


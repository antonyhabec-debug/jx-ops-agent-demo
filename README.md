# JX Ops Agent Demo

JX Ops Agent Demo is a clean-room operations sandbox for a fictional legacy
MMO fleet. It turns four hard-to-explain production workflows into safe,
repeatable commands: route validation, incident analysis, headless boot, and an
animated bot population. The repository contains no original game code,
artwork, binaries, database content, network routes, or private configuration.

The project was built during OpenAI Build Week 2026 with Codex and GPT-5.6. It
distills lessons from operating old online software into a toolkit that judges
can run locally with Python alone.

## Judge Quick Start

Requirements:

- Python 3.9 or newer
- Windows, Linux, or macOS
- A terminal that can run `pip`

From the repository root:

```bash
python -m venv .venv
```

Activate the environment:

```text
Windows PowerShell: .venv\Scripts\Activate.ps1
Linux/macOS:        source .venv/bin/activate
```

Install the local package and run the four demos:

```bash
python -m pip install -e .
jxops routes --demo
jxops incident --analyze samples/incident-demo.log
jxops bots --sim
jxops boot --mock
```

No external service, game installation, database, API key, or third-party
Python package is required at runtime. Generated SVG and Markdown files appear
under `artifacts/`.

## What The Commands Show

### `jxops routes --demo`

Builds a synthetic tile grid with hazardous cells, validates two routes, and
renders `artifacts/routes-demo.svg`. The rejected route is red and intersects
three hazards; the accepted route is green and takes a cardinal detour.

### `jxops incident --analyze samples/incident-demo.log`

Finds an alternating warp loop and repeated area-of-interest membership churn
in a sanitized log. It writes `artifacts/incident-report.md` with evidence,
root-cause reasoning, a bounded remediation, and a verification plan.

### `jxops bots --sim`

Runs 12 deterministic agents on the validated route. Every bot moves through
`idle -> route -> engage -> regroup`, while the terminal refreshes an ASCII
map and displays area-of-interest enter/leave events. The final population is
rendered to `artifacts/bots-final.svg`.

For a compact non-interactive run:

```bash
jxops bots --sim --ticks 6 --delay 0 --no-animate
```

### `jxops boot --mock`

Exercises a strict headless state machine:
`load config -> database check -> world spawn -> ready`. Each stage emits a
timestamped result and the command ends with a health table. Every component is
in memory; it cannot contact or alter a live service.

## Architecture

```text
CLI
 |-- routes: synthetic map -> validator -> SVG overlay
 |-- incident: sanitized log -> detectors -> Markdown report
 |-- bots: validated route -> bot state machines -> ASCII/SVG + AOI events
 `-- boot: ordered mock stages -> health summary
```

The route module is deliberately shared with the swarm. A bot simulation cannot
start unless its route passes the same validation shown in the route demo.
This small invariant demonstrates the larger operational idea: the agent must
turn diagnosis into a machine-checkable safety gate.

## Case Studies

- [Preventing a Corrective-Warp Loop](docs/trap-warp-route-validation.md)
- [Diagnosing AOI Visibility Flicker](docs/aoi-flicker-region-churn.md)

Both stories are newly written, generalized accounts. Names, coordinates,
events, and data in this repository are synthetic.

## Prior Work vs. This Week

| Area | Prior work before Build Week | New work built during 13-21 July 2026 |
| --- | --- | --- |
| Operations | A private manager and human runbooks for multiple legacy server lanes | A public-safe command model and judge workflow |
| Incident response | Manual investigation of production symptoms | A clean-room log analyzer with deterministic detectors and a structured report |
| Route safety | Operational knowledge that hazardous map cells can destabilize movement | A new synthetic map model, route validator, test suite, and dual-route SVG |
| Bot population | Private experience with scripted NPC populations | A new 10-20 agent state-machine simulation using only synthetic data |
| Boot validation | Private headless testing practices | A new in-memory boot state machine and health summary |
| Documentation | Internal notes tied to private infrastructure | New English README, case studies, sample log, demo artifacts, and tests |

Only the right-hand column is represented in this repository and submitted for
judging. The earlier system provided the problem domain, not reusable code or
assets. Every Python, test, sample, SVG generator, and document here was
created clean-room during the event.

## How We Built This With Codex

Codex with GPT-5.6 implemented the submission repository in one continuous
Build Week session. It converted operational goals into small modules, wrote
the command interface, built deterministic fixtures, added tests, executed each
command, and iterated on the outputs. Frequent Git commits preserve the build
sequence and make the new work auditable.

The human supplied the real-world problem framing, selected the Developer Tools
track, set the privacy boundary, and decided that the demo must emphasize the
bot swarm rather than a polished but passive dashboard. The key human safety
decision was to forbid any reuse of private game source or assets. GPT-5.6's
main contribution was turning those constraints into an integrated, testable
sandbox quickly while keeping the route, incident, simulation, and boot stories
coherent.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover route hazards and adjacency, incident thresholds and report
shape, swarm population limits and route confinement, SVG generation, and boot
ordering.

## Privacy And Ownership

This repository intentionally uses invented map geometry, identifiers, events,
and service behavior. It is not a server emulator and cannot connect to a real
game environment. The code and documentation in this repository are released
under the MIT License.


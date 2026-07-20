# Incident Analysis

**Status:** INCIDENT CONFIRMED  
**Source:** `incident-demo.log`  
**Generated:** 2026-07-20T00:41:33+00:00  
**Lines examined:** 16

## Evidence

| Severity | Pattern | Subject | Events | Interpretation |
| --- | --- | --- | ---: | --- |
| CRITICAL | `warp-loop` | `bot-07` | 6 | Repeated corrective warps alternate across the same boundary, indicating an invalid route crossing rather than random movement. |
| HIGH | `region-churn` | `bot-12@market-edge` | 6 | Balanced AOI enter/leave events repeat at one region boundary, which would present as visibility flicker to nearby observers. |

## Root Cause

1. **Route safety failure:** a movement path crosses a hazardous boundary. The recovery warp returns the actor to the opposite side, so the next route tick repeats the same invalid transition.
2. **AOI lifecycle instability:** repeated boundary oscillation removes and reintroduces the same entity. Observers receive alternating visibility state.

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

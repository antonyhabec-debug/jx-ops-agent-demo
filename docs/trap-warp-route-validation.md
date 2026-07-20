# Case Study: Preventing a Corrective-Warp Loop

## Symptom

A background character appeared to make progress across a map and then snap
back. The process stayed healthy, so basic uptime checks reported success. In
the movement log, however, the same actor crossed one boundary, received a
corrective warp, and attempted the identical segment again on its next tick.
That cycle could continue indefinitely.

## Why The First Explanation Was Incomplete

A warp loop can resemble network delay or an overloaded world process when
viewed only from the client. Those explanations did not account for the exact
alternation between two locations. The important evidence was geometric: every
loop began when the route touched a class of tile that movement should never
have selected.

The recovery behavior was individually reasonable. It moved the actor away
from an invalid position. The route planner was also individually consistent:
it resumed from the next planned segment. Together they formed a feedback
loop. Recovery returned the actor to one side of the boundary, while the
unchanged route immediately sent it back across.

## Bounded Fix

The safe intervention is not to weaken the warp guard. It is to reject the bad
route before the actor enters the world. An offline validator needs three
properties:

1. Every point is inside the declared map dimensions.
2. Consecutive points are cardinal neighbors, preventing hidden jumps.
3. No point intersects the map's hazardous tile set.

The `jxops routes --demo` command reconstructs that reasoning with invented
geometry. Its red route crosses three hazardous tiles and fails. Its green
route preserves the same start and destination but takes a short detour that
passes all checks. The generated SVG makes the evidence understandable without
showing any proprietary map artwork.

## Operational Lesson

The most useful agent output was not a prose guess about pathfinding. It was a
testable invariant that could block unsafe data. The bot swarm in this repo
imports the same validator and refuses to start on an invalid route. That turns
incident knowledge into a reusable safety gate: diagnosis, remediation, and
future prevention share one machine-checkable rule.


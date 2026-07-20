# Case Study: Diagnosing AOI Visibility Flicker

## Symptom

An entity near a busy boundary seemed to blink out and return. It was not
crashing, teleporting, or changing identity. To an observer it simply became
visible, disappeared, and became visible again in a tight cycle.

Legacy world servers often divide space into regions and maintain an
area-of-interest (AOI) set for each observer. Entering a nearby region adds an
entity to that set; leaving removes it. A rapid boundary oscillation can
therefore look like a rendering bug even when the renderer is faithfully
applying the messages it receives.

## Evidence Pattern

The decisive signal is balanced churn for the same entity and region:
`enter, leave, enter, leave` repeated within a short window. A one-off pair is
normal movement. Several matched pairs indicate that lifecycle state is not
converging.

The sample analyzer groups AOI events by entity and region, then raises a high
severity finding when both directions cross a minimum threshold. It deliberately
does not treat all event volume as an incident. That keeps a crowded but healthy
area from being mislabeled.

## Root Cause And Containment

The generalized root cause is instability at the region boundary. Movement
places an entity on alternating sides, or cleanup removes it before the next
position update confirms where it belongs. Either way, observers receive a
sequence of opposing membership decisions.

A bounded remediation keeps protocol and persistence untouched. It stabilizes
the movement result first, then debounces short-lived AOI removal long enough
for the entity's region membership to converge. Verification requires that the
same movement replay produces stable membership and that the analyzer reports
no repeated churn.

## Connection To The Swarm Demo

`jxops bots --sim` logs enter and leave events whenever a simulated bot crosses
between west, center, and east zones. Those events are healthy because each bot
continues through the boundary. The incident sample shows the unhealthy
counterexample: one subject repeatedly toggles at a single edge. Showing both
behaviors makes the distinction concrete and gives the operational agent a
clear pattern to measure instead of relying on a visual description alone.


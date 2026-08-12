# Structured Event-Record Contract
**Phase:** 1d — architecture consolidation  
**Date:** 2026-08-10  
**Status:** IMPLEMENTED

## Purpose
Provide one machine-readable, append-only event stream for learner actions, future interventions, future scenario actions, debrief, scoring, replay, and the eventual Scenario Log UI. This layer records what happened; it does **not** own physiology, scenario progression, grading, or GUI rendering.

## Stable record schema
Every event contains exactly these top-level fields:

```text
timestamp
event_type
source
target
action
old_value
new_value
revision
metadata
```

- `timestamp`: timezone-aware wall-clock occurrence time, serialized as UTC ISO-8601.
- `event_type`: machine-readable category such as `control.changed`, `observation.performed`, `system.lifecycle`.
- `source`: actor/origin (`learner`, `educator`, `scenario`, `system`).
- `target`: component or domain acted on.
- `action`: stable machine-readable verb/action identifier.
- `old_value` / `new_value`: JSON-compatible before/after values where meaningful.
- `revision`: optional revision identifier when an event participates in revision-safe asynchronous work.
- `metadata`: JSON-compatible extension data. Current workspace events include `simulation_time_s` here so wall time and simulation time are never conflated.

The record is immutable after construction. Serialization is validated before a record is accepted into the stream.

## Current integration
`EcmoWorkspaceModel` owns an `EventStream` and emits:

- `system.lifecycle / initialized` when the workspace model is created.
- `control.changed` for actual changes to learner ECMO controls.
- no event for a no-op update where old and new values are identical.

Current structured control actions include pump start/stop, commanded RPM, sweep, FdO2, bridge opening, shunt configuration, and scuffing state when changed through `EcmoWorkspaceModel.update()`.

`record_event()` is the generic Phase 1d hook for future interventions/observations. It exists specifically so Phase 2 and the future `neoscenarios` package can emit into the same stream without inventing another logger.

## Deliberate exclusions
- No Python scenario engine is created in Phase 1d.
- No trigger evaluation, objectives, scoring, branching, or scenario completion logic lives here.
- The Scenario Log GUI remains a reserved shell.
- Native-physiology async debug events remain a separate internal diagnostic stream. They are not learner events and are not silently mixed into this contract.
- Existing human-readable event-strip messages remain presentation text; they are not the canonical record format.

## Determinism and future scenarios
Future scenario code must supply deterministic scenario action inputs from the scenario engine's seeded RNG. The event stream records those actions; it does not generate randomness itself.

## Governance
All future learner/educator/scenario actions that materially change simulation state or disclose an observation should emit an `EventRecord` at the mechanism/action boundary. UI text must be rendered from structured data where practical, not parsed back into structure later.

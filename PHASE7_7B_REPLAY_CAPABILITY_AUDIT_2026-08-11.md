# Phase 7b Replay Capability Audit — 2026-08-11

## Decision

**STOP / RESCOPE REQUIRED.**

The current architecture does **not** retain sufficient immutable historical patient/workspace snapshot history to implement faithful scenario replay without re-solving physiology.

This is the required first deliverable for Fix Map v5 Phase 7b. No replay implementation is authorized from the current state.

## Evidence

1. `src/neoevents/core.py`
   - `EventRecord` is frozen and its JSON-compatible payload is recursively frozen.
   - `EventStream` is append-only and exposes tuple records.
   - The event schema records actions/changes/metadata. It is not a complete `WorkspaceSnapshot` archive.

2. `src/neogui/ecmo_workspace.py`
   - `EcmoWorkspaceModel.solve()` creates a current `WorkspaceSnapshot` from the current inputs and `dynamic.snapshot()`.
   - `EcmoWorkspaceModel.advance()` returns a current snapshot after advancing the dynamic system.
   - The model has no historical `WorkspaceSnapshot` collection.
   - `EcmoWorkspace` retains `_last_snapshot` only for the current GUI projection; prior snapshots are replaced.

3. `src/neoscenarios/engine.py`, `state_machine.py`, and `rng.py`
   - Existing `snapshot()` contracts preserve scenario orchestration / state-machine / RNG state.
   - They are not immutable time-indexed captures of the coupled neonatal patient, ECMO circuit, labs, displayed state, and GUI-relevant projections.

## Why event-only reconstruction is insufficient

Replaying event records by applying actions again would require the simulator to re-solve dynamic/native physiology. That would be a new simulation run, not historical replay. It could diverge because of asynchronous native-physiology timing, future solver changes, RNG/version changes, or state not represented in individual event payloads.

A Phase-7 replay surface must therefore not claim that event re-execution reproduces the original clinical state.

## Rescope required before replay code

A future replay contract should separately specify:

- immutable time-indexed historical snapshot ownership;
- snapshot capture cadence and event-boundary captures;
- exactly which patient, ECMO, lab, scenario, displayed/measurement, and availability state is frozen;
- schema/version migration;
- storage and memory limits;
- persistence/export expectations;
- synchronization between snapshots and canonical event IDs;
- handling of asynchronous native-physiology pending/committed state;
- a guarantee that replay is projection-only and never calls physiology/hydraulic solvers.

Until that contract is authorized, **no replay controls, scrubber, reconstruction engine, or event re-execution path should be added.**

## Phase 7 boundary

- 7a read-only event-stream debrief: implementable and authorized.
- 7b replay: gate failed; stopped and rescope required.
- 7c scoring: explicit HOLD; no code.
- 7d educator dashboard/scenario builder: deferred/unscoped; no code.

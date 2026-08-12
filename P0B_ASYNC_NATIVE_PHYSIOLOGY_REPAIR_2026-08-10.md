# Phase 0b — Async Native Physiology Repair

Date: 2026-08-10
Base: `neonatal-modular-patient-GUI-v0.17.1-P0-realtime-repair-2026-08-10`
Spec: `FIX_MAP_v4.md`

## Result

Phase 0b is implemented as a P0-close candidate. The GUI no longer performs a cache-invalidated native cardiopulmonary equilibrium solve synchronously on the Tk/main thread.

The existing synchronous/headless patient contract is preserved by default. Only the GUI workspace opts into the asynchronous native-physiology path.

## Architecture implemented

- Existing native cache key is reused as the immutable solver snapshot:
  - weight
  - lung run duration
  - circulation run duration
  - PEEP
  - airway opening pressure
  - FiO2
  - plus blood-volume delta as the seventh scalar solve input
- Worker receives primitives only and calls `run_coupled_neonate()` directly.
- Worker never reads or mutates the live `UnifiedNeonatalPatient` object.
- Cache mutation/commit remains on the main thread only.
- Native requests use incrementing revisions.
- Exactly one active solve and one latest-pending request are retained.
- Pending requests are overwritten by newer requests; obsolete intermediate revisions are never executed.
- An already-running solve is not cancelled; its result is discarded if stale.
- While an updated native equilibrium is required/in flight, the GUI keeps operating but simulation time does not advance on the stale native state. Zero-time snapshots continue to update/poll the circuit and commit the new equilibrium when ready.
- The GUI exposes a `PHYSIOLOGY UPDATING` advisory while native physiology is stale/in flight.
- Internal native-physiology request/result records include `event_time` and `solver_completion_time` fields.
- Worker lifecycle is shut down when the workspace closes.

## Thread vs process benchmark

A persistent thread was implemented/tested first as required by FIX_MAP_v4.

Representative sandbox result during an invalidated solve:

- immediate invalidation tick: ~64 ms
- worker settle: ~2.08 s
- main-side heartbeat maximum interval: ~357 ms
- heartbeat p95: ~90.5 ms

That did not satisfy the intended responsiveness contract in this environment, so the GUI was switched to a persistent single-worker `ProcessPoolExecutor` using explicit `spawn` semantics (matching Windows behavior and avoiding fork-from-multithreaded-process hazards).

`NativeSolveResult` was explicitly pickle round-tripped successfully before adopting the process path.

Representative process-worker result with realistic 1 Hz GUI refresh behavior:

- routine cache-hit tick mean: ~0.82 ms
- routine cache-hit tick max: ~1.04 ms
- forced-invalidation GUI callback: ~4.48 ms
- worker/equilibrium settle: ~2.01 s
- 1 Hz refresh callbacks while solve active: ~0.70–0.78 ms
- heartbeat p95 interval: ~5.82 ms
- one sandbox scheduling outlier: ~106.7 ms above the 5 ms heartbeat interval

The large single heartbeat outlier is not a synchronous GUI callback; it occurred under a CPU-constrained sandbox while a separate SciPy process was running. Real Tk event-loop jitter must still be confirmed on target Windows hardware.

## New System Behavior Contract coverage

`tests/test_native_physiology_async.py` adds:

1. Normal completion: one invalidation -> one revision -> exactly one commit.
2. Rapid supersession: active revision 1 runs; revisions 2 and 3 are overwritten; only revision 4 runs next; revision 1 is discarded stale; only revision 4 commits.
3. Simulation-time semantics: an invalidated equilibrium update does not advance simulation time while pending; normal time progression resumes once the current revision commits.

Existing native cache tests remain unchanged and passing.

## Validation completed

Focused async/cache/workspace suite after final changes:

- 13/13 pass

Additional individually/batched verified suites:

- Dynamic coupled patient/ECMO: 6/6 pass
- Coupled patient/ECMO time step: 4/4 pass
- ECMO-patient coupling contract: 5/5 pass
- ECMO workspace model: 5/5 pass
- ECMO workspace dynamic integration: 3/3 pass
- Native physiology cache: 2/2 pass
- Native physiology async/System Behavior Contracts: 3/3 pass
- ECMO-patient hydraulic coupling: 5/5 pass
- ECMO-patient gas behavior: 5/5 pass
- ECMO-patient closed-loop MAP: 6/6 pass
- ECMO preload/drainage coupling: 6/6 pass

NorthStar benches freshly regenerated and compared successfully where completed:

- ECMO bridge — PASS, 0 differences
- ECMO cannula — PASS, 0 differences
- ECMO CDI sensor — PASS, 0 differences
- ECMO console — PASS, 0 differences
- ECMO fixed shunt — PASS, 0 differences
- ECMO gas exchange — PASS, 0 differences
- ECMO main circuit full — PASS, 0 differences
- ECMO main circuit series — PASS, 0 differences
- ECMO main circuit + shunt — PASS, 0 differences
- ECMO main circuit + shunt + bridge — PASS, 0 differences
- ECMO oxygenator — PASS, 0 differences
- ECMO pump — PASS, 0 differences
- Gas exchange — PASS
- Lung — PASS, 0 differences
- Ventilator — PASS, 0 differences
- Combined equipment — PASS, 0 differences
- Cardiopulmonary coupling bundled/current comparison — PASS; full regeneration exceeded this sandbox command budget

### Pre-existing kidney bench inconsistency discovered

A fresh run of `kidney_regression_bench/run_kidney_northstar.py` emits a JSON structure that does not match the schema of `accepted_kidney_northstar_v1.json`. This is not caused by the Phase 0b change: in the input v0.17.1 package, `accepted_kidney_northstar_v1.json` and `current_kidney_northstar.json` were byte-identical before regeneration. The runner itself currently produces differently shaped keys/sections. The packaged `current_kidney_northstar.json` was restored to the accepted file so this unrelated validation-harness defect is not shipped as an artificial regression. Track the runner/schema mismatch separately; do not re-accept either schema during P0b.

## Phase 0b acceptance checklist

- PASS — Tk/main application path no longer waits synchronously for native physiology.
- PASS in sandbox callback measurements — forced-invalidation GUI callback ~4.5 ms; real Tk target-hardware event-loop measurement still required.
- PASS — routine cache-hit simulation/display ticks are far below 100–150 ms.
- PASS in sandbox callback measurements — no native solve is performed on the UI thread.
- PASS in sandbox — native solve/equilibrium settle ~2 s, below interim <=5 s target; target hardware still required.
- PASS — stale results are rejected.
- PASS — active/latest-pending coalescing works; obsolete pending revisions do not execute.
- PASS — cache commit occurs only on the caller/main thread.
- PASS — simulation-time semantics are explicit and tested.
- PASS — required RPM/cache, blood-loss async, and rapid supersession behavior is covered by System Behavior Contracts.
- REQUIRES TARGET HARDWARE — final Windows/Tk event-loop jitter benchmark and <=5 s solve confirmation.

## Scope deliberately not expanded

- No Phase 1 work was started.
- No physiology equations/tolerances were changed.
- No new GUI tabs were built.
- The long-term <500 ms–1 s native-solve target remains tracked performance debt, not a Phase 0 gate.

## Recommended next step

Run the included P0b benchmark/GUI on the actual Windows deployment machine. If the target-hardware UI responsiveness and <=5 s native-solve criteria pass, close Phase 0 and proceed to Phase 1a: audit the legacy JS complication/scenario engine before designing `neoscenarios/`.

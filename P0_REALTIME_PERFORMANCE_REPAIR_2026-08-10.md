# P0 Real-Time Performance Repair — 2026-08-10

## Scope
Repair Item 1 from the Fix Map for `neonatal-modular-patient-GUI-v0.17-coupling-stage7-2026-07-28`.

## Profile finding
The original diagnosis over-weighted the ECMO fixed-point loop. Direct cProfile measurement of a representative 1-second dynamic advance showed the dominant cost was repeated native patient recomputation:

- `DynamicCoupledVaEcmoPatient.advance(1.0)`: 6.14 s wall clock in a 1 s/1 s reduced benchmark configuration.
- `UnifiedNeonatalPatient.snapshot()`: called 6 times per tick.
- Native cardiopulmonary solve (`run_coupled_neonate` / `solve_ivp`): ~5.86 s cumulative.
- ECMO volume-limited / closed-loop solves: ~0.28 s cumulative.

The patient solve is deterministic for unchanged airway settings and clinically unchanged native blood volume, while ECMO support and renal therapy are applied downstream in `snapshot()`. Re-integrating the native cardiopulmonary model repeatedly within the same display tick was therefore redundant.

## Change
Added a native physiology cache in `UnifiedNeonatalPatient` keyed by:

- weight
- configured lung/circulation run duration
- PEEP
- airway opening pressure
- FiO2

The cache also tracks the blood-volume delta used for the solve. Routine continuous fluid drift is allowed to accumulate until `native_physiology_volume_recalc_threshold_ml` (default 0.10 mL) before forcing a fresh native solve.

Immediate cache invalidation remains in place for:

- airway changes
- explicit intravascular input
- blood loss
- sampling loss

ECMO vascular-support changes do not invalidate the native solve because support effects are applied after the native cardiopulmonary solve. Renal controls likewise remain downstream except insofar as their accumulated fluid effect crosses the blood-volume threshold.

## Performance result
Steady-state 1-second advances after the repair measured approximately 0.09-0.11 s wall clock on this sandbox, including the default 12 s lung/circulation configuration. This is below the Fix Map target of 250 ms per simulated second in this environment.

A cache-only exact-volume version first reduced the representative 1 s/1 s tick from 6.14 s to 0.90 s. The 0.10 mL recalc threshold reduced routine steady-state ticks further to ~0.10 s by avoiding a full native re-integration for sub-microliter-to-microliter-scale one-second renal drift.

## Solver tolerance experiment
A trial loosening `solve_ivp` tolerances and increasing `max_step` was rejected. LSODA did not reliably become faster under that combination in the coupled workload, so no integrator-fidelity tradeoff was shipped in this repair. The original circulation solver tolerances remain unchanged.

## Validation completed
- Dynamic coupling/workspace tests: 9 passed.
- Coupled ECMO/patient contract + hydraulic + gas + preload tests: 25 passed.
- ECMO NorthStar benches: 12/12 PASS, zero differences outside tolerance.
- Circulation, lung, ventilator, and gas-exchange NorthStars: PASS.

The full slow patient-coupling regression sweep exceeded the sandbox command timeout and is not claimed as completed here. The source handoff already notes that these pre-existing patient-side tests may require batching.

## Remaining P0 work
1. Run the full patient/kidney/coupling regression suite in batches on the target development machine.
2. Benchmark first-tick latency separately from steady-state latency; the initial native solve remains expensive by design.
3. Add a regression test around native-solve invocation count so future GUI work cannot silently reintroduce six native solves per display tick.
4. Benchmark on the actual deployment hardware.

## Architectural note
The most important lesson from the profile is that the simulation currently mixes two different concepts: a costly finite-duration physiology equilibration solve and a one-second learner-facing clock tick. They should not be treated as equivalent operations. The cache repair makes the existing architecture usable without rewriting physiology, but a future stateful/warm-start native model would be cleaner than repeatedly solving from baseline whenever native conditions materially change.

# Phase 1e — Scenario Engine Primitives Contract

## Purpose
`neoscenarios` is an orchestration layer above the authoritative patient/circuit runtime and below future educator/debrief surfaces. It owns deterministic scenario progression, trigger evaluation, action/fault requests, and event emission. It does **not** own physiology.

## Non-negotiable boundary
Scenario definitions may name a mechanism and provide mechanism parameters. They may not contain arbitrary callbacks or direct patches to learner-visible/internal physiology such as MAP, HR, CVP, PaO2 targets, lactate, or circuit flow. Every mutation crosses `MechanismRegistry` into a named handler implemented by the simulator.

If a mechanism is missing or only partial, validation reports it and runtime invocation emits `scenario.action_unavailable`; the engine does not synthesize a substitute response.

## Primitive set
- `ScenarioDefinition` — ID/version/title, ordered steps, learner actions, provenance metadata.
- `ScenarioStepDefinition` — trigger plus mechanism-backed actions/fault activations.
- `TriggerDefinition` — Phase 1e supports elapsed-time, event, manual, all, and any triggers.
- `ActionDefinition` — action ID, mechanism ID, immutable parameters.
- `FaultDefinition` — fault identity wrapping a mechanism-backed activation action; optional legacy ID preserved for migration provenance.
- `MechanismRegistry` — explicit scenario-to-simulator mutation boundary with available/partial/not-implemented descriptors.
- `ScenarioEngine` — deterministic progression state; emits to the Phase 1d `EventStream`.
- `ScenarioRng` — explicit seeded RNG and draw count.
- `validate_scenario_definition()` — software-capability preflight against the current mechanism registry.

## Current real mechanism adapters
1. `patient.add_intravascular_input` -> `UnifiedNeonatalPatient.add_intravascular_input()`.
2. `ecmo.set_rpm` -> authoritative `EcmoConsoleControls.rpm` through `DynamicCoupledVaEcmoPatient.set_controls()`.
3. `ecmo.set_sweep` -> authoritative `EcmoConsoleControls.sweep_gas_flow_ml_min` through the same control path.

The ECMO adapter intentionally exposes no direct flow setter.

## Trigger semantics
Automatic Phase 1e steps are one-shot. Repeatable steps are allowed only with an explicit manual trigger until recurrence/cooldown semantics are designed. This prevents a persistent true condition from creating an implicit infinite event loop.

Event triggers inspect immutable `EventRecord` history beginning at the scenario start boundary by default, so stale events from setup or a prior case cannot accidentally satisfy a new scenario. The engine reevaluates after an action so a newly emitted event may deterministically fire a subsequent step in the same simulation time.

## Determinism
Every engine instance requires an explicit integer seed. Scenario randomness must use the engine's `ScenarioRng`. A source guardrail test fails if `random` / NumPy random calls appear elsewhere in `src/`.

Determinism here means equal scenario definition + version + seed + ordered external actions/events produces equal orchestration decisions. It does not claim floating-point physiology is bit-identical across every platform.

## Event contract
Scenario primitives emit structured Phase 1d events including:
- `scenario.started`
- `scenario.step_fired`
- `scenario.fault_requested`
- `scenario.action_requested`
- `scenario.action_applied`
- `scenario.action_unavailable`
- `scenario.completed`

Scenario ID and simulation time are carried in event metadata. Wall-clock time remains the `EventRecord.timestamp` field.

## Explicitly not included in Phase 1e
- no port of legacy JS physiology/effect patches
- no production scenario library
- no diagnosis-specific learner buttons/UI
- no scoring/debrief/replay engine
- no educator dashboard/builder
- no objective/completion policy beyond explicit engine completion
- no clinical timing claims from legacy placeholders
- no automatic recurrence/cooldown scheduler
- no new fault physiology merely to make old scenarios runnable

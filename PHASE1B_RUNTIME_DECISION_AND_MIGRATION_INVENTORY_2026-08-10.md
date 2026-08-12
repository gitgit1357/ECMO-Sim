# Phase 1b — Runtime Decision and Migration Inventory

**Date:** 2026-08-10  
**Decision:** **PORT INTENT; RETIRE THE LEGACY JAVASCRIPT RUNTIME**  
**Source audit:** `PHASE1A_LEGACY_JS_ENGINE_AUDIT_2026-08-10.md`  
**Scope:** Record the runtime decision and translate the audited JS knowledge surface into a concrete Python migration ledger. This phase does **not** implement `neoscenarios/`, Phase 1c capability-matrix work, or Phase 1d event-stream infrastructure.

---

## 1. Locked Phase 1b decision

The July-22 V1 RC JavaScript engine is preserved as a read-only behavioral/provenance reference. It will **not** remain an active runtime, API service, hidden fallback, or second authoritative physiology world.

Migration rule:

> Preserve clinical/orchestration intent and test intent. Re-express consequences through the authoritative Python patient/circuit mechanisms. Never transliterate `effects.internal` monitor/physiology patches.

This decision is now explicit and should only be reopened if a future requirement appears that genuinely requires an independently deployed JS runtime. Phase 1a found no such requirement.

## 2. Runtime disposition

| Legacy area | Decision |
|---|---|
| Clinical event state-machine semantics | Port intent |
| Trigger policies / duplicate-fire protection / restore semantics | Port early in Phase 1e |
| Outcome taxonomy: preferred / acceptable / temporizing / ineffective / harmful | Port intent |
| Learner-vs-instructor disclosure separation | Port early |
| Ordered information/lab timing concepts | Port design |
| Scenario runtime pacing/director | Port orchestration semantics; revalidate timing values |
| Debrief/timeline concepts | Feed Phase 1d structured event schema |
| Clinical source / validation governance | Preserve |
| Legacy scenario/action/observation IDs | Preserve as `legacy_id` provenance; use canonical Python IDs going forward |
| `circuit-sandbox.mjs` physiology/hydraulics/gas formulas | Retire |
| `clinical-consequence.mjs` numeric outcome model | Retire |
| `effects.internal` direct numerical patches | Reject |
| Placeholder timing constants | Do not treat as clinical truth |
| Uncontrolled randomness | Reject; use scenario-owned seeded RNG |
| Generic flow-target learner control | Retire/restrict to test setup only |

## 3. Action migration inventory

All **79** audited legacy actions now have an explicit disposition in `PHASE1B_LEGACY_ACTION_MIGRATION_LEDGER.csv`.

Status counts:

- **MISSING_MECHANISM:** 41
- **MISSING_OR_FUTURE_OBSERVATION:** 8
- **MISSING_OR_PARTIAL_INTERVENTION:** 4
- **ORCHESTRATION_DIAGNOSTIC:** 3
- **ORCHESTRATION_OBSERVATION:** 1
- **PARTIAL_BACKEND:** 13
- **READY_EXISTING_CONTROL:** 2
- **READY_EXISTING_MECHANISM:** 1
- **READY_OBSERVATION_FROM_STATE:** 6

Interpretation:

- `READY_EXISTING_MECHANISM` / `READY_EXISTING_CONTROL`: a real authoritative Python mechanism already exists and may later be called by a typed scenario action.
- `READY_OBSERVATION_FROM_STATE`: the true data already exists; Phase 1e/Phase 2 only need a learner-safe observation pathway.
- `PARTIAL_BACKEND`: some real mechanism/state exists, but the full fault/action contract is incomplete.
- `ORCHESTRATION_DIAGNOSTIC` / `ORCHESTRATION_OBSERVATION`: preserve workflow semantics without inventing physiology.
- `MISSING_*`: clinically useful intent, but no authoritative mechanism exists today. These stay explicit backlog items and must not be approximated by direct numeric patches.

### Existing mechanism examples

- `volume-bolus` -> `UnifiedNeonatalPatient.add_intravascular_input()`
- `increase-rpm` -> `EcmoConsoleControls.rpm`
- `increase-sweep` -> `EcmoConsoleControls.sweep_gas_flow_ml_min`
- hemodynamic / pump / oxygenator / gas / renal assessments -> existing patient/circuit state, exposed later through observation mechanisms
- fluid-overload management / CKRT -> existing renal/UF surfaces are partial but real

### Important non-mappings

The ledger intentionally does **not** pretend that an engineering modifier is already a learner-facing clinical mechanism. For example, `PatientModifiers.systemic_resistance_scale` and `pulmonary_resistance_scale` demonstrate backend capability, but vasoplegia/PH treatment remain `PARTIAL_BACKEND` until typed patient/intervention ownership is created.

## 4. Complication-to-mechanism inventory

All **36** legacy complications are also inventoried in `PHASE1B_COMPLICATION_MECHANISM_LEDGER.csv`.

Status counts:

- **MECHANISM_NOT_IMPLEMENTED:** 22
- **PARTIAL:** 13
- **SUPPORTED_CORE_MECHANISM:** 1


This ledger is deliberately conservative. A complication is marked `PARTIAL` when reusable Python mechanics exist but a scenario-addressable fault/pathology state does not. Everything else remains `MECHANISM_NOT_IMPLEMENTED` rather than being faked.

Examples:

- hypovolemia -> supported core volume/preload behavior
- major bleeding -> real blood-loss + replacement mechanisms, but no coagulopathy model
- sweep failure -> real sweep/gas consequences, but no hidden gas-source fault object yet
- oxygenator dysfunction -> real oxygenator/pressure/gas mechanics, but no scenario fault API yet
- vasoplegia / pulmonary hypertension -> engineering modifiers exist, but no authoritative intervention/pathology port yet
- VV recirculation, tamponade, limb ischemia, rhythm/arrest, neurologic/metabolic/abdominal/congenital emergencies -> remain explicit mechanism backlog

## 5. Scenario ID normalization

`PHASE1B_SCENARIO_ID_MIGRATION.csv` assigns a unique canonical Python ID to each of the 28 preserved presets. The original 03A/03B and 04A/04B IDs remain available as `legacy_id` only.

No legacy ID is silently rewritten in the preserved archive.

## 6. Phase 1e build contract created by Phase 1b

When `neoscenarios/` is eventually implemented, it should start with these architectural units, in this order:

1. **Typed action result/outcome taxonomy** — preferred / acceptable / temporizing / ineffective / harmful.
2. **Event state machine** — active state, transitions, time-in-state, resolution, snapshot/restore.
3. **Generic trigger policies** — at-start, time-window, context, action-count, manual; duplicate-fire protection.
4. **Deterministic scenario context** — scenario-owned seeded RNG; no uncontrolled randomness.
5. **Typed mechanism adapters** — scenario actions call current Python mechanisms or explicitly report `mechanism not implemented`.
6. **Learner disclosure boundary** — hidden diagnosis/internal rationale never leaks through learner output.
7. **Observation/diagnostic actions** — read authoritative state or produce point-in-time diagnostic results; never become private physiology engines.
8. **Snapshot/restore** — event/trigger/director state survives restore without duplicate firing.

The Tier-A legacy tests should be mined first when Phase 1e starts. Clinical scenario families should not be ported until their mechanism ledger rows are ready enough to support them honestly.

## 7. Explicit non-goals for Phase 1b

Phase 1b does **not**:

- create a `neoscenarios` package;
- add event-stream code (Phase 1d);
- build the capability matrix (Phase 1c);
- expose new learner controls;
- add or tune physiology;
- port any legacy numeric patch;
- mark unsupported complications as supported merely because a JS scenario once existed.

## 8. Phase 1b exit criteria

| Exit item | Status |
|---|---|
| Explicit runtime decision recorded | **PASS — port intent / retire JS runtime** |
| Legacy JS retained as durable read-only reference | **PASS** |
| No JS API/service/fallback retained | **PASS — decision locked** |
| 79 legacy actions mapped to Python disposition | **PASS** |
| 36 complications mapped to mechanism disposition | **PASS** |
| 28 legacy scenario IDs normalized for future Python use | **PASS** |
| Direct numeric patching explicitly prohibited | **PASS** |
| Placeholder timing values explicitly kept unvalidated | **PASS** |
| Phase 1e architectural migration order defined | **PASS** |
| No Phase 1c/1d/1e runtime code started | **PASS** |

**Phase 1b is complete.**

Next roadmap item: **Phase 1c — build the living capability matrix against actual runtime behavior.**

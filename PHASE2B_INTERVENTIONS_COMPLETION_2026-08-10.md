# Phase 2b — Interventions Completion Record

**Date:** 2026-08-10  
**Primary roadmap:** FIX_MAP v4 Phase 2  
**Status:** COMPLETE — learner intervention surface v1

## Scope
Phase 2b converts the reserved Interventions tab into a real learner surface while preserving the roadmap's formulary-scope guardrail: only authoritative mechanisms already owned by the Python backend are exposed.

### Learner-operable now
1. **Generic intravascular volume input**
   - Calls `UnifiedNeonatalPatient.add_intravascular_input()`.
   - Uses a volume in mL and the existing intravascular-volume ledger.
   - Emits a structured `intervention.applied` event with `mechanism_id=patient.add_intravascular_input`.
   - Does **not** claim crystalloid, packed RBC, plasma, platelet, or other product composition.

2. **CKRT prescription controls**
   - Exposes CKRT blood flow (Qb) and net ultrafiltration rate through existing `EcmoConsoleControls` fields.
   - Emits structured control-change events plus one `intervention.applied` event.
   - Preserves CBC06 activation gating: patient net UF is active only when the ECMO shunt configuration is `CKRT` and CKRT blood flow is greater than zero.
   - A prescription may be stored while inactive; the learner UI labels that state explicitly.

## Explicitly unavailable in Phase 2b
The tab visibly marks the following unavailable rather than simulating them with numeric patches:
- vasoactive / inotrope therapy;
- sedation / analgesia;
- calcium / electrolyte therapy;
- blood-component-specific transfusion.

These remain blocked until the unified patient owns clinically defensible mechanisms and behavior contracts where appropriate.

## Safety / architecture rules preserved
- No intervention writes MAP, HR, PaO2, PaCO2, CVP, flow, or other monitor values directly.
- Flow remains an outcome of circuit/patient state.
- Invalid, negative, NaN, or infinite intervention inputs are rejected.
- No arbitrary clinical maximum/minimum dose thresholds were invented in the GUI.
- Patient Monitor remains read-only.
- Labs, Ventilator, and Scenario Log remain untouched Phase 2 placeholders.

## Verification
Focused headless tests cover:
- authoritative volume-ledger mutation and event emission;
- invalid volume rejection;
- CKRT prescription storage while inactive;
- CKRT UF activation only with CKRT selected and Qb > 0;
- zero-Qb gating;
- invalid CKRT-value rejection.

A real Tk construction/action smoke test also verifies the Interventions page and both learner callbacks construct and execute in the live workspace.

## Roadmap bookkeeping
Phase 0 and Phase 1 remain closed. Phase 2 is the active primary track. Clinical Behavior Contracts remain a parallel discipline and were not advanced in this block.

**Next FIX_MAP v4 item:** Phase 2c — Labs & Diagnostics, preserving ordered-test distinction and frozen sample-time semantics.

## Final verification
Zero-exit fresh batches:
- Phase 2b interventions + workspace/events/dynamic/patient-monitor projection: **21/21 passed**
- volume ledger + renal therapy + CBC06 CKRT net-UF contract: **17/17 passed**
- coupled patient/ECMO time-step + fixed-shunt regression: **26/26 passed**

**Total fresh zero-exit tests: 64 passed, 0 failed.**

Live Tk action smoke under X virtual display: **PASS**. Both the volume and CKRT learner callbacks executed and emitted structured intervention events.

Exact repository collection: **402 tests**.

Source diff versus Phase 2a: exactly one non-generated source file changed — `src/neogui/ecmo_workspace.py`. All patient, ECMO-physics, coupling, kidney, lung, scenario, and event-contract source files remain byte-for-byte unchanged.

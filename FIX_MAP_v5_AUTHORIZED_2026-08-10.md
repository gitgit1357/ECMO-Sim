# Neonatal ECMO Sim Platform — FIX_MAP v5

**Status: AUTHORIZED.** Extends FIX_MAP v4 after Phase 5a–5d. Authorized 2026-08-10 after four review rounds.

## Governing scope
Phase 6 is a learner-information-architecture and act→observe repair only. It touches `src/neogui/` and existing learner projections. It must not reopen physiology, hydraulics, gas exchange, kidney, coupling, CBC behavior, or Phase-5 review disposition. If any Phase-6 item requires new patient/model state, new physiology, a new mechanism, or new clinical semantics, stop that item and move it out of Phase 6 rather than inventing a mechanism.

## Fixed Phase-6 build order
**6a → 6b → 6c → 6d → 6e → 6f → full Phase-6 acceptance → STOP and obtain explicit confirmation before opening Phase 7 or Phase 8.**

## 6a — Shared projection + canonical labels + persistent ribbon
- Rename the prior monitor-specific learner projection to `learner_patient_reading()` and make it the single projection source for learner-facing patient-state values shared by multiple GUI surfaces.
- Console must stop duplicating owned `snapshot.dynamic.displayed.*` reads and consume the same projection as Monitor.
- Persistent ribbon is the third consumer.
- Canonical shared labels include `MAP` and exact `ECMO PATIENT FLOW`; do not shorten the latter.
- Structural verification is two-part and both are required:
  1. behavioral spy/substitution proving Monitor, Console, and ribbon consume `learner_patient_reading()`;
  2. narrow static guard in `ecmo_workspace.py` against direct reads of fields owned by that projection outside the projection itself.
- Before code changes, retain exact pre-Phase-6 pytest node IDs, not merely a count.
- Ribbon is visible on all six pages and shows MAP, SpO2, ECMO PATIENT FLOW, and updating state.
- During native update, ribbon values remain the last committed learner-visible values; do not extrapolate or independently refresh ahead of the committed snapshot.
- Ribbon updating indication and existing compute-status banner consume the same existing workspace-updating source.
- HR and temperature remain omitted because they are not modeled.

## 6b — Ventilator hemodynamic readback
- Add MAP, CVP, native cardiac output to the existing respiratory response panel using the 6a shared projection.
- Do not group ECMO PATIENT FLOW into the CBC07 response panel.
- Keep explicit disclosure: `ECMO PATIENT FLOW may also change with PEEP in the current simulator. That interaction is not a validated CBC07 relationship — the current preload interface uses measured CVP without a transmural-pressure concept, so this response is outside the validated teaching relationship.`
- At the supported reference window size, pressure-control inputs and response panel must be simultaneously visible without vertical scrolling.

## 6c — Interventions live readback
- Add compact MAP, CVP, ECMO PATIENT FLOW, urine output, net fluid, blood-volume-fraction readback beside volume/CKRT controls.
- Controls and readback must be simultaneously visible without vertical scrolling at the reference window size.

## 6d — Labs current context
- Add live `Current patient context` beside gas-order controls.
- It is live context, not frozen order-time state.
- Keep visually/structurally separate from frozen sample-time Ordered Results.
- Order buttons and current context must be simultaneously visible without scrolling; result history may scroll.
- Do not add stored order-context snapshots unless existing data already contains them.

## 6e — Nav attention
- GUI-only ephemeral attention state is permitted; it must not enter physiology, scenario state, scoring, persistence, event records, or clinical logic.
- Labs unread state is a set of result IDs. Indicator clears only after every currently available result contributing to unread state has rendered in Ordered Results.
- CKRT stored-but-inactive is persistent while condition remains true, and is causation-neutral: it can originate from learner action, scenario/educator initialization, or restored state.
- Required test: CKRT stored-but-inactive with zero learner actions must still show the Interventions indicator.
- Pressure-control-applied is not a nav indicator.
- Indicators are informational, not alarm architecture.

## 6f — Accessibility / contrast
- Audit actual foreground/background pairs at actual text size/weight against applicable WCAG AA thresholds.
- Fix contrast failures only; preserve established color meanings.
- Color must not be the sole carrier of state; ACTIVE/INACTIVE/PENDING/RESULT READY and equivalents remain text-identifiable.
- Broader aesthetics are out of scope for Phase 6.

## Act→observe matrix — all rows required
| Page | Learner action | Same-page consequence required |
|---|---|---|
| Console | RPM / sweep / FdO2 / bridge / shunt | Existing Console telemetry + global ribbon |
| Ventilator | PIP / PEEP / RR / Ti / FiO2 | Respiratory response + MAP/CVP/native CO + global ribbon; ECMO PATIENT FLOW not grouped into CBC07 panel |
| Interventions | volume | MAP/CVP/ECMO PATIENT FLOW/net fluid/blood-volume fraction |
| Interventions | CKRT prescription | MAP/CVP/ECMO PATIENT FLOW/urine/net fluid + CKRT active/inactive state |
| Labs | order gas panel | Live current context + clearly separate pending/frozen results |
| Monitor | none | Global ribbon remains visible |
| Scenario Log | none | Global ribbon remains visible |

## Phase-6 closure requirements
- 6a–6f fresh unit tests plus live Tk/Xvfb smoke tests; `test_phase6_*` naming.
- Verify act→observe matrix row by row.
- Completion document includes shared-projection ownership table mapping signal → authoritative learner projection → consuming surfaces.
- Capability matrix changes are GUI-exposure/system rows only; do not promote existing clinical behavior/evidence/implementation as a Phase-6 side effect.
- Written or screenshot before/after walkthrough for Console, Ventilator, Interventions, Labs.
- Baseline provenance: every pre-Phase-6 node ID must still exist and pass; every new node must be named `test_phase6_*`; collection increase fully accounted for by named new nodes. Bounded zero-exit batches are allowed. Timeout is incomplete, never pass/fail.
- Hash manifest for touched files.

## Phase 7 — gated backlog, not started
- 7a read-only event-stream debrief only; no scoring/interpretation.
- 7b first deliverable is to determine whether sufficient immutable historical state/snapshot history exists for replay without re-solving. If not, stop and rescope.
- 7c scoring is explicit hold; requires its own contract-style specification before code.
- 7d educator dashboard/scenario builder is unscoped/deferred.

## Phase 8 — gated visual hierarchy/workspace polish, not started
Opens only after Phase 6 closes. Candidate scope: density, spacing/alignment, typography hierarchy, grouping/rhythm, consistent tile sizes, dead-space reduction, responsive layout, visual emphasis using existing state categories, and screenshot-based before/after review. No physiology, alarm semantics, scoring, new state, CBC changes, trade-dress cloning, or de-emphasis of SIMULATION / TRAINING ONLY.

## Authorization record
Authorized as FIX_MAP v5 effective 2026-08-10. No further design review is required for Phase 6. Any scope/acceptance-criteria change must be justified by an implementation discovery, not another paper-review round.

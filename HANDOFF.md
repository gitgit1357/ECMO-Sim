# ECMO Circuit (neoecmo) — Session Handoff — 2026-07-26/27

Read this first. It's the complete picture of what exists, what's real vs.
provisional, and exactly where to pick back up. CHANGELOG.md has the
turn-by-turn detail; this document is the synthesized state.

## What this is

`neoecmo` is a standalone Python package modeling the physical ECMO
circuit — pump, oxygenator, fixed shunt, bridge, cannulas, gas exchange,
CDI sensor, and the shunt-line hemofilter/CKRT configuration — plus a
consolidated control surface (`ecmo_console.py`) tying every real
learner-adjustable control into one entry point. It is part of a larger
project (internally "Emo Sim") that also includes a separate, older
patient-physiology engine (`neocirculation`/`neolung`/`neokidney`/
`neocoupling`/`neopatient`, 81 tests, pre-existing before this session)
and a still-separate JS complication/scenario engine from an earlier
pivot (not touched this session, not reconciled with either Python
package).

**Test count as of this handoff: 244/244 passing (81 pre-existing +
163 neoecmo), verified fresh immediately before this handoff was
generated. All 12 NorthStar regression snapshots pass.**

## Why it's built this way (read before changing anything)

Two hard-won working principles govern this codebase, established after
an earlier merge attempt spiraled out of control:

1. **One component at a time.** Build each piece standalone, to a
   clinically-relevant (not over-engineered) threshold, verify it in
   isolation with its own tests and a frozen NorthStar regression
   snapshot, and only then wire it into the next thing. If you need to
   add or change a component, follow this pattern: new/changed module +
   tests + (if it's a hydraulic/gas component) a NorthStar snapshot,
   verified standalone before touching anything that depends on it.

2. **Every stage gets a NorthStar snapshot.** Each subsystem has its own
   `ecmo_<name>_regression_bench/` directory: a `run_*.py` that computes
   current behavior, a `compare_*.py` that diffs it against
   `accepted_*.json` within a tolerance, and a README explaining what's
   frozen and why. Changing a default value or model shape requires
   **regenerating and deliberately re-accepting** the snapshot — never
   silently overwrite one. Full-suite regression must be reconfirmed in
   batches after every change (the suite is slow enough — several
   minutes — that running it in one shot sometimes gets cut off by tool
   time limits; split into ~4-test-file batches, as done throughout this
   session).

## Module inventory (src/neoecmo/)

Hydraulic components (standalone, each with its own bench + tests):
- `pump.py` / `pump_bench.py` — RPM-to-flow via a pump head curve;
  RPM never assigns flow directly, it's solved against resistance +
  pressure boundary.
- `oxygenator.py` / `oxygenator_bench.py` — hydraulics only (resistance,
  ΔP, obstruction/clot state, low-flow exposure clock). Gas exchange is
  separate (see below).
- `fixed_shunt.py` / `fixed_shunt_bench.py` — the shunt branch, with a
  `ShuntLineConfiguration` enum (OPEN / HEMOFILTER / CKRT) for the real
  two-stopcock anatomy.
- `bridge.py` / `bridge_bench.py` — the bridge branch, clamp-position
  hydraulics, hard zero when fully closed.
- `cannula.py` / `cannula_bench.py` — return (8Fr) and drain (10Fr)
  cannula hydraulics, empirical quadratic model.
- `tubing_geometry.py` — Hagen-Poiseuille resistance from measured tube
  diameter/length; grounds the shunt/bridge/main-tubing defaults.

Wiring (composes the above into one solvable circuit, in order):
- `main_circuit_series.py` — pump + oxygenator in series.
- `main_circuit_with_shunt.py` — + fixed shunt as a parallel branch
  (used a placeholder patient-path resistance, now superseded).
- `main_circuit_with_shunt_and_bridge.py` — + bridge as a second
  parallel branch (bridge closed by default; verified this exactly
  reproduces the shunt-only stage).
- `patient_path.py` — composes real return tubing + real cannulas + a
  narrow vasculature-only placeholder (see "What's still placeholder"
  below).
- `main_circuit_full.py` — the complete standalone circuit, all three
  branches + real cannulas. Also has
  `solve_bridge_clamp_position_for_target_flow()`, an inverse solver
  (target bridge flow -> clamp position), matching how bridge titration
  actually works clinically (watch flow, adjust clamp — clamp_position
  itself is never a known clinical value).

Gas exchange and sensing:
- `oxygenator_gas_exchange.py` / `gas_exchange_bench.py` — O2 saturation
  transfer and CO2 clearance, separate from oxygenator hydraulics.
  Includes the real Spectrum O2 blender constants
  (`MIN_FDO2`/`MAX_FDO2`/`FDO2_BLENDER_STEP`) and
  `round_fdo2_to_blender_step()`.
- `cdi_sensor.py` — the CDI mixing sensor, at its real confirmed
  position on the drain limb (downstream of the bridge tee, upstream of
  the shunt/transducer T). Blends native venous blood with bridge
  recirculation ONLY — shunt is structurally excluded (enforced by
  signature-inspection tests, not just behavior).

Control surface:
- `ecmo_console.py` — `EcmoConsoleControls` (every real learner control)
  + `run_ecmo_console()` (applies them all, returns the complete solved
  monitor/CDI state in one call). This is the intended entry point for
  any future UI or scenario engine — device specs and pathology state
  are separate pass-through parameters, not part of "controls."

## What's REAL (confirmed directly, not guessed) vs. PROVISIONAL

Every provisional value is flagged in its own module docstring with the
word PROVISIONAL and a note on what it's grounded in. This is the
consolidated list:

**Real, confirmed measurements/specs:**
- Main circuit tubing: 3/8" ID, 8 ft cannula-to-cannula (3 ft pre-pump,
  2 ft pump-to-oxygenator, 3 ft return). Pre-pump limb sub-segments,
  exactly: patient -> 8" -> bridge tee -> 8" -> CDI -> 4" -> venous
  access pigtail -> 6" -> manifold -> 6" -> shunt/transducer T (4-way,
  drain transducer opposite shunt drain) -> 4" -> pump.
- Shunt tubing: 1/16" ID, ~1 ft (without anything installed).
- Bridge tubing: 3/8" ID, ~1 ft.
- Cannula sizing: 10Fr drain, 8Fr return (drain always larger).
- Oxygenator: Eurosets AMG PMP Infant (ECMO-cleared pediatric/infant
  line, <=20 kg). Confirmed minimum flow: 250 mL/min (clot prevention).
- Sweep gas: Spectrum O2 blender, medical air + O2, typically 100% FdO2,
  adjustable 21-100% in 1% steps.
- Shunt line anatomy: two stopcocks; OPEN (connected to each other) /
  HEMOFILTER (disconnected, filter placed between them) / CKRT
  (3-way stopcocks, main flow passes through unaffected, CKRT machine's
  own pigtails tap side ports — drain pigtail upstream, return
  downstream). CKRT is blood-primed on initiation (no volume steal at
  connection) and pulls some (not all) blood from the shunt line via its
  own pump, returning that volume minus only the net-ultrafiltration
  amount removed.
- Real clinical cross-check numbers (bridge closed): ~600 mL/min total
  flow -> ~240 shunt / ~360 patient (35-40% shunt fraction). Used
  throughout to validate the model, most recently reproduced within 10%
  using entirely real component physics (no tuned placeholder) at
  RPM=3000: 630/254/376.

**Provisional (flagged, needs real data to replace):**
- Pump head curve shape (revOlution pump specifics) — order-of-magnitude
  plausible, not manufacturer-validated.
- Oxygenator rated_flow_ml_min (1500) and the O2/CO2 transfer-efficiency
  curve shape — grounded in a comparable device (Quadrox-i Neonatal),
  not the AMG PMP Infant's own (unavailable) spec sheet.
- Drain cannula (10Fr) resistance coefficient — reuses a single-end-hole
  arterial bench figure as a stand-in for what should be a multi-hole
  venous cannula; flagged as a likely overestimate.
- Vasculature-only placeholder resistance (0.3574 mmHg/(mL/min) in
  `patient_path.py`) — back-solved from the real cross-check numbers,
  stands in for actual patient vascular resistance since patient
  physiology isn't coupled in.
- CKRT's own net ultrafiltration rate and blood flow — no defaults
  assumed; these are per-prescription inputs to the console, currently
  demonstrated with illustrative numbers (30 mL/min blood flow, 2 mL/min
  net UF) in tests, not real values from Frank's practice.

## What's NOT built at all

- **Sensors beyond the CDI**: no flow probes, pressure transducers
  (true-vs-measured-vs-displayed distinctions), bubble detector.
- **Heat exchanger.**
- **Cross-branch stagnation/clot-risk tracking** (deliberately deferred
  back at the bridge stage — hydraulics-only was the explicit scope).
- **Real patient physiology coupling.** `neoecmo` never imports
  `neocirculation`/`neolung`/`neokidney`/`neocoupling`/`neopatient` — this
  is enforced by tests, not just convention. Native venous
  saturation/pCO2 are required external inputs to the console; nothing
  in `neoecmo` computes them. Building a `neoecmo` <-> `neopatient`
  coupling layer (mirroring how `neocoupling` sits between heart and
  lung) is a separate, larger future project — discussed and explicitly
  deferred this session in favor of finishing the ECMO circuit control
  surface first.
- **No learner-facing UI on this Python side at all.** Everything is
  verified at the code/test level only.
- **Not reconciled with the earlier JS complication/scenario engine**
  (`clinical-events`, `circuit-sandbox.mjs`, etc. — 147 tests, from
  before the Python rebuild). Two independent, non-integrated tracks
  still exist under this project.

## Two corrected mistakes worth knowing about (both caught and fixed same-session)

1. **CKRT hydraulics** — first built as fully disconnecting the shunt
   line (forcing zero ECMO-driven flow) based on a wrong assumption that
   the stopcocks were simple on/off valves. Corrected after clarification
   that they're 3-way: shunt flow passes through unaffected regardless of
   CKRT being attached. If you see any reference to CKRT "disconnecting"
   the shunt in old context, it's wrong — the corrected model has CKRT
   behaving hydraulically identical to OPEN.
2. **A str_replace edit accidentally deleted a function's return
   statement** while adding the bridge-clamp inverse solver, causing a
   silent `None` return. Caught immediately by the test suite failing
   loudly. Lesson: after any edit that inserts a new function near an
   existing one, re-view the file before assuming the existing function
   is untouched.

## Next steps (in the order they came up, not necessarily priority order)

1. Confirm real AMG PMP Infant rated flow / transfer curve if it ever
   becomes available, replacing the Quadrox-i-based placeholder.
2. Get real CKRT prescription numbers (typical blood flow, typical net
   UF rate) from Frank if this ever needs to look realistic in a
   scenario rather than illustrative.
3. Patient physiology coupling (`neoecmo` <-> `neocirculation`/
   `neopatient`) — the big one. Needs its own scoping session.
4. Additional sensors (pressure transducers, bubble detector) if
   scenario work needs them.
5. Reconciling with the JS complication engine, or deciding this Python
   circuit replaces/feeds it rather than living alongside it forever.
6. Learner-facing UI, whenever there's something worth putting a UI on.

## How to verify this handoff yourself

```bash
cd neonatal-modular-patient
pip install -e . --break-system-packages
pip install pytest scipy --break-system-packages
python3 -m pytest tests/ -q
```
Expect 244 passed. If your environment's test runner times out on the
full suite in one shot (this session's did, repeatedly, on the
pre-existing non-ECMO tests which are slow), split into batches of ~4
files at a time — see CHANGELOG.md entries for the exact batching used
throughout.

To verify all NorthStar snapshots:
```bash
for d in ecmo_*_regression_bench; do
  python3 "$d"/compare_*.py
done
```
Expect 12 "PASS" lines, zero failures.

---

## 2026-08-10 Phase 1a legacy JS audit note

The older JavaScript scenario/complication branch referenced elsewhere in this handoff was recovered from the preserved July 22 V1 RC archive and audited directly. The best preserved release has 525/525 passing Node tests, not 147; the older 147 figure is stale or refers to an earlier checkpoint. See `PHASE1A_LEGACY_JS_ENGINE_AUDIT_2026-08-10.md` for the full inventory and migration recommendation. No JS runtime has been integrated into the Python rebuild as part of this audit.

## 2026-08-10 — Phase 1b decision

Phase 1b is closed. The legacy JavaScript runtime will be **retired as an active engine**; its clinical/orchestration/test intent will be migrated into the Python architecture. The preserved JS archive remains a read-only behavioral/provenance reference. See `PHASE1B_RUNTIME_DECISION_AND_MIGRATION_INVENTORY_2026-08-10.md`, `PHASE1B_LEGACY_ACTION_MIGRATION_LEDGER.csv`, `PHASE1B_COMPLICATION_MECHANISM_LEDGER.csv`, and `PHASE1B_SCENARIO_ID_MIGRATION.csv`. No Phase 1c/1d/1e runtime code was started in Phase 1b.

## Phase 1c capability-matrix correction — 2026-08-10

Phase 1c audited the actual Python runtime/test surface and created `CAPABILITY_MATRIX.md` plus CSV/JSON mirrors as the living capability-status index. The matrix distinguishes Implemented, Integrated, GUI-exposed, Test coverage, Clinical/behavior validation, and Learner-operable rather than treating those as interchangeable. Key corrections include: the ECMO workspace is the only functional GUI page today; the other five tabs are reserved shells, VA ECMO is integrated while VV ECMO patient coupling is not, ventilator rate/mode/Ti remain fixture-only, myocardial failure remains explicitly unvalidated, CKRT prescription control is incomplete, and Python scenario/event/debrief infrastructure is not yet implemented. See `PHASE1C_CAPABILITY_MATRIX_COMPLETION_2026-08-10.md` for audit details. No source or test code was changed during Phase 1c.

---

## 2026-08-10 — Phase 1d structured event-record contract
Phase 1d added `src/neoevents/` and wired the current `EcmoWorkspaceModel` control-change path into one append-only machine-readable `EventStream`. Stable schema: `timestamp, event_type, source, target, action, old_value, new_value, revision, metadata`. Simulation time is kept distinct in metadata. No scenario engine/scoring/Scenario Log GUI was started. Phase 1b migration ledgers are now embedded as backing data in `CAPABILITY_MATRIX.json`; standalone CSVs were moved to `archive/phase1b_ledgers/` as historical snapshots. See `EVENT_RECORD_CONTRACT.md` and `PHASE1D_EVENT_RECORD_COMPLETION_2026-08-10.md`.

Phase 1d fresh verification: exact-tree collection 312 tests; focused event/workspace/async/cache 20/20 pass; dynamic coupling/time-step/contract 15/15 pass; hydraulic/gas/MAP/preload 22/22 pass; ECMO component/console subset 123/123 pass.

## 2026-08-10 — Phase 1e scenario-engine primitives
Phase 1e added `neoscenarios` as a deterministic orchestration layer over the Phase 1d event stream and explicit simulator mechanisms. Scenario actions/faults now cross a `MechanismRegistry`; definitions cannot directly patch physiology/monitor values. Seeded `ScenarioRng`, trigger primitives, capability preflight validation, and real adapters for intravascular volume, RPM, and sweep are covered by focused tests. No production scenario library, new clinical fault physiology, scoring/debrief, or learner scenario GUI was added. See `SCENARIO_ENGINE_PRIMITIVES_CONTRACT.md` and `PHASE1E_SCENARIO_ENGINE_PRIMITIVES_COMPLETION_2026-08-10.md`.

## 2026-08-10 — Tier-A orchestration/disclosure semantics ported
Ported architecture-defining legacy behavior into `neoscenarios`: trigger lifecycle and snapshot/restore, eligibility/release director semantics, time-in-state event machines, learner/instructor disclosure separation, frozen observations, and a headless hypovolemia vertical slice using authoritative blood-loss/volume mechanisms. No legacy JS physiology or direct numeric patches were ported. See `TIER_A_ORCHESTRATION_AND_DISCLOSURE_CONTRACT.md` and `TIER_A_PORT_COMPLETION_2026-08-10.md`.

## 2026-08-10 — Ready scenario catalogs + first production-structured family
Post-Phase-1e work registered only currently authoritative mutation mechanisms, promoted six read-only state observations, added a mechanism-gated fault catalog with hypovolemia as the sole fully supported legacy complication, and added canonical `lowflow-hypovolemia` (`lf-01-preload`) as the first production-structured scenario family member. Clinical magnitudes remain behavior-contract pending. Learner disclosure was hardened so scenario IDs and scenario-engine internal mechanism actions cannot leak hidden diagnoses. See `READY_MECHANISM_AND_FIRST_SCENARIO_FAMILY_CONTRACT.md` and completion record.

## 2026-08-10 — Source-tag disclosure closure
The first ready scenario family's remaining learner-event provenance leak was closed. `learner_event_view()` now normalizes the internal source tag `scenario-engine` to learner-safe `system`, while instructor/debrief views retain the original source unchanged. See `SOURCE_TAG_DISCLOSURE_CLOSURE_2026-08-10.md`.

## 2026-08-10 — First Clinical Behavior Contract: hypovolemia / preload-limited low flow
Added `cbc.lowflow.hypovolemia.v1` as the first formal Clinical Behavior Contract. The automated contract uses a moderate, non-chattering 2200-RPM VA-ECMO baseline and a 15% modeled-blood-volume loss as a stable regression stimulus. Required directional behavior: preload, patient-directed ECMO flow, MAP, and CVP decrease; drainage pressure becomes more negative; equal intravascular replacement approximately restores baseline; escalating RPM to 3000 while still volume-depleted drives more-negative drainage pressure/chatter without materially improving patient flow or restoring baseline MAP. The 15% stimulus is explicitly not a validated neonatal hemorrhage/treatment threshold. Automation is passing; expert clinical review remains a separate status. See `clinical_behavior_contracts/HYPOVOLEMIA_PRELOAD_LOW_FLOW_V1.md`.

## 2026-08-10 — CBC02 complete sweep-gas failure
- Added `cbc.ecmo.sweep-gas-failure.v1` using CBC01 as the locked behavior-contract template.
- Found and repaired a narrow zero-sweep defect: zero gas flow no longer permits continued membrane O2 addition; CO2 removal was already correctly lost.
- Nonzero sweep behavior is unchanged: sweep remains the dominant CO2 control while FdO2 remains the principal modeled O2 control.
- CBC02 explicitly documents the current coupled-patient native-venous-saturation limitation and does not claim a patient pO2 response that the model cannot yet expose reliably.
- Capability matrix remains the sole living status source.

## 2026-08-10 — CBC03 oxygenator dysfunction
Added `cbc.ecmo.oxygenator-dysfunction.v1` using the locked CBC template. The contract intentionally separates oxygenator blood-path obstruction from membrane gas-transfer impairment: at fixed RPM, hydraulic obstruction raises oxygenator delta-P and reduces total/patient ECMO flow; at fixed blood flow/gas settings, reduced transfer capacity worsens post-oxygenator O2 and CO2 performance. No universal delta-P threshold, clot percentage, or one-to-one pressure/exchange relationship is asserted. No physiology source change was required. Also documented the CBC02 conversational 760-vs-450 pO2 wording correction; packaged CBC02 behavior/tests were unaffected.

## 2026-08-10 — CBC03 oxygenator dysfunction
Added `cbc.ecmo.oxygenator-dysfunction.v1` using the locked CBC template. The contract intentionally separates oxygenator blood-path obstruction from membrane gas-transfer impairment: at fixed RPM, hydraulic obstruction raises oxygenator delta-P and reduces total/patient ECMO flow; at fixed blood flow/gas settings, reduced transfer capacity worsens post-oxygenator O2 and CO2 performance. No universal delta-P threshold, clot percentage, or one-to-one pressure/exchange relationship is asserted. No physiology source change was required. Also documented the CBC02 conversational 760-vs-450 pO2 wording correction; packaged CBC02 behavior/tests were unaffected.

## 2026-08-10 — CBC04 ongoing major bleeding / hemorrhage
Added `cbc.patient.ongoing-major-bleeding.v1` over the authoritative patient volume ledger. The contract models ongoing loss as serial `record_blood_loss()` events: cumulative loss progressively lowers preload, patient-directed ECMO flow, MAP, and CVP while making drainage pressure more negative; partial replacement improves but does not resolve the deficit when input remains behind loss; a subsequent loss event resumes deterioration; once no further loss occurs, replacing the remaining net deficit restores the isolated baseline in the same mutable patient object. No persistent bleeding-rate/hemostasis state, coagulation/platelet physiology, RBC-mass loss, component transfusion, or surgical source control is claimed. If those mechanisms are later added, CBC04's cessation/recovery branch must be retested through them. CBC03 also received an append-only clarification that its current restoration branch is pure-function determinism and must be retested if oxygenator dysfunction becomes mutable state.


## 2026-08-10 — CBC05 split / CBC05A drainage-path resistance

CBC05 was split rather than forcing kink, common obstruction, and position-sensitive maldrainage through one primitive. CBC05A now protects the executable patient drainage-path resistance signature. CBC05B common pre-pump obstruction remains blocked because the existing resistance does not participate in the branched flow solve. CBC05C position-sensitive maldrainage remains blocked pending explicit position state. See `clinical_behavior_contracts/DRAINAGE_PATH_RESISTANCE_V1.md`.

## 2026-08-10 — CBC06 CKRT net-UF contract
- VA differential-hypoxemia CBC candidate was blocked: current Python VA coupling has no distinct upper/lower-body oxygenation or mixing-point state; no surrogate was introduced.
- Added `cbc.ecmo.ckrt-net-ultrafiltration.v1` using the existing coupled CKRT fluid-removal substrate.
- Fixed coupled CKRT UF gating so patient fluid removal occurs only when shunt configuration is CKRT and CKRT blood flow is > 0, matching the lower-level fixed-shunt rule.
- CBC06 validates active-UF divergence from a matched zero-UF control, UF stop behavior, and same-patient matched-counterfactual recovery after authoritative fluid replacement.
- CKRT solute clearance/dose, anticoagulation, access pressures/recirculation, and learner prescription controls remain not modeled.

## 2026-08-10 — CBC07 positive airway pressure / native hemodynamic coupling
Added `cbc.patient.positive-airway-pressure-hemodynamics.v1` over the authoritative unified-patient PEEP input. The contract protects a graded native response in which higher PEEP lowers native cardiac output and MAP while measured CVP rises without a blood-volume increase; same-patient PEEP reversal returns the equilibrium to baseline. A direct VA-coupled probe found that the current ECMO preload solver consumes absolute CVP and lacks a transmural/intrathoracic-pressure boundary, so PEEP-to-ECMO drainage behavior is explicitly BLOCKED rather than legitimized with a surrogate. No runtime physiology source change was made.

## 2026-08-10 — CBC08 ECMO FdO2 oxygen-fraction control
Added `cbc.ecmo.fdo2-oxygen-fraction-control.v1` over the existing learner-operable ECMO FdO2 control. Contract probing found a real internal O2-state defect: post-oxygenator saturation and pO2 were generated by separate approximations and could contradict each other. The narrow repair keeps the existing provisional pO2 transfer model as the single outlet O2 state and derives saturation from it through the inverse of the existing Hill relationship. With fixed nonzero sweep, lower FdO2 now lowers the coherent post-oxy O2 state while pCO2 clearance and hydraulics remain unchanged. Coupled-patient FdO2 behavior remains blocked because the current patient-to-ECMO adapter uses arterial saturation as a temporary venous surrogate; no surrogate correction was introduced. See `clinical_behavior_contracts/FDO2_OXYGEN_FRACTION_CONTROL_V1.md` and `CLINICAL_BEHAVIOR_CONTRACT_08_COMPLETION_2026-08-10.md`.

## 2026-08-10 — CBC09 bridge recirculation / flow diversion
CBC09 (`cbc.ecmo.bridge-recirculation-flow-diversion.v1`) is automated/passing; expert review remains separate. Probing found and repaired a bridge target-flow inverse-solver defect: the final returned operating point now preserves the same live patient pressure/resistance boundary used during clamp root-finding. CBC09 protects target-flow accuracy, patient-flow/MAP diversion, branch conservation, and bridge-induced venous-CDI mixing. Exact bridge target values remain regression fixtures, not clinical prescriptions. See `CLINICAL_BEHAVIOR_CONTRACT_09_COMPLETION_2026-08-10.md`.

## 2026-08-10 — CBC10 fixed-shunt configuration / hemofilter hydraulics
Added `cbc.ecmo.fixed-shunt-configuration.v1` over the existing OPEN / HEMOFILTER / CKRT fixed-shunt configurations. CBC10 protects the hydraulic distinction that inline HEMOFILTER resistance reduces shunt diversion and slightly redistributes flow toward the patient branch; `scuffing_active` itself is hydraulically neutral; CKRT remains hydraulically equivalent to OPEN in the current 3-way side-port model. Hemofilter net-fluid removal is explicitly BLOCKED in the coupled patient because the lower-level helper uses a provisional default rate, no clinically bounded learner prescription exists, and the coupled coordinator does not hand that rate into the patient volume ledger. No source-model changes were made. See `clinical_behavior_contracts/FIXED_SHUNT_CONFIGURATION_V1.md` and `CLINICAL_BEHAVIOR_CONTRACT_10_COMPLETION_2026-08-10.md`.

## 2026-08-10 — Phase 2 resumed / Phase 2a Patient Monitor

FIX_MAP v4 roadmap tracking was explicitly reset after the CBC campaign: Phase 0 and Phase 1 remain closed; Clinical Behavior Contracts remain an ongoing parallel discipline, not numbered-phase progress. Phase 2 is now the active primary track.

Phase 2a Patient Monitor is implemented as a read-only/dumb display over the authoritative workspace snapshot. It reuses the existing dynamic learner-display path where available and does not create physiology. HR, patient temperature, and waveforms remain explicitly unavailable rather than synthesized. See `PHASE2A_PATIENT_MONITOR_COMPLETION_2026-08-10.md` and the authoritative `CAPABILITY_MATRIX.*`.

## 2026-08-10 — Phase 2b Interventions
FIX_MAP v4 remains the primary track. The reserved Interventions tab is now a real learner surface exposing only mechanisms the Python backend already owns: generic intravascular volume input through `UnifiedNeonatalPatient.add_intravascular_input()` and CKRT blood-flow/net-UF prescription through existing ECMO controls. CKRT UF remains gated by CKRT shunt selection plus Qb > 0, preserving CBC06. Vasoactive/inotrope therapy, sedation/analgesia, calcium/electrolytes, and blood-component-specific transfusion remain visibly unavailable rather than being represented by direct monitor-value patches. Labs, Ventilator, and Scenario Log remain pending Phase 2 work. See `PHASE2B_INTERVENTIONS_COMPLETION_2026-08-10.md` and the authoritative `CAPABILITY_MATRIX.*`.

## 2026-08-10 — Phase 2c Labs & Diagnostics
FIX_MAP v4 remains the primary track. Phase 2c replaces the Labs & Diagnostics shell with a learner-orderable point-in-time diagnostic workflow. Results freeze at collection time, use separate simulation-time availability, and emit distinct ordered/available structured events. Initial panels are a deliberately partial patient arterial gas (PaO2/PaCO2/SaO2 only) and post-oxygenator gas assessment. Unsupported analytes are not fabricated. The 30-second GUI turnaround is an orchestration placeholder, not clinical truth. Next numbered roadmap item: Phase 2d Ventilator.

## 2026-08-10 — Phase 2d Ventilator
FIX_MAP v4 remains the primary track. Phase 2d promotes the deterministic pressure-control ventilator from a bench-only fixture into production backend code and replaces the Ventilator shell with a learner-operable page. PIP/PEEP/rate/Ti/FiO2 now drive the authoritative lung/cardiopulmonary solve through `AirwayPort`; the async native worker reconstructs these settings from primitive inputs. Unified snapshots expose modeled RR/VT/minute ventilation/mode, and learner ventilator changes emit structured events. Native/spontaneous breathing remains the default. CBC07's blocked PEEP-to-ECMO drainage/transmural-preload limitation remains explicitly unresolved. Next numbered roadmap item: Phase 2e Scenario Log.

## 2026-08-10 — Phase 2d verification bookkeeping correction
Independent verification confirmed the Phase 2d workspace/Monitor/Interventions/Labs bucket is 27/27 rather than the documented 25/25. Correct fresh Phase 2d total: 73 passed, 0 failed. Documentation arithmetic only; no runtime/source correction required.

## 2026-08-10 — FIX_MAP v4 Phase 2 CLOSED (Phase 2e Scenario Log)
Phase 2e replaced the Scenario Log reserved shell with a read-only learner timeline over the canonical Phase 1d EventStream. The GUI reuses Tier-A `learner_event_view` disclosure; hidden diagnosis-bearing/internal scenario events remain withheld while instructor/debrief provenance remains unchanged. Fresh Phase 2e verification: 81/81 zero-exit tests plus live Tk/Xvfb disclosure smoke. Exact tree: 418 collected tests. Source scope from v0.18.3: `src/neogui/scenario_log.py` new, `src/neogui/ecmo_workspace.py`, and `src/neogui/__init__.py`; no physiology/coupling/scenario/event-schema changes. Capability matrix remains sole living status authority at 81 rows with 79/36/28 backing data. FIX_MAP v4 Phase 2 is now closed; next numbered phase is Phase 4 behavior-first physiology fidelity, with myocardial dysfunction explicitly named by the roadmap as the first known failure that has earned investigation.

## 2026-08-10 — FIX_MAP v4 Phase 4a myocardial dysfunction
The roadmap-named myocardial dysfunction gap was re-investigated. The original v0.3.0 under-response had already received a v0.4.0 physiology correction (ventricular source resistance + nonlinear passive stiffness); current severe LV/RV failure profiles are directionally strong, so no new equation rewrite was justified. The remaining gap was integration: LV/RV contractility is now a real `MyocardialFunctionPort` input to the unified cardiopulmonary solve, included in native cache/async signatures and exposed to scenarios as `patient.set_myocardial_function`. CBC11 (`cbc.patient.myocardial-dysfunction.v1`) is automated/passing; exact contractility-scale to clinical-severity mapping remains expert-review pending. No learner GUI control or inotrope mechanism was added.

## 2026-08-10 — FIX_MAP v4 Phase 4b oxygenator/cannula fidelity disposition
Phase 4b re-reviewed the roadmap-named oxygenator proxy and cannula resistance against CBC03/CBC05A and the underlying hydraulic tests. Focused verification passed 30/30. No additional physiology complexity was earned: the current reduced-order oxygenator behavior is retained with device-specific transfer/Delta-P limits disclosed, and the current patient drainage-path resistance model is retained for CBC05A. Common pre-pump obstruction and position-sensitive maldrainage remain explicitly blocked until real mechanisms exist; no surrogate knobs were introduced. No `src/` or `tests/` files changed. Next Phase 4 primary-track item: phased CKRT scope review.

## 2026-08-10 — Phase 4c CKRT scope disposition / Phase 4 closure
Phase 4c revalidated the existing CKRT Qb/net-UF pathway (CBC06 + Phase 2b controls + fixed-shunt semantics) at 35/35 focused passes and concluded that no additional CKRT model complexity is currently earned. Real Qb/net-UF behavior remains supported; solute clearance/dose, device/access pressures, anticoagulation, alarms/state machine, circuit-volume effects, and clinically validated prescription bounds remain deferred. Historical CBC06 text saying learner CKRT controls were absent predates Phase 2b and is superseded for current status by the living capability matrix. This closes the final specifically named FIX_MAP v4 Phase 4 scope item; Phase 4 is now CLOSED and Phase 5 is the next numbered primary track. See `PHASE4C_CKRT_SCOPE_DISPOSITION_2026-08-10.md`.

## 2026-08-10 — Phase 5a positioning / claims boundary
Phase 5 is now active after Phase 4 closure. Added `PRODUCT_POSITIONING_AND_CLAIMS_BOUNDARY.md` and locked the project intent to education/simulation training, with a claims evidence ladder that separates runtime implementation, regression, CBC behavior, expert clinical review, device/institution evidence, and later commercial/legal/regulatory review. The learner workspace now visibly labels itself `SIMULATION / TRAINING ONLY`; this is an intended-use statement, not a legal/regulatory classification claim. The capability matrix remains the current status authority. Next FIX_MAP v4 work is functional UX architecture review (alarms, control placement, visibility/feedback, latency), separate from cosmetic polish. See `PHASE5A_POSITIONING_CLAIMS_COMPLETION_2026-08-10.md`.

## 2026-08-10 — Phase 5b functional UX architecture
Phase 5b keeps UX work functional rather than cosmetic. Existing low-volume/low-flow/negative-P1/chatter messages are explicitly labeled `SIMULATOR ADVISORIES • NOT DEVICE-VALIDATED`; no device-alarm priority, threshold, acknowledge, silence, audio, or bubble-alarm semantics were invented. Global Space/Up/Down ECMO shortcuts are now gated to the ECMO page and suppressed while editing. A global `PHYSIOLOGY UPDATING • SIM TIME PAUSED` header makes P0/P0b async latency semantics visible from every tab. See `PHASE5B_FUNCTIONAL_UX_ARCHITECTURE_2026-08-10.md`. Next Phase 5 item: broader validation readiness / expert-review queue.

## 2026-08-10 — Phase 5c validation readiness
Added `VALIDATION_REVIEW_QUEUE.json/.md`, derived one-to-one from all 11 current CBCs. Seven Priority-A contracts are tied to learner-operable mechanisms and are queued before four Priority-B headless/indirect contracts. Every item names review domains, concrete review questions, evidence boundaries, and an external-training gate. The queue is deliberately not a competing status ledger; `CAPABILITY_MATRIX.json` remains authoritative and no CBC is promoted to expert-reviewed by this phase. See `PHASE5C_VALIDATION_READINESS_COMPLETION_2026-08-10.md`.

## 2026-08-10 — Phase 5d Priority-A evidence review started

FIX_MAP v4 remains the primary roadmap. Phase 5d begins the Priority-A evidence/expert-review packet sequence. CBC01 (`cbc.lowflow.hypovolemia.v1`) now has `validation_packets/CBC01_HYPOVOLEMIA_PRELOAD_EVIDENCE_REVIEW_2026-08-10.md`. External evidence supports the core directional preload/drainage teaching relationship, but no CBC01 numeric regression stimulus or threshold was promoted to a neonatal bedside claim. Capability-matrix status is now "external evidence packet complete; expert sign-off pending." The current roadmap status overlay is `ROADMAP_CURRENT_STATUS_2026-08-10.md`; `FIX_MAP_v4.md` itself remains unchanged.


## 2026-08-10 — Phase 5d Priority-A Packet 02
CBC02 Sweep-Gas Failure external evidence review is complete; expert sign-off remains pending. Evidence review added one important interpretation guardrail: zero-sweep O2/CO2 boundary assertions are sustained/post-transient steady-state behavior because residual gas washout is not dynamically modeled. No physiology or acceptance tolerance changed. See `validation_packets/CBC02_SWEEP_GAS_FAILURE_EVIDENCE_REVIEW_2026-08-10.md`.


## 2026-08-10 — Phase 5d CBC06 evidence packet
- Added `validation_packets/CBC06_CKRT_NET_ULTRAFILTRATION_EVIDENCE_REVIEW_2026-08-10.md`.
- CBC06 remains automated/passing; external evidence packet complete; expert sign-off pending.
- Corrected stale pre-Phase-2b wording: learner CKRT Qb/net-UF controls are implemented.
- No CBC06 physiology/tolerance/regression-stimulus change.
- FIX_MAP v4 unchanged; Phase 5d remains the active primary track.


## 2026-08-10 — Phase 5d CBC07 evidence packet
- Added `validation_packets/CBC07_POSITIVE_AIRWAY_PRESSURE_HEMODYNAMICS_EVIDENCE_REVIEW_2026-08-10.md`.
- CBC07 remains automated/passing; external evidence packet complete; expert sign-off pending.
- Evidence review explicitly narrows the monotonic CO/MAP response to the simulator canonical isolated regression path; real pediatric/neonatal response to PEEP is heterogeneous and may be modest.
- Corrected stale pre-Phase-2d text: learner pressure-control ventilator controls are implemented.
- PEEP-to-ECMO drainage remains blocked pending a transmural preload interface.
- Validation queue bookkeeping corrected for CBC01/CBC02 evidence-complete statuses.
- No CBC07 physiology/tolerance/regression-stimulus change. FIX_MAP v4 remains unchanged.


## 2026-08-10 — Phase 5d CBC08 evidence packet
- Added `validation_packets/CBC08_FDO2_OXYGEN_FRACTION_EVIDENCE_REVIEW_2026-08-10.md`.
- CBC08 remains automated/passing; external evidence packet complete; expert sign-off pending.
- Evidence supports the FdO2 oxygenation-control vs sweep CO2-control distinction and the lack of a blood-side hydraulic role for an FdO2-only change.
- Exact transfer curves, probe values, Hill constants, and device-specific oxygenation magnitudes remain regression-only/device-validation pending.
- Coupled-patient FdO2 behavior remains blocked until a true central-venous oxygen state exists.
- No CBC08 physiology/tolerance/regression-stimulus change. FIX_MAP v4 remains unchanged.

## 2026-08-10 — Phase 5d CBC09 external-evidence review
CBC09 (`cbc.ecmo.bridge-recirculation-flow-diversion.v1`) external evidence packet is complete; expert sign-off remains pending. ELSO circuit guidance directly supports the total-circuit-flow versus patient-directed-flow distinction when a bridge is opened during VA weaning. Venous-CDI saturation contamination is supported as a recirculation principle; exact bridge-specific CDI pCO2/magnitude claims remain inferential/unvalidated. No physiology/source behavior changed. See `validation_packets/CBC09_BRIDGE_RECIRCULATION_FLOW_DIVERSION_EVIDENCE_REVIEW_2026-08-10.md`.

## 2026-08-10 — Phase 5d CBC10 evidence review
- CBC10 Fixed-Shunt Configuration external evidence packet complete; expert sign-off pending.
- Priority-A external evidence packet pass is complete (7/7).
- No physiology/runtime source changes in this packet.
- Next primary Phase-5 work is consolidated human expert disposition / external-training readiness gating, not opportunistic model expansion.


## 2026-08-10 — Single-reviewer clinical review (project author, practicing ECMO specialist)
The project author, a practicing ECMO specialist, reviewed all 11 current Clinical Behavior Contracts against bedside ECMO practice. This is a single-reviewer clinical review, not independent external expert review — the reviewer has a direct relationship to the project. It moves the human-review gate from "expert review pending" to "single-reviewer clinical review complete, independent review pending" for all 11 CBCs. Historical evidence packets/completion records remain unchanged as point-in-time provenance. This review does not validate blocked/unimplemented mechanisms, device-specific quantitative performance, institutional policy, regulatory status, or commercial/legal/IP claims. Independent external review by the facility ECMO educator is planned and required before external-training/go-live.


## 2026-08-10 — Phase 5e external-review readiness
Prepared a focused independent clinical-review packet for the planned facility ECMO educator. The current build remains blocked from external-training/go-live until all 11 CBCs receive independent dispositions and any rejected items are remediated. This does not alter the prior single-reviewer clinical review or any physiology/runtime behavior.


## 2026-08-10 — Phase 5f commercial/regulatory/IP review readiness
Prepared formal-review readiness artifacts grounded in current official FDA, U.S. Copyright Office, and USPTO source categories. No legal/regulatory/IP conclusion is claimed. External clinical, regulatory, legal/IP, and facility approvals remain separate gates.


## 2026-08-10 — Phase 5g release documentation polish
Updated the repository front door and package metadata to the current integrated v0.21.0 simulator, added release-readiness gating, and removed stale top-level claims that described the project as the old standalone v0.3 circulation engine. Historical stage documents remain unchanged as provenance. No runtime source behavior changed.

## 2026-08-11 — FIX_MAP v5 Phase 6 complete / mandatory stop gate
Phase 6 is CLOSED. The learner-information-architecture and act→observe work passed 17/17 fresh Phase-6 tests under live Tk/Xvfb, including all 7 act→observe rows. Exact baseline accounting is complete at 497/497 original nodes: 434 were freshly re-verified during closure and 63 exact nodes are backed by explicit direct/bounded zero-exit results recorded in the immediately preceding Phase-6 continuation handoff; no timeout was converted into a pass. Final collection is 514 nodes = 497 preserved baseline + 17 named `test_phase6_*` additions, with zero missing baseline nodes. The capability matrix is 99 rows and Phase-6 additions remain GUI/system exposure only. No physiology/CBC behavior was reopened. See `PHASE6_COMPLETION_2026-08-11.md` and `PHASE6_BASELINE_VERIFICATION_LEDGER_2026-08-11.*`. Per FIX_MAP v5, STOP here and obtain explicit project-owner confirmation before opening Phase 7 or Phase 8.


## 2026-08-11 — FIX_MAP v5 Phase 7 closed at authorized boundary
Project-owner authorization opened Phase 7 after Phase 6 closure. Phase 7a is complete: the learner-facing Scenario Log is now presented as a read-only **Debrief — Event Timeline**, still projected from the canonical immutable EventStream through Tier-A disclosure, with no scoring, grading, diagnosis, interpretation, recommendation, or state mutation. Phase 7b completed its required first-deliverable audit and **failed the replay gate**: the current architecture retains canonical event history but not sufficient immutable time-indexed WorkspaceSnapshot/coupled-state history for faithful replay without re-solving. Replay implementation therefore STOPPED and requires a separate historical-snapshot/replay contract. Phase 7c scoring remains HOLD; Phase 7d educator dashboard/scenario builder remains deferred. Current collection is 519 = 514 preserved Phase-6 nodes + 5 Phase-7 nodes, with 0 missing Phase-6 nodes. Focused live-Tk/touched acceptance passed 29/29 and broader affected workspace/event regression passed 43/43. Monolithic full-suite timeout is recorded as incomplete, not pass/fail. See `PHASE7_COMPLETION_2026-08-11.md` and `PHASE7_7B_REPLAY_CAPABILITY_AUDIT_2026-08-11.md`.


## 2026-08-11 — FIX_MAP v5 Phase 8 complete
Phase 8 visual hierarchy/workspace polish is complete. Presentation-only changes improve default proportions, responsive navigation density, typography hierarchy, telemetry/card consistency, cross-page gutters, and Console grouping. `SIMULATION / TRAINING ONLY`, existing state-category colors, clinical values, physiology, alarm semantics, scoring holds, and model/scenario state are unchanged. Collection is 527 = 519 preserved Phase-7 nodes + 8 Phase-8 nodes with 0 missing. Focused visual-boundary acceptance passed 18/18; broader affected GUI/workspace/event regression passed 64/64. See `PHASE8_COMPLETION_2026-08-11.md` and `PHASE8_VISUAL_REVIEW_2026-08-11.md`.


## 2026-08-11 — Post-Fix-Map-v5 audit superseding closure notice
For Fix Map v5 closure/provenance, `FIX_MAP_V5_FINAL_AUDITED_HANDOFF_2026-08-11.md` supersedes the Phase-6/7/8 summary claims in this historical handoff. In particular, the standalone package does not independently establish the individual Phase-7/Phase-8 opening checkpoints; older wording asserting project-owner authorization is historical assertion, not package-verifiable provenance. Test subtotals are governed by the named `AUDIT_*_NODE_MANIFEST_2026-08-11.txt` files and the audit findings. No product code, CBC gating/tolerance, or test behavior changed during the audit.


## 2026-08-11 — Fix Map v6 Phase 9a.0 / 9b.0 audits complete
Fix Map v6 was authorized as the governing roadmap with only 9a.0 and 9b.0 opened. 9a.0 concluded PROCEED under a constrained design that consolidates/exposes existing CVP, volume-ledger, pleural-pressure, and native mixed-venous authorities at the unified-patient boundary rather than creating a second venous solver. 9a.1+ remains not authorized. 9b.0 concluded existing scenario primitives already satisfy the typed scenario→mechanism activation contract; no new generalized 9b.1 surface is needed. Phase 10+ remains unopened. No `src/` or test behavior changed; collection remains 527.


## 2026-08-11 — Fix Map v6 Phase 9a implementation complete
Phase 9a.1+ was explicitly authorized under the 9a.0 ownership constraints and is now closed. `UnifiedPatientSnapshot` carries an immutable `VenousState` container separating preload and native mixed-venous oxygen substates. Existing authorities remain intact: CVP/right-atrial pressure from native circulation, effective venous volume from the volume ledger, and native mixed-venous oxygen from `neocoupling`. The preload proxy is derived/disclosed, not a new solver. The ECMO patient-boundary adapter now consumes the canonical venous API rather than arterial saturation as a venous-saturation surrogate. Structural projection-feedback guard and negative control are in place. Targeted verification passed 24/24; affected patient↔ECMO/CBC regression passed 44/44; collection is 533 = 527 preserved baseline + 6 Phase-9a nodes, 0 missing. 9b.1 remains unauthorized; Phase 10a remains unopened.

## 2026-08-11 — Fix Map v6 Phase 10a implementation complete
Phase 10a is CLOSED. The VA-ECMO patient-boundary adapter now uses the Phase 9a `intrathoracic_relative_preload_proxy_mmhg` for the drainage pressure boundary instead of measured CVP. Measured CVP remains independently authoritative/displayed. In the canonical fixed-control probe, graded PEEP raises measured CVP while lowering the drainage-preload proxy and patient-directed ECMO flow; the effect is regression-bounded and same-patient reversible. CBC07 and the learner Ventilator disclosure now describe this as an educational reduced-order coupling, not a validated quantitative bedside prediction. The living capability matrix also removes the stale claim that authoritative venous oxygen is absent; Phase 10b remains unopened. Five new Phase-10a nodes bring collection from 533 to 538 with zero intended baseline removals. Affected 33-node verification passed when executed in bounded groups; the combined long invocation exceeded the execution window after 26 passes and is not represented as a monolithic pass. Phase 10b and Phase 11 remain unopened/unauthorized.

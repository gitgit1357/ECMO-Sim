# Phase 1a — Legacy JavaScript Scenario / Complication Engine Audit

**Date:** 2026-08-10  
**Audit source:** `ECMO_SIM_V1_RC_GATE1_BEDSIDE_BENCH_2026-07-22.zip` recovered from the project Library (`/Emo sim/`).  
**Current target:** `neonatal-modular-patient-GUI-v0.17.2-P0b-async-close-candidate-2026-08-10`  
**Scope:** Inventory and evaluate the older JavaScript scenario/complication system before any Python scenario-engine design or migration. This document does **not** implement Phase 1b.

---

## Executive conclusion

The older JavaScript branch is real, substantial, and worth mining, but it should **not** survive as a second runtime beside the Python rebuild.

The audit strongly supports the existing Phase 1b default recommendation:

> **Port the validated clinical/orchestration intent and regression-test intent into Python; retire the JavaScript runtime.**

The JavaScript branch contains two very different layers:

1. **High-value reusable design/clinical intent** — complication state machines, triggers, pacing, multiple acceptable pathways, learner/instructor disclosure separation, ordered labs and studies, event/debrief logging, deterministic orchestration concepts, source governance, clinical-validation gates, and broad scenario coverage.
2. **Obsolete duplicate simulation mechanics** — its own flow equation, pressure model, drug effects, gas-exchange model, clinical-consequence engine, and extensive direct patching of MAP/CVP/HR/lactate/PaO2/etc. Those mechanisms conflict with the new project's rule that scenarios call mechanisms rather than assign monitor/physiology numbers.

The right migration unit is therefore **behavior**, not source code.

---

## 1. Provenance and verification

The current Python `HANDOFF.md` refers to a separate older JS branch containing `clinical-events` and `circuit-sandbox.mjs`, and says it had 147 tests. That branch was not included in the current Python package or the July 29 umbrella handoff.

The preserved July 22 V1 RC archive was recovered from the Library and contains the actual source:

- `src/core/clinical-events.mjs`
- `src/engines/circuit-sandbox.mjs`
- scenario family libraries
- scenario builder and runtime director
- trigger/eligibility engines
- information and lab pipelines
- debrief / learner-disclosure layers
- clinical knowledge registry
- clinical validation/source-governance machinery
- 95 Node test files

Independent verification on 2026-08-10:

```text
Reproduction command:
node --test test/*.test.mjs

Node tests: 525
Passed:     525
Failed:     0
Node-reported duration: 2316.165 ms
Measured wall time: 2.34 s
Exit status: 0
```

The full raw test-runner transcript is preserved as
`legacy_reference/LEGACY_JS_NODE_TEST_TRANSCRIPT_2026-08-10.txt` in the Phase 1a handoff package.

Legacy archive SHA-256:

```text
8ba7146399ef457f89035b57afbdafdf07ff552f2054ba7587addffc23577c54
```

The recovered archive itself is preserved under
`legacy_reference/ECMO_SIM_V1_RC_GATE1_BEDSIDE_BENCH_2026-07-22.zip`
inside the Phase 1a handoff package so the audit remains independently reproducible.

### Important correction to HANDOFF

The `147 tests` number is **not correct for the preserved V1 RC being audited**. The recovered release contains **525 passing tests**. The 147 figure may describe an earlier JS checkpoint, but it must not be used as the audit inventory for this release.

No evidence was found that the preserved V1 RC depends on an external deployed JS service that must remain operational.

---

## 2. Quantitative inventory

The clinical knowledge registry contains:

| Artifact | Count |
|---|---:|
| Complications | 36 |
| Reusable learner/clinical actions | 79 |
| Reusable observations | 36 |
| Learning objectives | 12 |
| Accepted scenario presets | 28 |
| Node tests | 525 |
| Test files | 95 |

Action-rule outcome classifications across the 36 complication definitions:

| Outcome class | Rule count |
|---|---:|
| Preferred | 69 |
| Acceptable | 8 |
| Temporizing | 2 |
| Ineffective | 5 |
| Harmful | 13 |

This outcome taxonomy is worth preserving. It encodes a clinically useful idea the Python rebuild should keep: an action need not be merely “correct” or “wrong.” It can be appropriate, acceptable, temporarily helpful, irrelevant, or harmful depending on the hidden mechanism and current state.

---

## 3. Supported scenario inventory — 28 accepted presets

### Low-flow troubleshooting — 6

1. `lf-01-preload` — preload limitation / hypovolemia
2. `lf-02-tamponade` — postoperative tamponade
3. `lf-03-position` — position-sensitive drainage compromise
4. `lf-04-kink` — drainage cannula / tubing kink
5. `lf-05-circuit-obstruction` — mechanical circuit obstruction
6. `lf-06-pump-failure` — pump failure / loss of support

### Circuit emergencies — 6

1. `ce-01-air-emergency` — air entrainment / circuit air emergency
2. `ce-02-circuit-breach` — circuit breach / disconnection with major blood loss
3. `ce-03-oxygenator` — oxygenator thrombosis / membrane-lung failure
4. `ce-04-sweep-gas` — sweep gas / gas-source failure
5. `ce-05-hemolysis` — clinically significant hemolysis
6. `ce-06-major-bleeding` — major bleeding / coagulopathic hemorrhage

### VA ECMO — 4

1. `va-01-differential-hypoxemia` — differential hypoxemia / North-South syndrome
2. `va-02-lv-distension` — LV distension / inadequate unloading
3. `va-03-limb-ischemia` — peripheral cannulation limb ischemia
4. `va-04-thrombosis` — circuit / cannula / intracardiac thrombosis

### VV ECMO — 5

1. `vv-01-recirculation` — VV recirculation / ineffective support
2. `vv-02-oxygenator` — oxygenator dysfunction
3. `vv-03-gas-exchange` — gas-exchange failure / support mismatch
4. `vv-04-pneumothorax` — tension pneumothorax / intrathoracic pressure emergency
5. `vv-04-airway` — airway / ETT / ventilator failure

### Patient emergencies — 7

1. `pe-01-arrhythmia-arrest` — arrhythmia / arrest
2. `pe-02-ich` — intracranial hemorrhage
3. `pe-03-vasoplegia` — vasoplegia / distributive shock
4. `pe-03-sepsis` — infection / sepsis
5. `pe-04-aki-fluid` — AKI / fluid overload
6. `pe-05-metabolic` — metabolic / electrolyte emergency
7. `pe-06-ph-crisis` — pulmonary hypertensive / RV crisis

### Legacy scenario-ID numbering quirk — verified in source

The apparent ID collisions are **genuine legacy naming**, not an audit transcription error:

- `vv-04-pneumothorax` is labeled **VV ECMO 04A**
- `vv-04-airway` is labeled **VV ECMO 04B**
- `pe-03-vasoplegia` is labeled **Patient Emergency 03A**
- `pe-03-sepsis` is labeled **Patient Emergency 03B**

The original source libraries and their acceptance tests use these IDs exactly. Preserve them only as
legacy provenance. **Do not propagate the collision-prone numbering scheme into the Python migration
inventory**; assign unique canonical Python scenario IDs while retaining a `legacy_id` field for traceability.

The knowledge registry additionally contains complications not yet represented as one of the 28 final preset scenarios, including thromboembolic stroke, anticoagulation imbalance, pulmonary hemorrhage, CKRT/ECMO interaction, broader neurologic deterioration, abdominal ischemic/compartment emergencies, congenital-circulation-specific problems, treatment/transfusion adverse events, and transport/procedural hazards.

---

## 4. Architecture worth preserving

### 4.1 Scenario definitions reference shared clinical knowledge rather than copying it

`scenario-builder.mjs` deliberately separates:

- educator setup
- learning objectives
- complication IDs
- action IDs
- observation IDs
- trigger policies
- runtime-director pacing

from the complication rule definitions themselves.

That is the correct direction for `neoscenarios/`: the 50th scenario should compose reusable mechanisms/knowledge rather than duplicate the first scenario's code.

**Migration:** Preserve design intent. Reimplement in Python.

### 4.2 Generic trigger eligibility

`trigger-eligibility.mjs` supports generic policies:

- at start
- time window
- context condition
- action count
- manual

It persists fired trigger state across snapshot/restore and prevents duplicate activation.

**Migration:** High-priority port of semantics and tests. Do not port JS syntax.

### 4.3 Runtime complication pacing/director

`scenario-runtime-director.mjs` separates eligibility from release. It can limit concurrent unresolved events, enforce event spacing, prioritize eligible events, and persist release state.

This is useful orchestration, but its current pacing values are explicitly nonclinical placeholders.

**Migration:** Preserve architecture and tests; treat profile values as educator/simulation policy, not clinical facts.

### 4.4 Clinical event state machines

`clinical-events.mjs` supports:

- hidden event activation
- event states
- action-dependent transitions
- context-dependent transitions
- time-in-state transitions
- resolution
- score deltas
- feedback/rationale
- snapshot/restore
- trajectory signals
- outcome classes

This is one of the strongest pieces of the old branch.

**Migration:** Port the state-machine semantics. Replace the generic `effects.internal` patch mechanism with typed Python mechanism calls/events.

### 4.5 Multiple clinically coherent paths

The old tests explicitly verify different responses to the same learner action depending on cause. Examples:

- Volume is definitive/preferred for hypovolemia.
- Volume is only temporizing for tamponade.
- Additional volume can become ineffective once tamponade remains unresolved.
- Echo can move tamponade from suspected to diagnosed.
- Emergency decompression may be acceptable before formal echo confirmation in a crashing postoperative patient.
- Increasing RPM against preload-limited or obstructive drainage can be harmful rather than therapeutic.
- Increasing sweep does not fix a mechanical low-flow problem.

This is exactly the type of **clinical decision graph** worth preserving.

**Migration:** Preserve as Clinical Behavior Contracts + scenario action/outcome intent. Do not preserve numeric patches.

### 4.6 Learner vs instructor disclosure separation

`learner-disclosure.mjs` strips:

- complication IDs
- hidden states
- scores
- rationale
- educator setup
- knowledge plan
- trigger policies

and hides internal event-transition records from learner presentation.

Tests explicitly check that a hidden diagnosis (e.g. tamponade) does not leak through the presentation, action result, or event log.

**Migration:** Preserve strongly. This should become an invariant/System Behavior Contract in Python.

### 4.7 Ordered information and frozen labs

The old system already distinguishes true hidden state from ordered/revealed information:

- lab order snapshots the true value at draw time
- result appears after turnaround
- studies can be requested, acquired, raw-result available, and later interpreted
- acquisition can be blocked by clinical context

This strongly supports the new Phase 2 lab design.

**Migration:** Preserve concept and tests. Replace placeholder turnaround values with explicitly configurable/validated values.

### 4.8 Debrief/event timeline

The old debrief system records structured event kinds, sequence, simulation time, outcome classifications, state transitions, studies, labs, settings changes, interventions, bubble alarms, and endpoints. It derives instructor timelines and sanitized learner timelines.

**Migration:** Use as source material for Phase 1d's new structured event-record contract. Do not preserve the old schema verbatim; normalize it to the v4 schema and current Python state ownership.

### 4.9 Clinical validation governance

The legacy branch has unusually valuable anti-overclaim machinery:

- institution-specific policy preferred when available
- ELSO used as default authority for institutional gaps
- unresolved rules remain explicitly unvalidated
- passing software tests does not equal clinical validation
- exact-source review / applicability / expert review / regression verification are distinct gates
- source statements require traceable locators before authorizing clinical changes
- placeholder timers cannot be mislabeled as ELSO requirements

The test suite includes exact-comparison dossiers and reviewer-status gates.

**Migration:** Preserve the governance model even if the file structures change. It aligns directly with the current Behavior Contract philosophy.

---

## 5. Architecture that should NOT be ported

### 5.1 `circuit-sandbox.mjs` as a second physiology/circuit engine

The legacy runtime has its own:

- RPM-to-flow model
- cannula-limited flow saturation
- preload penalty/chatter rule
- circuit-pressure equations
- oxygenator ΔP approximation
- sweep / PaCO2 relationship
- FdO2 / PaO2 relationship
- drug-to-HR/MAP approximations
- volume-bolus effects
- rhythm progression
- support-consequence model

These were useful scaffolding before the Python rebuild, but the Python project now has dedicated packages (`neoecmo`, `neocirculation`, `neolung`, `neokidney`, `neocoupling`, `neoecmocoupling`, `neopatient`). Keeping the JS formulas would recreate two authoritative worlds.

**Disposition:** RETIRE runtime mechanics. Mine tests/intent only.

### 5.2 Direct numerical consequence patching

The most important incompatibility with the new architecture is pervasive direct manipulation of hidden numerical state.

Across complication activation/action/time effects, the legacy knowledge registry directly patches fields such as:

| Patched path | Occurrences |
|---|---:|
| `mapBaseline` | 80 |
| `hrCurrent` | 35 |
| `clinicalPao2Target` | 34 |
| `supportFlowMultiplier` | 24 |
| `cvpBaseline` | 22 |
| `trueLatent.lactateMmolL` | 18 |
| `clinicalPaco2Target` | 13 |
| `trueLatent.hgbGdl` | 13 |
| `oxygenatorDeltaPAddMmHg` | 4 |

There are also direct target/status patches for recirculation fraction, limb perfusion, LV distension, oxygenation zones, urine output, fluid balance, potassium, pulmonary pressure, etc.

This violates the new governing rule:

> Scenario actions call mechanisms, not monitor numbers.

Example migration:

```text
OLD
hypovolemia + volume bolus
  -> mapBaseline += 8
  -> cvpBaseline += 5
  -> lactate -= 0.8

NEW
hypovolemia mechanism changes patient volume/preload state
volume intervention adds actual intravascular volume
patient/circuit engines determine MAP, CVP, drainage, flow and later perfusion/lactate response
scenario engine only evaluates/records the action and state transition
```

**Disposition:** Do not transliterate any `effects.internal` numerical patches.

### 5.3 Hard-coded observation results tied to synthetic targets

`observation-resolver.mjs` contains good diagnostic reasoning, but many findings are assembled from legacy synthetic targets such as `recirculationFractionTarget`, `rightRadialSpo2Target`, `lvDistensionGrade`, etc.

**Disposition:** Preserve the finding concepts and diagnostic relationships. Rebuild observations from current authoritative Python state and future diagnostic mechanisms.

### 5.4 Legacy timing values

Thirty of the 36 complication definitions explicitly declare:

```text
timingPolicyStatus = placeholder-until-validated
```

Multiple deterioration timers therefore must not be treated as clinical truth simply because 525 tests enforce them.

**Disposition:** Preserve *sequence semantics* (unresolved problems can worsen; temporization expires; rescue windows exist), but revalidate or deliberately define the actual timing policy before migration.

### 5.5 Generic “set flow target” learner action

The old sandbox exposes `set-flow-target`, which internally binary-searches an RPM to achieve a desired flow. That is inconsistent with the current NorthStar principle that RPM is the control and actual flow is the outcome.

**Disposition:** Do not expose as a normal learner control. If retained at all, restrict to educator/test setup tooling.

### 5.6 Legacy randomness

`lab-queue.mjs` creates result IDs with `Math.random()`. This is harmless presentation randomness in the old implementation but violates the new determinism rule if copied.

**Disposition:** Use deterministic sequence IDs or the scenario engine's seeded RNG where randomness has semantic meaning. No uncontrolled randomness in migrated runtime code.

---

## 6. The 36-complication knowledge inventory

The old registry defines these reusable complication concepts:

### Low-flow / mechanical
- hypovolemia
- postoperative tamponade
- position-sensitive cannula drainage compromise
- drainage cannula / tubing kink
- mechanical circuit obstruction
- pump-support failure

### Circuit emergency / hematologic
- air emergency
- circuit breach / hemorrhage
- oxygenator thrombosis/failure
- sweep-gas failure
- hemolysis
- major bleeding
- circuit/systemic thrombosis
- anticoagulation imbalance

### Neurologic / thromboembolic
- intracranial hemorrhage
- thromboembolism / ischemic stroke
- broader neurologic deterioration / seizure

### VV / respiratory
- VV recirculation
- pneumothorax / intrathoracic-pressure failure
- airway / ETT / ventilator failure
- pulmonary hemorrhage
- gas-exchange failure

### VA / cardiac / perfusion
- differential hypoxemia
- LV distension / inadequate unloading
- limb ischemia
- arrhythmia / arrest
- pulmonary hypertensive / RV crisis

### Systemic / organ support
- vasoplegia / distributive shock
- infection / sepsis
- AKI / fluid overload
- CKRT / ECMO interaction
- metabolic / electrolyte emergency
- abdominal compartment / bowel ischemia / abdominal perfusion emergency

### Special context / operational
- congenital-circulation-specific failure
- medication / transfusion adverse event
- transport / positioning / operational hazard

This inventory should become the starting backlog for Python mechanism coverage and Clinical Behavior Contracts. It should **not** be interpreted as “36 complications must be implemented immediately.” Unsupported mechanisms should remain explicitly marked unsupported rather than faked.

---

## 7. Test intent worth porting

The legacy test suite is more valuable as a **behavioral specification** than as JavaScript regression code.

### Tier A — port early / architecture-defining

- trigger policy types work generically without clinical hard-coding
- trigger state survives snapshot/restore and does not fire twice
- runtime director separates eligibility from release
- concurrent-event limits and pacing are orchestration, not clinical knowledge
- scenario definitions do not copy action rules
- same action produces different outcomes for different hidden causes
- state-entry timing is based on time in the current state, not time since event creation
- snapshot/restore preserves event state and timers
- hidden complication identity never leaks to learner output
- all learner actions remain available through a universal cockpit rather than scenario-specific answer buttons
- lab value freezes at collection/order time and reveal timing is separate
- debrief/instructor timeline retains information that learner output sanitizes
- no duplicated trigger activation after restore

### Tier B — port as Clinical Behavior Contracts as mechanisms become available

- hypovolemia vs tamponade differential behavior
- preload-limited RPM escalation can worsen drainage without fixing flow
- positional drainage compromise responds to restoring position
- kink/obstruction requires mechanical correction rather than blind RPM escalation
- pump failure requires restoring actual pump support
- bubble detector/interlock/reset/retrip behavior
- oxygenator dysfunction uses gas-transfer + pressure-trend context, not one universal ΔP cutoff
- sweep-gas failure localizes to gas source / sweep path
- VV recirculation can worsen effective support despite high apparent circuit flow
- VA differential hypoxemia requires upper-body/right-radial assessment
- LV distension assessment/resolution logic
- limb perfusion checks
- patient emergency response categories

### Tier C — do not port until clinical/timing validation is intentionally revisited

- exact deterioration durations
- exact arrest/rescue windows
- exact MAP/HR/lactate increments or decrements
- exact PaO2/PaCO2 targets
- exact lab turnaround defaults
- synthetic drug coefficients
- synthetic cannula/pressure/flow coefficients

---

## 8. Clinical judgment embedded in the old system that should not be lost

Several design decisions appear repeatedly in definitions/tests and are clinically meaningful even though the numerical implementations are obsolete:

1. **Treat causes, not display abnormalities.** Mechanical low flow should drive investigation of preload, position, kink, obstruction, pump function, etc., rather than reflex RPM escalation.
2. **Temporization is not resolution.** A therapy can transiently improve numbers while the underlying mechanism persists.
3. **Diagnosis may be probabilistic and action urgency context-dependent.** A crashing postoperative tamponade pattern can justify definitive action before formal confirmation; stable situations can require diagnostic confirmation.
4. **ECMO flow is not synonymous with perfusion.** Vasoplegia and other patient problems can cause poor perfusion despite apparently adequate circuit flow.
5. **VV displayed flow is not synonymous with effective systemic support.** Recirculation must be inferred from cannula relationship and saturation patterns.
6. **Gas-exchange troubleshooting should localize the failing component.** Sweep, FdO2, membrane lung, native lungs, airway/ventilator, flow, and recirculation are distinct mechanisms.
7. **Learner-visible information should not reveal the hidden diagnosis.** Assessment actions return findings; educator state retains the hidden cause.
8. **Multiple reasonable pathways can succeed.** The engine should not force one scripted button sequence.
9. **Evidence strength matters.** A published reference can support a trend without justifying a universal numeric cutoff.
10. **Software regression and clinical validation are separate gates.** Passing tests proves implementation consistency, not medical correctness.

These principles should be explicitly retained during Phase 1b/1e migration.

---

## 9. Migration disposition matrix

| Legacy subsystem | Disposition | Reason |
|---|---|---|
| `clinical-events.mjs` state-machine semantics | **PORT INTENT** | Strong reusable event/action/state model |
| Outcome classes + scoring categories | **PORT INTENT** | Supports nuanced assessment rather than binary correct/wrong |
| Trigger eligibility | **PORT EARLY** | Generic, deterministic, well-tested |
| Runtime director | **PORT INTENT** | Good separation of eligibility and pacing; values are policy placeholders |
| Scenario builder / knowledge references | **PORT DESIGN** | Correct composition architecture |
| Learner disclosure sanitizer | **PORT EARLY** | Prevents diagnosis/scoring leakage |
| Lab/information timing concepts | **PORT DESIGN** | Matches new ordered-test architecture |
| Debrief log/timeline | **PORT DESIGN** | Strong basis for Phase 1d structured event stream |
| Clinical source governance / validation gates | **PORT GOVERNANCE** | Valuable anti-overclaim discipline |
| Clinical knowledge registry IDs/taxonomy | **MIGRATE/REVIEW** | Good backlog and vocabulary; each relationship still needs validation status |
| Scenario family inventory | **MIGRATE/REVIEW** | Valuable teaching coverage |
| `observation-resolver.mjs` text/diagnostic relationships | **MINE INTENT** | Findings useful, synthetic target fields obsolete |
| `clinical-consequence.mjs` | **DO NOT PORT RUNTIME** | Duplicates patient physiology through categorical number modification |
| `physiology.mjs` | **RETIRE** | Replaced by Python physiology/circuit packages |
| `circuit-sandbox.mjs` physics | **RETIRE** | Second authoritative circuit/patient world |
| `effects.internal` numeric patches | **REJECT** | Violates mechanism-not-monitor-number rule |
| Placeholder timing constants | **REVALIDATE** | Explicitly marked unvalidated |
| `Math.random()` IDs | **REPLACE** | Violates deterministic scenario rule |
| `set-flow-target` learner action | **RESTRICT/RETIRE** | Flow should be outcome of RPM + circuit conditions |

---

## 10. Comparison with current Python architecture

The Python rebuild already has stronger authoritative mechanism ownership for:

- native circulation
- lung/gas exchange
- kidney/fluid handling
- circuit hydraulics
- ECMO gas transfer
- VA patient/circuit coupling
- patient volume ledger
- ECMO console controls and displayed state

The legacy JS branch therefore should **not** be connected as a separate service/API. Doing so would preserve exactly the duplication the rebuild was intended to eliminate.

The old branch is best treated as:

```text
LEGACY JS
clinical judgment + workflow + test intent
                 |
                 v
translation / validation layer
                 |
                 v
NEW PYTHON
one authoritative patient/circuit world
+ typed mechanisms
+ neoscenarios orchestration
+ Behavior Contracts
```

---

## 11. Phase 1b recommendation produced by this audit

Phase 1a's audit evidence supports a clear default decision for Phase 1b:

### Recommend: PORT INTENT, RETIRE JS RUNTIME

Do **not** maintain the old JS engine behind an API boundary.

Instead:

1. Preserve the old archive untouched as a historical behavioral reference.
2. Extract the 36-complication / 79-action / 36-observation taxonomy into a migration inventory.
3. Create Python scenario/orchestration primitives for event state, triggers, actions, observations, event records, and deterministic scenario RNG.
4. Port Tier A architectural tests first.
5. Map each legacy clinical action/effect to one of:
   - existing Python mechanism,
   - mechanism missing / backlog,
   - observation/information action,
   - educator/scenario orchestration only,
   - reject as obsolete direct-number manipulation.
6. Port scenario families only after their required mechanisms exist.
7. Convert clinically meaningful old assertions into Clinical/System Behavior Contracts.
8. Never use the old 525 green tests as evidence that old numeric values are clinically validated.

There is no technical evidence from this audit that justifies keeping two runtime stacks.

---

## 12. Phase 1a exit criteria status

| Exit item | Status |
|---|---|
| Locate actual JS source | **PASS** |
| Inventory events/complications | **PASS — 36 complications** |
| Inventory triggers | **PASS — generic at-start/time/context/action-count/manual** |
| Inventory sequencing/orchestration | **PASS** |
| Inventory scenario coverage | **PASS — 28 accepted presets** |
| Inventory actions/observations/objectives | **PASS — 79 / 36 / 12** |
| Verify test suite | **PASS — 525/525** |
| Identify clinical judgment worth preserving | **PASS** |
| Identify duplicate/obsolete physics | **PASS** |
| Identify unvalidated placeholders | **PASS — 30 complications explicitly flag timing as placeholder** |
| Determine whether JS must remain independently deployed | **No evidence found** |
| Produce bounded audit document | **PASS — this document** |

**Phase 1a is complete.**

The next roadmap action is Phase 1b: explicitly approve or reject the recommendation to **port validated intent and retire the JS runtime**. No migration code should be written until that decision is recorded.

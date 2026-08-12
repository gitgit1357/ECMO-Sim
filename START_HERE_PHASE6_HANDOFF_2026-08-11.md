# START HERE — FIX_MAP v5 Phase 6 Continuation Handoff

**Handoff status:** Phase 6 implementation is substantially complete, but **Phase 6 is NOT CLOSED**. Do not open Phase 7 or Phase 8. Do not call this a completed release until the remaining baseline-regression accounting and completion artifacts are finished.

## Governing authority
- `FIX_MAP_v5_AUTHORIZED_2026-08-10.md` is the active roadmap for this handoff.
- Build order was fixed: 6a → 6b → 6c → 6d → 6e → 6f → full acceptance → stop/cue user before Phase 7 or 8.
- Same autonomous engineering authority as prior work remains active.
- Do not reopen physiology/CBCs. Phase 6 is GUI/projection only.

## Baseline and exact node provenance
Pre-Phase-6 baseline is v0.21.0.
- Frozen clean baseline node-ID manifest: `PHASE6_BASELINE_PYTEST_NODEIDS_2026-08-10.txt`
- Baseline node count: **497**
- Post-implementation manifest: `PHASE6_POST_PYTEST_NODEIDS_2026-08-11.txt`
- Current post count: **514**
- Delta file: `PHASE6_NODEID_DELTA_2026-08-11.txt`
- Delta currently proves: **17 new / 0 missing / every new node is `test_phase6_*`**.
- `PHASE6_BASELINE_COLLECTION_ENVIRONMENT_NOTE_2026-08-10.txt` records an initial bad collection invocation that produced 496 + 1 error. It is provenance only; the clean 497-node manifest is authoritative.

## Phase-6 implementation currently in tree
Only three non-generated source files differ from the v0.21.0 reference:
1. `src/neogui/__init__.py`
2. `src/neogui/patient_monitor.py`
3. `src/neogui/ecmo_workspace.py`

Seven new test files exist:
- `tests/test_phase6_6a_shared_projection_ribbon.py`
- `tests/test_phase6_6b_ventilator_hemodynamic_readback.py`
- `tests/test_phase6_6c_interventions_live_readback.py`
- `tests/test_phase6_6d_labs_current_context.py`
- `tests/test_phase6_6e_nav_attention.py`
- `tests/test_phase6_6f_accessibility_contrast.py`
- `tests/test_phase6_act_observe_matrix.py`

### 6a implemented
- `learner_patient_reading()` is the shared learner projection.
- Console and Monitor shared patient values are consolidated through it.
- Canonical labels include `MAP` and exact `ECMO PATIENT FLOW`.
- Persistent global ribbon shows MAP, SpO2, ECMO PATIENT FLOW and uses the existing updating state.
- Last committed values remain visible while native physiology is pending; no extrapolation/second solve path.
- Behavioral shared-projection test + narrow static guard are present.

### 6b implemented
- Ventilator shows MAP, CVP, native CO beside respiratory delivery/response.
- ECMO PATIENT FLOW is not grouped into CBC07 hemodynamic response.
- CBC07 transmural-preload limitation disclosure is present.
- Reference-window no-scroll check is in the live Tk test.

### 6c implemented
- Interventions live readback: MAP, CVP, ECMO PATIENT FLOW, urine, net fluid, blood-volume fraction.
- Co-visible with volume and CKRT controls at reference size.

### 6d implemented
- Labs has live `CURRENT PATIENT CONTEXT` beside order controls.
- It is structurally distinct from frozen Ordered Results.
- No stored order-context snapshot was invented.

### 6e implemented
- Labs unread attention uses a set of unread result IDs and only clears after all contributing available results render.
- CKRT stored-but-inactive is persistent and state-based, not learner-action-based.
- No pressure-control nav indicator.
- No alarm architecture.

### 6f implemented
- WCAG AA checks added for core workspace color pairs.
- State remains text-identifiable independent of color.
- One pre-existing low-contrast `POWER` nav label was corrected; color semantics otherwise retained.

## Fresh Phase-6 verification already completed
- Phase-6 test surface: **17/17 green under live Tk/Xvfb**.
- Act→observe matrix: **7/7 rows green**.
- Reference test window used by Phase-6 tests: **1360×820**.
- Capability matrix currently has **99 rows** (93 baseline + 6 Phase-6 GUI/system capability rows).
- New Phase-6 matrix rows explicitly classify changes as UI/system exposure; existing CBC validation/evidence is not promoted.

## Baseline regression status — IMPORTANT
The remaining blocker is **complete auditable accounting of all 497 original tests**. Several legacy native/coupling tests are extremely slow and can outlive wrapper processes. Under FIX_MAP v5, a timeout is **INCOMPLETE**, never a pass or fail.

Confirmed direct/bounded zero-exit results during this continuation include, among others:
- 72/72 baseline block green.
- 63/63 coupling block green.
- 32/32 fast lung/circuit subset green.
- kidney live-coupling file 6/6 green.
- myocardial worker nodes 6/6 individually green.
- remaining renal files 9/9 green.
- earlier direct isolated runs also confirmed cardiopulmonary 5/5, standalone lung 5/5, North Star 2/2, PEEP/CO2 2/2, reintegrated PEEP/CO2 2/2, standalone lung PEEP/CO2 3/3, combined equipment 1/1.

Do **not** add those numbers arithmetically as a unique-node total without checking overlap. The correct closure method is the frozen node-ID manifest, not conversational pass-count addition.

### Known harness problem
Nested subprocess-based verification is unreliable for some old multiprocessing/native tests: child workers can outlive the wrapper timeout. Attempts to run monolithic or large mixed batches repeatedly hit the harness window without assertion failures. Do not report those timeouts as pass/fail.

### Recommended resume method
1. Read `PHASE6_BASELINE_PYTEST_NODEIDS_2026-08-10.txt`.
2. Build a resumable ledger keyed by exact baseline node ID or by original test file.
3. Run direct pytest commands from project root, avoiding nested subprocess wrappers around multiprocessing/native tests.
4. Commit ledger results after each zero-exit file/group.
5. For files that exceed the window, split to individual node IDs.
6. Phase 6 closes only when **all 497 baseline node IDs are accounted for as zero-exit passes**.
7. Re-run post collection and reconfirm 514 = 497 baseline + 17 named Phase-6 nodes, 0 missing.

No failing assertion has been observed in the Phase-6 changes during this work; the unresolved issue is verification runtime/accounting, not a known product failure.

## Remaining closure artifacts to create
Before declaring Phase 6 complete:
1. `PHASE6_BASELINE_VERIFICATION_LEDGER_2026-08-11.*` — exact zero-exit accounting for all 497 baseline nodes.
2. `PHASE6_COMPLETION_2026-08-11.md` containing:
   - fresh pass counts for 6a–6f and total;
   - act→observe 7-row verification;
   - shared-projection ownership table;
   - capability-matrix audit;
   - written before/after walkthrough for Console, Ventilator, Interventions, Labs;
   - baseline/post node-ID proof;
   - explicit note that no physiology/CBC behavior changed.
3. `PHASE6_REFERENCE_SHA256.txt` for every Phase-6-touched/new file.
4. Update `ROADMAP_CURRENT_STATUS_2026-08-10.md` only after closure.
5. Update `HANDOFF.md` append-only with Phase-6 completion only after closure.
6. Package the single latest release only after all acceptance checks are met.
7. **STOP and cue the user before opening Phase 7 or Phase 8.**

## Shared-projection ownership table required at closure
At minimum document these ownership relationships in the completion file:
- MAP → `learner_patient_reading()` → ribbon, Monitor, Console, Ventilator, Interventions, Labs context as applicable.
- SpO2 → shared learner projection → ribbon, Monitor, Labs context as applicable.
- ECMO PATIENT FLOW → shared learner projection → ribbon, Monitor, Console, Interventions; visible globally on Ventilator via ribbon but deliberately not grouped into CBC07 response.
- CVP → shared learner projection → Monitor, Ventilator, Interventions, Labs context as applicable.
- Native CO → shared learner projection → Monitor, Ventilator.
- Net fluid / urine / blood-volume fraction → shared learner projection where Phase-6 readbacks consume them.

## Capability matrix current Phase-6 rows
Current `CAPABILITY_MATRIX.json/.csv/.md` contain six new Phase-6 rows:
- 6a shared learner projection + persistent ribbon
- 6b Ventilator hemodynamic readback
- 6c Interventions live patient readback
- 6d Labs current patient context
- 6e nav attention indicators
- 6f accessibility contrast/state-carrier pass

Current total: **99 rows**.

## Versioning / release warning
This tree is a **handoff work tree**, not a certified Phase-6 release. Do not label it Phase-6 complete merely because the GUI work and new tests are green. Finish the 497-node baseline acceptance first.

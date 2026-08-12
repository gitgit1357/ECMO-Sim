# Phase 6 Completion — 2026-08-11

**Roadmap:** `FIX_MAP_v5_AUTHORIZED_2026-08-10.md`  
**Phase:** 6 — learner information architecture / act→observe repair  
**Status:** **CLOSED**  
**Baseline:** v0.21.0

## Acceptance result
Phase 6 satisfies the authorized 6a→6f closure contract without reopening physiology, hydraulics, gas exchange, kidney, coupling, Clinical Behavior Contracts, alarm architecture, scoring, or Phase 7/8 scope.

### Fresh Phase-6 test result
- 6a shared projection / ribbon: **3/3 passed**
- 6b Ventilator hemodynamic readback: **1/1 passed**
- 6c Interventions live readback: **1/1 passed**
- 6d Labs current context: **1/1 passed**
- 6e navigation attention: **2/2 passed**
- 6f accessibility / contrast: **2/2 passed**
- Act→observe matrix: **7/7 passed**
- Total Phase-6 acceptance surface: **17/17 passed under live Tk/Xvfb**.
- Named node manifest: `AUDIT_PHASE6_ACCEPTANCE_17_NODE_MANIFEST_2026-08-11.txt` (fresh audit rerun: 17/17 passed).
- Reference test window: **1360×820**

## Act→observe verification — 7/7
1. Console action/readback row — PASS.
2. Ventilator action/readback row — PASS.
3. Interventions volume action/readback row — PASS.
4. Interventions CKRT action/readback row — PASS.
5. Labs order/current-context row — PASS.
6. Monitor read-only row with persistent global ribbon — PASS.
7. Scenario Log read-only row with persistent global ribbon — PASS.

## Shared-projection ownership table
| Signal | Authoritative learner projection | Consuming surfaces |
|---|---|---|
| MAP | `learner_patient_reading()` | Global ribbon, Monitor, Console, Ventilator, Interventions, Labs current context where applicable |
| SpO2 | `learner_patient_reading()` | Global ribbon, Monitor, Labs current context where applicable |
| ECMO PATIENT FLOW | `learner_patient_reading()` | Global ribbon, Monitor, Console, Interventions; visible globally while on Ventilator but deliberately excluded from CBC07 response grouping |
| CVP | `learner_patient_reading()` | Monitor, Ventilator, Interventions, Labs current context where applicable |
| Native cardiac output | `learner_patient_reading()` | Monitor, Ventilator |
| Urine output | `learner_patient_reading()` | Interventions and other shared readbacks where consumed |
| Net fluid | `learner_patient_reading()` | Interventions and other shared readbacks where consumed |
| Blood-volume fraction | `learner_patient_reading()` | Interventions and other shared readbacks where consumed |

The projection uses the existing committed workspace state. During native physiology updating, the learner continues to see the last committed values; Phase 6 adds no extrapolator and no second solve path.

## Written before/after walkthrough
### Console
**Before:** repeated patient values were exposed through page-specific reads and the patient-flow label was not fully canonical across learner surfaces. Important patient state could disappear when the learner moved away from the Console.  
**After:** shared values resolve through `learner_patient_reading()`, the canonical label is exact `ECMO PATIENT FLOW`, and the persistent ribbon keeps MAP, SpO2, and ECMO PATIENT FLOW visible while navigating the workspace.

### Ventilator
**Before:** respiratory controls/response were visible, but immediate hemodynamic context required looking elsewhere.  
**After:** MAP, CVP, and native cardiac output are co-located beside respiratory delivery/response. ECMO PATIENT FLOW remains outside the CBC07 response grouping, and the transmural-preload limitation is explicitly disclosed rather than implying a new physiologic relationship.

### Interventions
**Before:** volume and CKRT controls were learner-operable, but the learner had to leave the action surface to inspect several consequences.  
**After:** MAP, CVP, ECMO PATIENT FLOW, urine, net fluid, and blood-volume fraction are co-visible with the existing volume/CKRT controls at the 1360×820 reference window.

### Labs
**Before:** ordered results correctly froze at sample time, but the learner lacked a clearly separate live patient-context panel beside ordering controls.  
**After:** `CURRENT PATIENT CONTEXT` is live and structurally distinct from frozen Ordered Results. No retrospective order-context snapshot was invented; sample-time result semantics remain unchanged.

## Navigation attention and accessibility
- Labs attention is set-based over unread available result IDs and clears only after all contributing results render.
- CKRT attention is persistent for stored-but-inactive state and is deliberately causation-neutral.
- No pressure-control nav indicator and no alarm architecture were introduced.
- Core workspace color pairs pass the Phase-6 WCAG AA normal-text checks.
- Meaningful states remain text-identifiable without depending on color alone.
- One pre-existing low-contrast `POWER` nav label was corrected without changing the underlying state semantics.

## Capability-matrix audit
`CAPABILITY_MATRIX.json/.csv/.md` contain **99 rows total**: 93 pre-Phase-6 rows plus six Phase-6 GUI/system rows (6a–6f). The six additions are explicitly classified as UI/system exposure or accessibility behavior. No existing clinical behavior, CBC evidence status, device validation claim, or external-review status is promoted by Phase 6.

## Baseline/post node-ID proof
- Frozen pre-Phase-6 baseline: **497 nodes**.
- Exact baseline ledger: **497/497 PASS accounted**, 0 unaccounted, 0 failed, 0 timeout-as-pass.
- Freshly re-verified in this continuation: **434 nodes**.
- Explicit direct/bounded zero-exit results carried from the immediately preceding continuation handoff: **63 exact nodes**.
- Final post-Phase-6 collection: **514 nodes**.
- New nodes: **17**.
- Missing baseline nodes: **0**.
- Every new node is in a `test_phase6_*` test file.
- Therefore: **514 = 497 preserved baseline + 17 named Phase-6 additions**.

See `PHASE6_BASELINE_VERIFICATION_LEDGER_2026-08-11.csv/.md`, `PHASE6_BASELINE_PYTEST_NODEIDS_2026-08-10.txt`, `PHASE6_POST_PYTEST_NODEIDS_2026-08-11.txt`, and `PHASE6_NODEID_DELTA_2026-08-11.txt`.

## Source-scope audit
The Phase-6 implementation changes remain confined to the three previously identified non-generated source files:
1. `src/neogui/__init__.py`
2. `src/neogui/patient_monitor.py`
3. `src/neogui/ecmo_workspace.py`

Seven Phase-6 test files were added. No patient/model physiology source, coupling source, CBC contract, or clinical validation behavior was changed as part of Phase 6.

## Gate
Phase 6 is **closed**. Per FIX_MAP v5, **Phase 7 and Phase 8 remain unopened and require explicit user confirmation before work begins.**

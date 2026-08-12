# Fix Map v6 Phase 10b Completion — 2026-08-11

## Scope
Phase 10b closes the FdO2→coupled-patient oxygenation block through the Phase 9a authoritative native mixed-venous oxygen boundary and extends CBC08. Phase 11 differential hypoxemia remains unopened.

## Architectural result
No new physiology solver or authoritative state owner was added. Inspection and direct probing showed that the Phase 9a venous oxygen boundary already feeds the existing ECMO oxygenator model and the existing native+ECMO arterial mixing path. Phase 10b therefore formalizes and regression-protects that path instead of duplicating oxygen physiology.

Path protected by Phase 10b:
`native mixed-venous oxygen (neocoupling → VenousState)` → `patient_boundary_from_snapshot()` → `run_ecmo_console()` membrane inlet → `post-oxygenator return oxygen state` → `VascularSupportPort` → `mix_native_and_ecmo_arterial_blood()` → coupled patient PaO2/SaO2.

## Behavior protected
- Graded FdO2 reduction at fixed sweep/RPM/native state monotonically lowers post-oxygenator PO2.
- The same change directionally lowers coupled-patient PaO2.
- Native mixed-venous inlet oxygen is not rewritten by the FdO2 control.
- Patient-directed ECMO flow is materially unchanged by FdO2-only changes.
- Coupled-patient PaCO2 remains materially unchanged at fixed sweep.
- Same-runtime restoration of FdO2 restores the coupled oxygenation result.
- Exact patient/device magnitudes and time courses are explicitly non-validated.
- Differential upper-/lower-body oxygenation remains Phase 11 territory.

## Existing stale assertion corrected
`tests/test_ecmo_patient_coupling_contract.py` still asserted the pre-Phase-10a raw-CVP drainage boundary. Phase 10a already changed that authoritative drainage input to the intrathoracic-relative preload proxy. The stale assertion was corrected without changing the test node ID or runtime source code.

## Files
See `PHASE10B_CHANGED_FILES_2026-08-11.txt`. No `src/` file changed in Phase 10b.

## Verification
- New Phase 10b tests: 5/5 passed.
- CBC08/Phase9a/coupled-gas/workspace/validation regression invocation: 49/49 passed.
- Phase10a/hydraulic/console/CDI/capability/release regression invocation: 71/71 passed after correcting the stale pre-10a assertion.
- pytest collection: 543 nodes.
- Baseline node IDs: 538; current: 543; exactly five added Phase 10b nodes; zero removed.
- Capability matrix JSON/CSV mirror: exact.
- Full-suite/native-physiology aggregate attempts hit the execution timeout without a reported test failure. Individual completion claims therefore do not represent the full 543-node suite as freshly passed in this environment.

## Clinical/validation boundary
CBC08's existing external evidence packet remains historical evidence and is not rewritten to imply quantitative validation. Phase 10b uses the authorized teaching-fidelity standard: directional correctness, internal coherence, bounded/reversible behavior, and explicit non-claims. Independent external review remains pending.

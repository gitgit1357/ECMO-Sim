# Phase 9a — Unified Venous-State Foundation Completion
Date: 2026-08-11
Status: **CLOSED — IMPLEMENTATION COMPLETE**

## Authorization / governing constraints
Phase 9a.1+ was explicitly authorized after 9a.0 concluded PROCEED. Implementation was bound to the audit constraints and did not open 9b.1 or Phase 10+.

## What was implemented
`UnifiedPatientSnapshot` now carries an immutable `VenousState` with two independently defined components:

### `VenousPreloadState`
- `cvp_mmhg` — sourced directly from native circulation `mean_ra_mmhg`; no second CVP authority exists.
- `effective_venous_volume_ml` / `effective_venous_volume_fraction` — sourced from the existing patient volume ledger.
- `pleural_delta_mmhg` — sourced from the existing native cardiopulmonary coupled result.
- `intrathoracic_relative_preload_proxy_mmhg` — explicitly derived as `mean_ra_mmhg - pleural_delta_mmhg`.

The preload value is a simplified teaching proxy. It is **not** a validated transmural-pressure measurement or patient/device-specific quantitative model.

### `VenousOxygenState`
- native mixed-venous PO₂;
- native mixed-venous saturation;
- native mixed-venous oxygen content.

These remain owned by `neocoupling`; Phase 9a exposes them at the unified-patient boundary rather than introducing an independent oxygen state. `neocoupling` now returns the mixed-venous oxygen-content value derived from its existing native mixed-venous solve.

## Existing consumer migration
`neoecmocoupling.adapters.patient_boundary_from_snapshot()` now consumes:
- venous pressure from `snapshot.venous.preload`;
- effective venous-volume fraction from `snapshot.venous.preload`;
- native venous oxygen saturation from `snapshot.venous.oxygen`.

This removes the old arterial-saturation-as-venous-surrogate path for oxygen saturation.

Venous PCO₂ remains unavailable as an authoritative patient state, so the adapter still uses arterial PaCO₂ as an explicit temporary surrogate for **PCO₂ only**, with that limitation retained in the adapter disclosure.

## Ownership / solve-order result
No new venous solver, circulatory topology, resistance network, or independent free venous state was introduced.

Existing ownership remains:
- CVP/right-atrial pressure → native circulation;
- effective venous volume → patient volume ledger;
- native mixed-venous oxygen → `neocoupling`;
- container/exposure boundary → unified patient snapshot.

`VenousState` is assembled once during `UnifiedNeonatalPatient.snapshot()` after the existing native solve and volume-ledger snapshot are available and before downstream projection/adapter consumers receive the snapshot. Existing native circulation/gas solve ordering is unchanged.

## Structural invariant
`tests/test_phase9a_venous_state.py` contains the required static no-projection-feedback guard over the venous computation path. It fails if `learner_patient_reading`, `patient_monitor_reading`, or the learner patient-monitor projection module appears as a data source in the guarded computation files.

A separate negative-control test supplies a deliberately broken projection dependency and verifies the guard detects it.

## Verification
- Focused patient/GUI compatibility set: **24/24 passed**; exact nodes: `PHASE9A_FOCUSED_24_NODE_MANIFEST_2026-08-11.txt`.
- Affected patient↔ECMO boundary/CBC regression set: **44/44 passed**; exact nodes: `PHASE9A_AFFECTED_REGRESSION_44_NODE_MANIFEST_2026-08-11.txt`.
- Pre-9a collection: **527 nodes**.
- Post-9a collection: **533 nodes**.
- New Phase-9a nodes: **6**.
- Missing pre-9a nodes: **0**.
- Every new node is named `test_phase9a_*` and lives in `tests/test_phase9a_venous_state.py`.
- Capability matrix mirrors now contain **100 rows**.

## Explicit non-goals preserved
No Phase 10 coupling was implemented. In particular:
- PEEP does not yet consume the preload proxy to alter ECMO drainage.
- FdO₂ does not yet update coupled-patient venous return through the Phase-10b systemic mixing/extraction path.
- Harlequin/preductal-postductal behavior is not implemented.
- No new scenario activation surface was added.
- No new quantitative validation claim was made.

## Gate
Phase 9a is closed.

Phase 9b remains closed at its audit conclusion: existing primitives suffice; 9b.1 remains unauthorized.

**Phase 10a remains unopened and requires its own explicit authorization.**

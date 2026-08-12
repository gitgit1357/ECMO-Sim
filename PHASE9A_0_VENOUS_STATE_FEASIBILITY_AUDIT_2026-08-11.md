# Phase 9a.0 — Unified Venous-State Foundation Feasibility / Ownership Audit
Date: 2026-08-11
Status: AUDIT COMPLETE
Conclusion: **PROCEED — with ownership constrained to consolidation/exposure of existing authorities, not creation of a second venous solver.**

## 1. Existing authorities found

The audit found that the codebase already owns most of the quantities the original Phase-9 idea described:

- **Measured CVP / right-atrial pressure:** `neocoupling.CoupledResult.circulation_metrics.mean_ra_mmhg`, exposed as `UnifiedPatientSnapshot.cvp_mmhg`.
- **Effective venous-volume availability:** `neopatient.volume_ledger`, exposed as `effective_venous_volume_ml` and `effective_venous_volume_fraction`.
- **Intrathoracic pressure effect:** `neocoupling.CoupledResult.pleural_delta_mmhg` already exists as part of the native cardiopulmonary solve.
- **Native mixed-venous oxygen:** `neocoupling.CoupledResult.mixed_venous_po2_mmhg` and `.mixed_venous_saturation_pct` are already iterated from systemic flow and oxygen extraction.
- **Patient arterial mixing under VA ECMO:** `neoblood.mix_native_and_ecmo_arterial_blood()` already creates a patient-side mixed arterial oxygen-content state.

The actual missing foundation is therefore **a correctly owned, stable patient/coupling boundary representation of these venous quantities**, plus an intrathoracic-relative preload proxy, not invention of unrelated free venous state variables.

## 2. Ownership decision

**Chosen ownership boundary: `UnifiedNeonatalPatient` / `UnifiedPatientSnapshot`.**

A future `VenousState` should be an immutable patient-owned snapshot container assembled from authoritative upstream results already owned by the native patient/cardiopulmonary solve and volume ledger. It is not a new independent solver or tunable state store.

Why this location:
- it is the first boundary where native circulation, lung/cardiopulmonary coupling, volume ledger, and patient-facing vascular support are already normalized into one patient snapshot;
- `neoecmocoupling.adapters.patient_boundary_from_snapshot()` already treats the unified patient snapshot as the patient-owned boundary supplied to ECMO;
- downstream consumers can therefore read one patient-owned API without reconstructing state from GUI projections or circuit internals.

Rejected alternatives:
- **new `neovenous` authoritative module:** rejected because it would duplicate existing CVP, volume, and mixed-venous authorities and create a second solver/state owner;
- **ECMO coupling layer as owner:** rejected because CVP, effective venous volume, and native mixed-venous oxygen are patient-owned quantities. Making the ECMO coordinator their authority would invert ownership and invite circular patient↔ECMO dependencies;
- **GUI/projection ownership:** categorically rejected. Learner projections are consumers only.

## 3. Dependency direction

The current CVP authority remains `circulation_metrics.mean_ra_mmhg`. Phase 9a should **not** make a new preload state become “the CVP” and should not reverse the existing dependency.

The future preload substate should expose:
- measured CVP/right-atrial pressure by reference to the existing authority;
- effective venous-volume fraction by reference to the volume ledger;
- a **derived intrathoracic-relative preload proxy** using existing native-solve quantities such as right-atrial pressure and `pleural_delta_mmhg`.

The exact proxy formula/tuning belongs to 9a.1 implementation specification/authorization. The audit finding is only that the required upstream values already coexist in the native solve and can be derived without using learner-facing projections.

For oxygen, the native mixed-venous PO2/SvO2 calculation already exists in `neocoupling`. Phase 9a should expose that existing result through the unified patient boundary rather than initializing a second unrelated venous oxygen number. Phase 10b, if later authorized, may extend the coupled oxygen path after ECMO/systemic mixing and extraction; it must not erase the distinction between native source oxygen and future coupled-return oxygen.

## 4. Solve-order safety

**No restructuring of existing CBC-validated native solve order is required to establish the Phase-9a boundary.**

Current order already produces:
1. lung mechanics / intrathoracic pressure;
2. circulation equilibrium;
3. iterative mixed-venous extraction ↔ gas exchange;
4. immutable `CoupledResult`;
5. volume-ledger snapshot and unified patient snapshot;
6. patient-to-ECMO adapter boundary;
7. ECMO coupling / support application;
8. final patient snapshot / learner projections.

A future Phase-9a implementation can assemble/expose venous substates after the existing native `CoupledResult` is available and before projection. It need not move the native circulation/gas loop or make a display projection feed physiology.

## 5. Duplicate-authority check

The phase **must not** introduce:
- a second “authoritative CVP”;
- a second independently evolving blood-volume/preload state;
- a new free mixed-venous saturation disconnected from `neocoupling`;
- any GUI/display-derived source.

The safe design is a normalized immutable container referencing/deriving from existing owners.

## 6. Stop/rescope criteria evaluation

- Unsafe restructuring of already-CBC-validated solve order required? **NO.**
- Only viable design creates duplicate authoritative sources? **NO**, provided implementation follows the consolidation/reference design above.
- Projection→physiology feedback required? **NO.**
- New circulatory topology required? **NO.**

Therefore the audit conclusion is **PROCEED**, not STOP/RESCOPE.

This conclusion authorizes no implementation by itself. Per Fix Map v6, Phase 9a.1+ remains closed until separately authorized.

## 7. Required implementation constraints if 9a.1 is later authorized

1. `VenousState` is an immutable patient-boundary container, not an independent solver.
2. `VenousPreloadState` and `VenousOxygenState` remain separate components.
3. CVP remains sourced from native right-atrial pressure.
4. Effective venous volume remains volume-ledger-owned.
5. Native mixed-venous oxygen remains sourced from `neocoupling`.
6. Any transmural/preload proxy is explicitly derived from authoritative native quantities and named as a proxy.
7. No learner-facing projection may be an input, directly or transitively.
8. Phase 10b must preserve native-vs-coupled oxygen source distinction.

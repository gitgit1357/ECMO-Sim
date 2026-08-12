# Clinical Behavior Contract 07 Completion — Positive Airway Pressure / Native Hemodynamic Coupling

**Date:** 2026-08-10  
**Contract:** `cbc.patient.positive-airway-pressure-hemodynamics.v1`  
**Status:** automated behavior contract implemented/passing; expert clinical review pending

## Decision

CBC07 was selected only after the proposed VA differential-hypoxemia contract had already been blocked and the capability matrix was re-scanned for an authoritative, integrated mechanism. PEEP was chosen because `AirwayPort.peep_cmh2o` is a real unified-patient input with live cardiopulmonary consequences.

The contract is deliberately limited to the **native cardiopulmonary boundary**. It does not create a pneumothorax fault, ventilator-failure state, or PEEP-to-ECMO-drainage claim.

## Empirical behavior captured

For the canonical 3 kg patient at PEEP 0/5/8/12 cmH2O, the current model shows a graded pattern in which native cardiac output and MAP fall while measured CVP rises. Total blood volume and blood-volume fraction do not change from PEEP alone.

This protects an important learner-facing interpretation: elevated measured CVP during positive airway pressure is not proof that intravascular volume or effective transmural preload increased.

Static PEEP is also constrained not to create an artificial large hypocapnia response.

## Restoration semantics

Returning PEEP to baseline in the same `UnifiedNeonatalPatient` returns native equilibrium outputs to baseline. This is an authoritative control reversal, but the current lung model does not maintain persistent recruitment/derecruitment history. The restoration branch is therefore deterministic re-equilibration rather than proof of stateful lung recovery.

## VA-ECMO preload limitation discovered

A direct VA-coupled probe showed that higher PEEP raises measured CVP and the current ECMO preload solver uses that absolute CVP in drainage-capacity calculations. Because no separate transmural venous-pressure/intrathoracic-pressure boundary exists, fixed-RPM patient ECMO flow can rise as PEEP rises.

CBC07 explicitly does **not** validate that relationship. `PEEP-to-ECMO drainage coupling via transmural preload` is now a blocked capability and requires a real preload-interface mechanism before a CBC can be written.

No runtime physiology source was modified in CBC07.

## Files added

- `clinical_behavior_contracts/POSITIVE_AIRWAY_PRESSURE_HEMODYNAMICS_V1.md`
- `clinical_behavior_contracts/positive_airway_pressure_hemodynamics_v1.json`
- `tests/test_clinical_behavior_contract_positive_airway_pressure.py`

## Capability-matrix changes

The living matrix now records CBC07 as automated/passing, updates the existing Airway PEEP row, and adds the blocked PEEP-to-ECMO transmural-preload interface. The Phase 1b backing inventory remains embedded in `CAPABILITY_MATRIX.json` and unchanged.

## Fresh verification

Zero-exit bounded batches:

- CBC07 contract: 4/4 passed
- cardiopulmonary coupling: 5/5 passed
- PEEP/CO2 coupling: 2/2 passed
- standalone PEEP gas semantics: 3/3 passed
- reintegrated PEEP/CO2: 2/2 passed
- unified patient: 4/4 passed
- kidney live coupling: 6/6 passed
- VA coupled time-step + preload/drainage: 10/10 passed

**Total fresh zero-exit verification: 36 passed, 0 failed.**

The exact tree collects **377 tests**. All **93 non-generated files under `src/` are byte-for-byte identical** to v0.17.9. The capability-matrix CSV/JSON mirrors match at **71 unique rows**, with embedded backing inventory unchanged at **79 actions / 36 complications / 28 scenario IDs**.

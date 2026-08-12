# Ready Mechanism, Observation, Fault, and First Scenario Family Contract
**Date:** 2026-08-10

## Purpose
Promote only capabilities already supported by the Python runtime into reusable `neoscenarios` catalogs, then prove them with the first production-structured scenario family member.

## Mutation boundary
`build_supported_mechanism_registry()` registers only:
- `patient.add_intravascular_input`
- `patient.record_blood_loss`
- `ecmo.set_rpm`
- `ecmo.set_sweep`

No partial legacy intervention is promoted to available. Flow remains an outcome, never a scenario-set control.

## Read-only observation boundary
`register_ready_state_observations()` registers six Phase-1b `READY_OBSERVATION_FROM_STATE` assessments:
- hemodynamics
- pump function/output
- oxygenator pressure/gas state
- sweep/FdO2 settings
- patient + post-oxygenator gas exchange
- renal/fluid state

These providers report authoritative state only. They do not infer a diagnosis or fabricate missing alarm/fault semantics.

## Fault boundary
`build_supported_fault_catalog()` currently registers exactly one complete legacy complication:
- `hypovolemia` -> `patient.record_blood_loss`

This is deliberate. Circuit breach, major bleeding/coagulopathy, tamponade, cannula malposition, oxygenator failure, sweep-source failure, and other partial/missing complications are not upgraded merely because pieces of their consequences exist.

## First scenario family
`build_lowflow_hypovolemia_scenario()` produces canonical scenario `lowflow-hypovolemia`, preserving legacy ID `lf-01-preload` as provenance.

The factory owns orchestration and mechanism mapping, not clinical dosing. `blood_loss_ml` and `replacement_ml` are supplied by the caller and remain `behavior-contract-pending` until clinical review defines validated scenario content.

## Disclosure rule hardened in this block
Learner event views suppress scenario-engine mutation events and internal scenario identity metadata. A hidden diagnosis must not leak through canonical scenario IDs, fault IDs, mechanism names, or internal release/resolution events.

## Scope explicitly not added
- no learner scenario GUI
- no Labs tab
- no scoring/debrief engine
- no automatic clinical correctness grading
- no new physiology
- no promotion of partial legacy complications

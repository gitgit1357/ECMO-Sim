# Clinical Behavior Contract 06 Completion — CKRT Net Ultrafiltration

**Date:** 2026-08-10  
**Build target:** v0.17.9  
**Contract:** `cbc.ecmo.ckrt-net-ultrafiltration.v1`

## Candidate decision

CBC06 was initially considered for VA differential hypoxemia. Source inspection rejected that candidate because the current Python VA coupling has no distinct upper-body/right-radial versus lower-body oxygenation state and no mixing-point mechanism capable of producing differential hypoxemia. No surrogate gas target was introduced.

The next fully real substrate in the capability matrix was CKRT net ultrafiltration.

## Defect found and repaired

Before CBC06, `CoupledVaEcmoPatient._solve_current()` forwarded `shunt_ckrt_net_ultrafiltration_rate_ml_min` to the patient as external fluid removal whenever the number was nonzero. It did this even if:

- the shunt was `OPEN`; or
- the shunt was `CKRT` but CKRT blood flow was zero.

This contradicted the already-existing lower-level `step_filtrate_removal()` rule, where CKRT net removal requires both CKRT configuration and a running CKRT blood pump.

The repair is intentionally narrow. Coupled-patient external CKRT removal is now nonzero only when:

1. `shunt_configuration == CKRT`; and
2. `shunt_ckrt_blood_flow_ml_min > 0`.

No CKRT solute, dialysis-dose, anticoagulation, access-pressure, recirculation, or full device model was added.

## Contract behavior

CBC06 compares active net UF with a matched zero-UF system over the same elapsed time. It requires real cumulative CKRT removal and lower body-fluid/intravascular/preload/hemodynamic state in the active-UF branch without attributing endogenous urine to CKRT.

Stopping UF is represented by setting net UF to zero. The cumulative CKRT-removal ledger must then stop increasing, but the contract intentionally does not require immediate hemodynamic recovery.

The recovery branch is stateful: the same patient receives active UF for 20 minutes, UF is stopped, and the removed net fluid is returned through authoritative renal-therapy fluid input over the next 20 minutes. The final state is compared with a matched no-UF counterfactual at the same elapsed time. Historical CKRT removal remains recorded.

## Validation boundary

The canonical `0.4 mL/min`, `30 mL/min CKRT blood flow`, and 20-minute intervals are reproducible regression stimuli only. They are not validated neonatal CKRT prescriptions or treatment recommendations.

CBC06 is automated/passing. Expert clinical review remains separate.

## Future retest conditions

The contract must be revised if the simulator adds a stateful CKRT device machine, solute-clearance/dose physiology, access-pressure/recirculation behavior, revised fluid-compartment partitioning, or learner-operable CKRT prescription controls.

## Fresh verification

- CBC01-CBC06 contracts: 24/24 passed.
- Coupled patient/cache/preload/MAP: 27/27 passed.
- Fixed shunt/console/full circuit/oxygenator/gas: 69/69 passed.
- Ready scenario/Tier-A/scenario primitives: 36/36 passed.
- Total fresh bounded verification: **156 passed, 0 failed**.
- Exact tree collection: **373 tests** with `PYTHONPATH=.:src`.

## Source-diff boundary

Compared with v0.17.8, the only non-generated file under `src/` changed is `src/neoecmocoupling/time_step.py`. The change is limited to CKRT external-fluid-removal gating.

The living capability matrix contains 69 rows. CSV/JSON mirrors match exactly, and embedded Phase 1b backing data remains 79 actions / 36 complications / 28 scenario-ID migrations.

# Phase 4c — CKRT Scope Disposition
**Date:** 2026-08-10
**Roadmap:** FIX_MAP v4 Phase 4 — physiology fidelity gaps, behavior-first
**Status:** CLOSED — no additional CKRT model complexity earned in Phase 4

## Decision
The current CKRT substrate is sufficient for the learner behavior presently claimed:

- independent CKRT blood-flow setting (`Qb`) is stored as a device/prescription control;
- net ultrafiltration (UF) is a real patient fluid-removal mechanism;
- patient UF is gated on `shunt_configuration == CKRT` and `Qb > 0`;
- stopping UF stops further CKRT removal without erasing the historical removal ledger;
- volume/preload/ECMO-flow/MAP/CVP consequences use the same authoritative patient volume and coupling path as other fluid loss;
- Phase 2b exposes Qb and net-UF controls to the learner;
- CBC06 protects those semantics.

The focused Phase 4c re-validation passed 35/35 tests across CBC06, Phase 2b interventions, and fixed-shunt behavior.

## Complexity not earned
Phase 4c does **not** add any of the following because no current learner-facing Behavior Contract requires them and no existing contract failure demonstrates that their absence is producing an incorrect supported behavior:

- solute clearance / dialysis dose;
- urea/creatinine kinetics;
- electrolyte or acid-base clearance;
- dialysate or replacement-fluid composition;
- CKRT access pressure model;
- access recirculation;
- filter TMP / clot burden / filter life;
- CKRT anticoagulation;
- alarms, access-disconnect states, or a complete device state machine;
- circuit blood-volume sequestration/prime effects;
- non-negligible side-port Qb effect on the fixed ECMO shunt hydraulics;
- clinically validated prescription ranges or dose targets.

These remain explicit future capabilities, not hidden assumptions.

## Prescription bounds
The current learner controls reject negative and non-finite Qb/net-UF values. Phase 4c intentionally does not introduce clinical upper/lower prescription limits from unsupported defaults. Numeric values in CBC06 are regression stimuli, not validated neonatal CKRT prescriptions. Clinically bounded prescription ranges belong to a later evidence/validation step or to a future Behavior Contract that demonstrates a learner-safety need for them.

## Historical note on CBC06
CBC06 was authored before Phase 2b and therefore contains historical text saying learner-operable CKRT prescription controls were not yet implemented. That statement is no longer current. The living capability matrix is the status authority: Phase 2b implemented learner Qb/net-UF controls. The CBC06 behavior itself remains valid and unchanged.

## Phase 4 closure
FIX_MAP v4 named three Phase 4 fidelity decisions:

1. myocardial dysfunction — investigated and integrated in Phase 4a;
2. oxygenator proxy/cannula resistance — re-reviewed and left reduced-order in Phase 4b because the supported Behavior Contracts pass;
3. CKRT — retained as a phased Qb/net-UF model in Phase 4c, with deeper prescription/device physiology deferred.

All three are now closed. Therefore **Phase 4 is CLOSED**.

Blocked physiology gaps already recorded in the capability matrix remain blocked and must not be interpreted as Phase 4 completion of those mechanisms. Examples include VA differential hypoxemia/mixing-point state, transmural preload for PEEP-to-ECMO drainage, true venous oxygen state for coupled FdO2 effects, common pre-pump obstruction, position-sensitive maldrainage, hemofilter patient UF coupling, and deferred formulary/lab-analyte mechanisms.

## Next roadmap phase
**Phase 5 — broader validation and commercial readiness** becomes the next numbered primary track. Behavior Contracts continue underneath it.

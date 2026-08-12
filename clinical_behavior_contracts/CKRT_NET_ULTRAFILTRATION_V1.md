# Clinical Behavior Contract — CKRT Net Ultrafiltration / Fluid Removal v1

**Contract ID:** `cbc.ecmo.ckrt-net-ultrafiltration.v1`  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending  

## Purpose

Protect the learner-facing relationship for **CKRT net ultrafiltration (UF)** using the already-authoritative coupled ECMO/patient fluid-removal path. CBC06 does not model solute clearance, dialysis dose, filter performance, prescription adequacy, or a complete CKRT machine.

The contract exists to ensure that an entered net-UF rate changes patient fluid state **only when CKRT is actually selected and its independent blood pump is running**, and that the resulting fluid loss propagates through the same volume/preload model used everywhere else.

## Preconditions

- 3.0 kg unified neonatal patient.
- VA ECMO at 2200 RPM and sweep 600 mL/min.
- Bridge closed for the canonical path.
- Fixed shunt configured as CKRT.
- CKRT blood flow 30 mL/min for the active-UF branch.
- Canonical net-UF stimulus 0.4 mL/min for 20 minutes.
- No additional modeled complication is active.

The numeric CKRT settings are regression stimuli only. They are not asserted as a validated neonatal CKRT prescription or treatment recommendation.

## Required activation gating

Configured net UF must be applied to the patient only when both are true:

1. shunt configuration is `CKRT`; and
2. CKRT blood flow is greater than zero.

Therefore:

- `OPEN` + a nonzero stored CKRT UF setting must remove **no CKRT fluid**;
- `CKRT` + zero CKRT blood flow + nonzero UF setting must remove **no CKRT fluid**;
- `CKRT` + running CKRT blood flow + nonzero UF setting may remove fluid at the configured net-UF rate.

This mirrors the existing lower-level fixed-shunt filtration rule and prevents a stale control value from silently removing patient volume when no CKRT machine is running.

## Required behavior while net UF is active

Compared with an otherwise identical matched system with CKRT running but net UF set to zero over the same elapsed time:

1. cumulative CKRT removal increases by `UF rate × elapsed time`;
2. cumulative net body fluid is lower by approximately that removed volume;
3. intravascular blood volume is lower according to the unified patient model's configured intravascular fraction of net fluid change;
4. preload is lower;
5. patient-directed ECMO flow is lower;
6. drainage pressure is lower/more negative;
7. MAP and CVP are lower in the isolated canonical path.

The matched-control comparison is intentional: endogenous urine continues in both systems and must not be misattributed to CKRT UF.

## Stopping UF

CBC06 v1 represents stopping net UF by setting the authoritative CKRT net-UF rate to zero while CKRT may remain configured/running.

After that change:

- cumulative CKRT removal must stop increasing;
- endogenous urine/fluid changes may continue independently;
- the contract does not require immediate hemodynamic recovery because stopping removal does not replace volume already removed.

## Stateful replacement / recovery

To test reversibility without pretending endogenous urine is absent, CBC06 uses a matched counterfactual:

- Path A receives active CKRT UF for 20 minutes, then UF is set to zero and fluid is returned at the same rate for the next 20 minutes through the authoritative renal-therapy fluid-input path.
- Path B runs for the same total elapsed time with CKRT blood flow present but net UF zero throughout.

At the end, Path A must return approximately to Path B for blood volume, preload, patient-directed flow, drainage pressure, MAP, CVP, and cumulative net body fluid. The CKRT removal ledger must retain the amount that was genuinely removed; recovery must not erase historical accounting.

This is a genuine stateful recovery test in the same patient object, not a fresh immutable parameter evaluation.

## Allowed exceptions / scope

- This contract does not validate CKRT blood-flow prescriptions, solute clearance, dialysis dose, anticoagulation, membrane performance, access recirculation, replacement-fluid composition, electrolyte correction, or acid-base effects.
- The model treats CKRT blood flow as informational with negligible impact on fixed-shunt hydraulics; CBC06 does not claim otherwise.
- Net fluid changes are partitioned into intravascular volume using the existing reduced-order patient fraction; that fraction is not declared device-specific or clinically exact by this contract.
- Other concurrent causes of preload loss or gain can alter the displayed hemodynamic response and require their own contracts.
- Learner-facing CKRT Qb and net-UF controls are implemented in Phase 2b; device-specific prescription bounds and a full CKRT machine state model remain outside this contract.

## Future invalidation / retest conditions

CBC06 must be expanded or rewritten if the simulator later adds:

- a stateful CKRT device model with explicit running/stopped/alarm states;
- solute-clearance or dialysis-dose physiology;
- CKRT access pressure/recirculation or circuit-volume effects;
- separate replacement-fluid/dialysate physiology;
- a revised body-fluid-to-intravascular partition model;
- a more complete learner-operable CKRT prescription/device state machine beyond the current Phase 2b Qb/net-UF controls.

At that point, simple `configuration + blood flow > 0` gating may no longer be sufficient evidence that the real device-state transition is correct.

## Exit criteria

CBC06 is **automated/passing** when activation gating, active-UF divergence from a matched zero-UF control, stopping behavior, and stateful matched-counterfactual recovery all pass against the authoritative coupled model. It becomes **clinically validated** only after expert review accepts the preconditions, directional relationships, and scope boundaries.

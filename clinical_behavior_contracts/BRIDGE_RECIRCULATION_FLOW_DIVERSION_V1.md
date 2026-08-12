# Clinical Behavior Contract — Bridge Recirculation / Flow Diversion v1

**Contract ID:** `cbc.ecmo.bridge-recirculation-flow-diversion.v1`  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending

## Purpose

Protect the learner-facing distinction between **total circuit flow** and **patient-directed ECMO flow** when the bridge is opened/titrated. Bridge flow is recirculated circuit flow: it can increase total pump flow without reaching the patient, can reduce effective VA support, and can contaminate the venous CDI reading with recently oxygenated/CO2-cleared blood.

CBC09 also closes a target-flow solver defect discovered during probing: the inverse bridge-clamp search used live patient pressure boundaries, but its final returned operating point silently recomputed without those boundaries. In coupled use this caused requested bridge-flow targets to miss materially.

## Preconditions

- VA-ECMO reduced-order patient boundary: 3.0 kg, MAP 42 mmHg, CVP 5 mmHg, native cardiac output 300 mL/min.
- Native venous saturation: 0.65.
- Native venous pCO2: 55 mmHg.
- Pump: 3000 RPM.
- Sweep: 600 mL/min.
- FdO2: 1.00.
- Bridge target-flow probe: 0, 25, 50, 75, 100, 150 mL/min.

These values are regression fixtures, not clinical bridge-flow prescriptions.

## Required response

As bridge target flow is increased while RPM and patient boundary are otherwise held constant:

1. the solved bridge flow must track the requested bridge target within solver tolerance under the **live patient boundary**;
2. patient-directed ECMO flow must decrease;
3. settled VA MAP support must decrease because bridge flow is not systemic return;
4. venous-CDI recirculation fraction must increase;
5. venous-CDI saturation must shift upward toward post-oxygenator blood;
6. venous-CDI pCO2 must shift downward toward post-oxygenator blood;
7. total circuit flow must never be interpreted as patient support: branch conservation remains total = patient + shunt + bridge.

## Restoration branch

Returning bridge target flow to zero must reproduce the closed-bridge operating point for the same immutable patient/control boundary. This is deterministic control reversal, not proof of recovery from a persistent bridge-clot, accidental unclamping, or stopcock fault state.

If mutable bridge-fault state is introduced later, restoration must be re-tested through the actual activation/clear action in one runtime object.

## Not modeled

- Persistent accidental bridge-opening fault state.
- Bridge clamp mechanics beyond the current reduced-order resistance relation.
- A clinically validated bridge target-flow range or flush interval.
- Thrombus propagation or embolization caused by bridge management.
- Automated learner scoring for bridge-management errors.

## Validation boundary

A passing CBC09 means the simulator preserves the intended **directional and accounting relationship** between bridge recirculation, patient-directed flow, MAP support, and CDI contamination, and that target-flow titration actually honors the live patient boundary. It does not validate exact clamp positions or prescribe clinical bridge flow.

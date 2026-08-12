# Clinical Behavior Contract — Drainage-Path Resistance Increase v1

**Contract ID:** `cbc.ecmo.drainage-path-resistance.v1`  
**Legacy reference:** `lf-04-kink` / `drainage-cannula-kink`  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending  

## Purpose

Protect the learner-facing hydraulic signature that the current Python model can honestly represent for an **increase in resistance in the patient drainage path**. This contract does not claim a complete typed kink fault, does not model body/cannula position, and does not reuse the common pre-pump resistance knob as a substitute for either.

CBC05 was intentionally split after probing the existing primitives:

- **CBC05A (this contract):** increased patient drainage-path/cannula resistance — executable now;
- **CBC05B:** common pre-pump mechanical obstruction — blocked until the branched operating-point solver contains a stateful obstruction mechanism whose resistance affects both pressure and solved flow;
- **CBC05C:** position-sensitive maldrainage — blocked until an explicit position/cannula-position state exists.

## Preconditions

- VA ECMO circuit with the project's always-open fixed shunt and bridge closed.
- Pump RPM fixed for the primary comparison.
- Live patient arterial and venous pressure boundaries held fixed.
- Baseline drain cannula uses the existing provisional `DRAIN_10FR` hydraulic coefficient.
- No hypovolemia or other drainage-limiting complication is introduced.

## Regression stimulus

The automated contract multiplies the drain-cannula quadratic resistance coefficient by a fixed regression factor. The multiplier is **not** a clinical kink-severity scale and is not mapped to a percentage lumen occlusion.

## Required behavior at fixed RPM

Compared with the unobstructed baseline, increased drainage-path resistance must:

1. reduce patient-directed ECMO flow;
2. reduce total circuit flow;
3. increase fixed-shunt flow fraction / circuit recirculation fraction;
4. increase the pressure requirement across the patient/junction path;
5. leave the obstruction present even if RPM is subsequently increased.

Because this circuit has an always-open recirculation shunt joining the drainage side before the pump, **a more-negative P1 is not required by CBC05A**. The shunt can partially supply pump inlet flow while patient drainage falls, so gross total flow and inlet pressure need not mirror patient-directed flow one-for-one.

## RPM escalation branch

Increasing RPM while the resistance increase remains present may increase patient flow in this model. CBC05A therefore does **not** reuse the hypovolemia rule that RPM escalation must fail to improve flow.

Instead, at the same elevated RPM, the obstructed circuit must still deliver less patient-directed flow than the unobstructed circuit and retain a higher shunt fraction / higher patient-path pressure requirement. Increasing RPM does not constitute removal of the obstruction.

## Restoration semantics

CBC05A v1 uses immutable `CannulaHydraulicParameters` supplied fresh to the hydraulic solve. Returning to the baseline coefficient is therefore a **pure-function determinism check**, not proof that a persistent kink fault can be cleared in place.

If a mutable scenario-addressable drainage-kink mechanism is later introduced, the restoration branch must be rewritten to activate and clear that real fault in the same runtime object.

## Not modeled

- explicit kink severity or lumen geometry;
- kink location along the drainage tubing/cannula;
- common pre-pump tubing obstruction as a solved flow-limiting fault;
- body/cannula position and position-dependent drainage;
- suction events caused by intermittent cannula-wall apposition;
- a typed learner action that relieves the kink;
- device-specific pressure-flow curves for the actual clinical drainage cannula.

## Future invalidation / retest conditions

CBC05A must be expanded or rewritten if the simulator later adds:

- a mutable `drainage_kink` or drainage-obstruction fault state;
- a typed kink-relief action;
- position-sensitive cannula state;
- explicit cannula-wall apposition/chatter mechanics;
- validated device-specific drainage cannula hydraulics;
- a corrected/common pre-pump obstruction mechanism that participates in the branched operating-point solve.

## Exit criteria

CBC05A is **automated/passing** when the fixed-RPM resistance comparison, RPM-escalation comparison, and deterministic baseline re-evaluation pass. It becomes **clinically validated** only after expert review accepts the directional bedside signature and the circuit-topology caveat regarding P1.

# Clinical Behavior Contract — Complete Sweep-Gas Failure v1

**Contract ID:** `cbc.ecmo.sweep-gas-failure.v1`  
**Scenario family:** `circuit-sweep-gas-failure` (`legacy_id: ce-04-sweep-gas`)  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending

## Purpose

Protect the learner-facing relationship for a complete loss of membrane-lung sweep-gas flow without conflating it with blood-path obstruction, oxygenator thrombosis, or an FdO2-only fault.

CBC02 intentionally distinguishes **ordinary nonzero sweep titration** from **zero effective sweep**. For ordinary sweep changes, the reduced-order model keeps CO2 clearance sweep-dominant and oxygen transfer FdO2-dominant. At zero sweep, however, there is no gas-side flow across the membrane and the oxygenator must not continue adding oxygen or removing carbon dioxide. CBC02 interprets this as a sustained/effective-zero-sweep **post-transient equilibrium**; residual oxygen in the oxygenator/gas path and its short washout transient are not dynamically modeled.

## Preconditions

- 3.0 kg unified neonatal patient for the coupled branch.
- VA ECMO configuration.
- Pump at 2200 RPM.
- Sweep 600 mL/min before failure.
- FdO2 1.0.
- Bridge closed (`bridge_clamp_position = 0.0`).
- No additional modeled complication active.
- The isolated membrane-boundary regression uses representative inlet venous saturation 0.65 and inlet pCO2 58 mmHg so oxygen and CO2 transfer can be evaluated independently of current patient-state limitations.

The representative inlet values are **test fixtures**, not treatment targets.

## Failure stimulus

Set effective sweep-gas flow to **0 mL/min** through the authoritative ECMO sweep control.

## Required membrane-boundary response

At fixed blood-side conditions and pump settings:

1. solved blood/circuit flow must remain materially unchanged;
2. post-oxygenator pCO2 must return approximately to inlet pCO2 (no CO2 removal);
3. post-oxygenator oxygen saturation must return approximately to inlet saturation (no O2 addition);
4. post-oxygenator pO2 must return approximately to the pO2 implied by the inlet saturation.

This guards against the prior model defect where zero sweep removed CO2 clearance but continued producing a hyperoxic post-oxygenator pO2.

## Required coupled-patient response

With the same ECMO blood-flow configuration:

- true patient pCO2 must rise when sweep falls from 600 to 0 mL/min;
- patient-directed ECMO blood flow must remain materially unchanged from sweep loss alone.

CBC02 v1 does **not** assert a coupled-patient pO2 fall. The current native-venous-saturation calculation can produce near-fully-saturated venous inlet blood, which masks that consequence. That limitation is documented rather than silently repaired inside this contract.

## Restoration branch

Restore sweep to **600 mL/min**.

Required behavior:

- post-oxygenator CO2 clearance returns;
- oxygen addition again occurs for a representative desaturated venous inlet;
- coupled-patient pCO2 returns approximately toward its pre-failure state;
- blood flow remains governed by the pump/circuit rather than by the sweep setting.

## Nonzero sweep titration rule

At fixed blood flow and FdO2, increasing **nonzero** sweep should predominantly improve CO2 clearance. The existing reduced-order model is allowed to keep modeled oxygenation essentially unchanged across ordinary nonzero sweep adjustments.

## Scope / allowed exceptions

- Oxygenator clot/thrombosis and blood-path obstruction require separate contracts.
- FdO2 loss with continued gas flow is a different failure mode.
- Gas-line obstruction or source disconnection may converge on zero effective sweep but can produce different bedside clues.
- Learner-displayed gases may lag true values through the dynamic display layer.
- Device-specific transfer magnitudes are outside CBC02 v1.
- The short residual-gas washout period after sweep is stopped is not modeled; zero-sweep acceptance assertions apply after that transient.

## Validation boundary

A passing automated contract means the model satisfies these directional relationships. It does **not** certify device-specific gas-transfer performance or complete clinical validation. Expert review remains separate.

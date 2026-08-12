# Clinical Behavior Contract — Fixed-Shunt Configuration / Hemofilter Hydraulics v1

**Contract ID:** `cbc.ecmo.fixed-shunt-configuration.v1`  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending

## Purpose

Protect the learner-facing hydraulic distinction among the three mutually exclusive fixed-shunt configurations already implemented in the circuit: **OPEN**, **HEMOFILTER**, and **CKRT**. The contract intentionally separates *device presence/resistance* from *fluid-removal activity*.

CBC10 does **not** promote the lower-level hemofilter ultrafiltration helper into coupled-patient physiology. Its current default removal rate is provisional, is not learner-prescribed through the console, and has not been clinically validated.

## Preconditions

- VA-ECMO reduced-order patient boundary: 3.0 kg, MAP 42 mmHg, CVP 5 mmHg, native cardiac output 300 mL/min.
- Native venous saturation: 0.65.
- Native venous pCO2: 55 mmHg.
- Pump: 2600 RPM.
- Sweep: 600 mL/min.
- FdO2: 1.00.
- Bridge: closed.
- Clean fixed-shunt tubing (`clot_fraction = 0`).

These are regression fixtures, not clinical operating prescriptions.

## Required response

At otherwise identical conditions:

1. installing the inline HEMOFILTER must increase shunt-branch resistance and therefore reduce fixed-shunt flow and shunt fraction relative to OPEN;
2. reduced shunt diversion must redistribute some flow toward the patient branch, increasing patient-directed ECMO flow relative to OPEN at the same RPM;
3. the closed-loop VA MAP support must not fall when the only change is reduced fixed-shunt diversion from inline hemofilter resistance;
4. setting `scuffing_active` true versus false with the HEMOFILTER already installed must not change circuit hydraulics — filter *presence* owns resistance, filtration activity does not;
5. CKRT configuration must remain hydraulically equivalent to OPEN because its pigtails use the 3-way stopcock side ports and do not occupy the inline shunt path in this reduced-order model;
6. branch conservation must remain intact.

## Restoration branch

Returning HEMOFILTER configuration to OPEN must reproduce the OPEN operating point for the same immutable boundary and controls. This is deterministic configuration reversal, not proof of stateful filter insertion/removal, line de-airing, clot removal, or procedure-related recovery.

## Explicitly blocked behavior

**Hemofilter net-fluid removal in the coupled patient is not contracted here.**

The lower-level `step_filtrate_removal()` helper can accumulate removal while HEMOFILTER + `scuffing_active` are present, but the console currently supplies only the activity flag, not a clinically bounded learner prescription, and the coupled VA coordinator does not hand that provisional hemofilter rate into the patient volume ledger.

Promoting the current default `ultrafiltration_rate_ml_min` into coupled physiology would therefore turn an implementation placeholder into a clinical behavior claim. CBC10 refuses that promotion.

## Not modeled

- Clinically validated scuffing-filter ultrafiltration prescription or TMP-driven removal.
- Stateful filter insertion/removal procedure.
- Filter priming-volume or blood-volume sequestration effects.
- Hemoconcentration, solute clearance, electrolyte change, or anticoagulation effects.
- Filter clot propagation beyond the existing generic shunt `clot_fraction` resistance proxy.
- CKRT side-port interaction with shunt hydraulics beyond the current deliberately negligible reduced-order assumption.

## Future retest conditions

CBC10 must be extended/retested if:

- a learner-settable hemofilter ultrafiltration prescription is added;
- hemofilter removal is coupled into the patient volume ledger;
- TMP-driven or device-specific hemofilter behavior is introduced;
- filter insertion/removal becomes persistent scenario state;
- CKRT side-port blood-flow interaction is modeled as non-negligible.

## Validation boundary

A passing CBC10 means the current simulator preserves the intended **configuration-level hydraulic accounting** among OPEN, inline HEMOFILTER, and side-port CKRT. It does not validate an ultrafiltration dose, device-specific filter resistance, or clinical benefit of installing a hemofilter.

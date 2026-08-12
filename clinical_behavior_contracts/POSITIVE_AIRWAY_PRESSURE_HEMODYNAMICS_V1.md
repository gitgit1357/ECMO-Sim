# Clinical Behavior Contract — Positive Airway Pressure / Hemodynamic Coupling v1

**Contract ID:** `cbc.patient.positive-airway-pressure-hemodynamics.v1`  
**Automation status:** implemented and regression-tested  
**Clinical review status:** external evidence packet complete; expert sign-off pending

## Purpose

Protect the reduced-order relationship between authoritative **PEEP** and native neonatal cardiopulmonary hemodynamics without pretending that the simulator predicts a universal patient response to each PEEP increment.

CBC07 began as a **native cardiopulmonary contract**. Phase 10a now extends its canonical teaching path into VA-ECMO drainage using the Phase 9a intrathoracic-relative preload proxy. The proxy is explicitly educational and reduced-order; it is not a validated patient/device-specific transmural-pressure measurement or quantitative bedside predictor.

## Preconditions

- 3.0 kg unified neonatal patient.
- No vascular-support contribution in the canonical contract snapshot.
- Baseline PEEP 0 cmH2O.
- Canonical elevated PEEP 8 cmH2O.
- Graded regression probe at 0, 5, 8, and 12 cmH2O.
- No blood loss, fluid input, third spacing, or CKRT removal.

These PEEP values are **regression stimuli, not a validated neonatal ventilator prescription**.

## Required behavior — canonical isolated regression path

Within the simulator's stated canonical preconditions, as PEEP rises across the graded probe:

1. native cardiac output falls;
2. MAP falls;
3. measured CVP rises;
4. total blood volume and blood-volume fraction remain unchanged;
5. static PEEP must not create a large artificial hypocapnia response.

The clinically important interpretation guardrail is that **higher measured CVP under positive airway pressure must not be treated as evidence of increased intravascular volume or effective transmural preload**.

### External-evidence scope

The monotonic CO/MAP path above is a **canonical simulator teaching path**, not a claim that every ventilated neonate or child must show the same direction or magnitude at every PEEP step. Pediatric and neonatal studies show that the cardiovascular response to PEEP is context dependent: cardiac/right-ventricular output can fall, yet the average systemic effect may be modest, blood pressure may remain unchanged, and lung recruitment/compliance can modify the response.

The evidence packet for this distinction is `validation_packets/CBC07_POSITIVE_AIRWAY_PRESSURE_HEMODYNAMICS_EVIDENCE_REVIEW_2026-08-10.md`.

## Restoration / control reversal

CBC07 reverses PEEP from 8 cmH2O back to 0 cmH2O in the same `UnifiedNeonatalPatient` and requires the native equilibrium outputs to return to the original baseline.

This is a real authoritative airway-input reversal in the same patient object, but it is **not** evidence of a history-dependent recruitment/derecruitment recovery path. The current native solve re-equilibrates from the new airway input; it does not maintain a persistent recruited-lung state.

## Phase 10a ECMO-drainage extension

Phase 9a introduced one canonical patient-boundary venous container and an explicitly derived `intrathoracic_relative_preload_proxy_mmhg = measured CVP - pleural pressure delta`. Phase 10a routes the ECMO drainage boundary through that proxy instead of absolute measured CVP.

The protected teaching behavior is therefore: at fixed VA-ECMO controls, raising PEEP can raise measured CVP while lowering effective drainage preload and patient-directed ECMO flow. The effect is required to remain bounded at the canonical probe and to reverse when PEEP returns to baseline in the same patient.

This closes the prior architectural block but **does not convert the proxy into a clinically validated transmural-pressure measurement**. Exact PEEP-to-flow magnitude remains regression-only and requires later expert/external validation before any stronger teaching claim.

## Current ventilator integration

Phase 2d implemented learner-operable pressure-control ventilation through the unified patient, including PIP, PEEP, respiratory rate, inspiratory time, and FiO2. CBC07 therefore no longer lists those basic pressure-control inputs or learner ventilator controls as absent.

CBC07 remains deliberately narrower than full ventilator validation: it protects the PEEP/hemodynamic teaching relationship, not device accuracy or every ventilator mode.

## Not modeled / not validated by CBC07

CBC07 does not validate:

- advanced ventilator modes beyond the implemented pressure-control pathway;
- history-dependent lung recruitment or derecruitment;
- barotrauma or ventilator-induced lung injury;
- pneumothorax;
- a validated patient/device-specific transmural central-venous-pressure measurement;
- a clinically validated quantitative PEEP-to-ECMO-drainage dose-response;
- a universal quantitative PEEP-to-cardiac-output or PEEP-to-MAP dose-response.

## Future invalidation / retest conditions

CBC07 must be revisited if the simulator later adds:

- advanced ventilator modes or synchrony mechanisms that materially change mean-airway-pressure/hemodynamic behavior;
- persistent recruitment/derecruitment or lung-injury state;
- pneumothorax physiology;
- replacement of the Phase 10a preload proxy with a more physiologically explicit venous/transmural model;
- materially expanded cannula-collapse or intrathoracic drainage mechanics.

Those changes must re-open the coupled drainage assertions rather than silently inheriting the Phase 10a regression behavior.

## Exit criteria

CBC07 is **automated/passing** when the canonical graded PEEP response, non-volume guardrail, gas-artifact guardrail, coupled ECMO-drainage direction/boundedness, and same-patient control reversal all pass. The external evidence packet is now complete; expert sign-off is still required before the teaching interpretation is treated as clinically reviewed.

# Clinical Behavior Contract — Ongoing Major Bleeding / Hemorrhage v1

**Contract ID:** `cbc.patient.ongoing-major-bleeding.v1`  
**Legacy reference:** `ce-06-major-bleeding`  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending  

## Purpose

Protect the learner-facing relationship for **ongoing blood-volume loss** without inventing coagulopathy, transfusion-component physiology, a surgical bleeding-control model, or a generic mutable hemorrhage-severity state that the Python patient does not yet contain.

CBC04 treats ongoing hemorrhage as serial calls to the authoritative `UnifiedNeonatalPatient.record_blood_loss()` mechanism. The cumulative volume ledger is therefore the source of truth.

## Preconditions

- 3.0 kg unified neonatal patient.
- VA ECMO configuration.
- Pump at 2200 RPM and sweep 600 mL/min.
- Bridge closed for the canonical regression path.
- Baseline state is not chattering.
- No additional modeled complication is active.

The moderate pump setting intentionally avoids beginning the contract at a drainage-demand boundary.

## Regression stimulus

The canonical automated path applies **three serial blood-loss increments**, each equal to **5% of modeled baseline blood volume**.

After the second loss increment, an intravascular replacement equal to **50% of one loss increment** is given while bleeding is still considered ongoing. A third loss increment then follows.

These percentages are reproducible regression stimuli only. They are **not** validated neonatal hemorrhage thresholds, transfusion doses, or treatment recommendations.

## Required behavior during ongoing loss

Across serial loss increments, the authoritative state must show a coherent cumulative volume deficit:

1. cumulative blood-loss ledger increases by the amount actually removed;
2. blood-volume/preload fraction decreases as net loss accumulates;
3. patient-directed ECMO flow decreases;
4. drainage pressure becomes more negative;
5. MAP decreases;
6. CVP decreases.

The contract requires progressive deterioration for this isolated canonical path, but does not assert that every real hemorrhage must produce strictly monotonic displayed vital signs under all concurrent therapies/pathology.

## Partial replacement while loss continues

After two loss increments, replace only half of one increment through the authoritative intravascular-input mechanism.

Required behavior:

- preload/flow/MAP/CVP improve relative to the immediately preceding depleted state;
- drainage pressure becomes less negative;
- the patient remains measurably below the original euvolemic baseline because cumulative loss still exceeds cumulative replacement;
- cumulative blood-loss accounting is unchanged by replacement;
- cumulative input increases only by the amount actually given.

When the next loss increment occurs, deterioration must resume from that partially corrected state.

This is the central CBC04 teaching relationship: **replacement that does not keep pace with ongoing loss may transiently improve hemodynamics without resolving the underlying volume deficit.**

## Bleeding cessation and definitive volume restoration

The current model has no mutable `bleeding_active` state or explicit surgical/hemostatic control mechanism. For CBC04 v1, **bleeding cessation is represented by ceasing further calls to `record_blood_loss()`**.

Once further loss has stopped, replacing the remaining net intravascular deficit must return preload, patient-directed flow, drainage pressure, MAP, and CVP approximately to the isolated baseline. The automated tolerance is 1% relative error.

This is a real state-reversal test of the patient volume ledger, not a reset or reconstructed baseline object.

## Allowed exceptions / scope

- Vasopressors, myocardial dysfunction, vasoplegia, tamponade, pneumothorax, or other concurrent pathology can alter MAP and flow responses and need their own contracts.
- Higher RPM/cannula demand may cause chatter earlier than this canonical path.
- Opening bridge/shunt paths can change gross circuit flow without correcting patient volume loss.
- Learner-displayed values may lag authoritative state because monitor dynamics are intentionally smoothed.
- This contract does not model platelet/coagulation factor depletion, anticoagulation changes, hemoglobin/oxygen-content loss, component transfusion effects, surgical source control, or a bleeding-rate state machine.
- “Major bleeding” is the legacy scenario label; the automated percentage stimulus is not asserted as a clinical severity definition.

## Future invalidation / retest conditions

CBC04 must be expanded or rewritten if the simulator later adds any of the following:

- a persistent/mutable bleeding-rate mechanism;
- explicit hemostatic/source-control actions;
- hemoglobin/RBC-mass loss coupled to bleeding;
- coagulation/platelet physiology;
- blood-component transfusion mechanisms.

At that point, stopping calls to `record_blood_loss()` will no longer be sufficient evidence that a true stateful hemorrhage process has been stopped.

## Exit criteria

CBC04 is **automated/passing** when the serial-loss, partial-replacement, resumed-loss, and final state-reversal assertions pass against the authoritative model. It becomes **clinically validated** only after expert review accepts the preconditions, directional relationships, and scope boundaries.

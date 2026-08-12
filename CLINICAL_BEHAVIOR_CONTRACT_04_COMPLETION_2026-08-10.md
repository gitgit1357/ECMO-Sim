# Clinical Behavior Contract 04 Completion — Ongoing Major Bleeding / Hemorrhage

**Date:** 2026-08-10  
**Contract:** `cbc.patient.ongoing-major-bleeding.v1`  
**Legacy reference:** `ce-06-major-bleeding`

## Decision

CBC04 protects only behavior the current Python patient actually owns: cumulative authoritative blood-volume loss, serial worsening while loss continues, partial improvement when replacement does not fully catch up, resumed deterioration when another loss event occurs, and stateful recovery after further loss ceases and the remaining net volume deficit is replaced.

CBC04 does **not** create a generic hemorrhage-severity variable or a persistent bleeding-rate state. It does not model coagulopathy, platelet/factor consumption, hemoglobin/RBC-mass loss, blood-component transfusion effects, or surgical/hemostatic source control.

## Canonical automated path

- 3.0 kg unified neonatal patient on VA ECMO.
- Pump 2200 RPM, sweep 600 mL/min, bridge closed.
- Three serial blood-loss increments, each 5% of modeled baseline blood volume.
- After the second increment, replace 50% of one loss increment intravascularly.
- Apply the third loss increment to prove that deterioration resumes while loss continues.
- Stop generating additional blood-loss events and replace the remaining net intravascular deficit.

The percentage values are reproducible regression stimuli only and are not clinical definitions of major hemorrhage or transfusion dosing.

## Required automated relationships

Serial net blood loss must progressively lower blood-volume/preload fraction, patient-directed ECMO flow, MAP, and CVP while making drainage pressure more negative. Partial replacement must improve those variables without restoring the euvolemic baseline when cumulative loss still exceeds replacement. A subsequent loss event must worsen them again.

After no further loss occurs, replacing the remaining net volume deficit in the **same mutable patient object** must restore the isolated baseline approximately. This is a genuine volume-ledger state-reversal check; it does not reconstruct the patient or patch monitor values.

## State-model boundary

CBC04 v1 represents ongoing bleeding as repeated calls to `UnifiedNeonatalPatient.record_blood_loss()`. There is currently no `bleeding_active` flag, bleeding-rate integrator, or hemostatic action. Therefore "bleeding cessation" in CBC04 means **no further blood-loss calls are made**.

That is a named future invalidation condition. If persistent bleeding state/rate or explicit source-control actions are added, CBC04 must be rewritten so cessation and recurrence are tested through those mechanisms rather than through absence/presence of calls.

## External clinical framing

ELSO's public ECMO material identifies bleeding as a major/common ECMO complication and notes that bleeding may occur at cannula/surgical sites or elsewhere. ELSO also publishes adult/pediatric anticoagulation guidance. CBC04 deliberately does not infer a universal bleeding-rate threshold or treatment dose from that framing; institutional and expert review remain separate from the automated model relationship.

## Source-change discipline

CBC04 required **no physiology source change**. It is a behavior contract over the existing authoritative volume ledger and coupled VA-ECMO response.

# Clinical Behavior Contract — Hypovolemia / Preload-Limited ECMO Low Flow v1

**Contract ID:** `cbc.lowflow.hypovolemia.v1`  
**Scenario family:** `lowflow-hypovolemia` (`legacy_id: lf-01-preload`)  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending  

## Purpose

Protect the learner-facing bedside relationship for hypovolemia/preload limitation on VA ECMO without pinning the simulator to one exact physiologic value.

The contract asks whether the current authoritative patient/circuit model behaves coherently when intravascular volume falls, when volume is restored, and when RPM is increased against a drainage-limited circuit.

## Preconditions

- 3.0 kg unified neonatal patient.
- VA ECMO configuration.
- Pump at 2200 RPM, sweep 600 mL/min.
- Bridge closed for the canonical regression path.
- Baseline state is not chattering.
- No additional modeled complication is active.

The 2200-RPM baseline is intentional. At higher RPM the current 3 kg baseline can already be near a drainage-demand boundary, which would confound the contract by starting too close to chatter.

## Regression stimulus

Remove **15% of modeled baseline blood volume** through `UnifiedNeonatalPatient.record_blood_loss()`.

This percentage is a stable automated-test stimulus. It is **not** being declared a clinically validated neonatal hemorrhage threshold.

## Required response to volume loss

With the preconditions above, the true authoritative state must show:

1. preload fraction decreases;
2. patient-directed ECMO flow decreases;
3. drainage pressure becomes more negative;
4. MAP decreases;
5. CVP decreases.

The contract does not require chatter at the moderate baseline RPM.

## Required response to equal intravascular replacement

Replacing the removed volume through the authoritative intravascular-input mechanism must return preload, patient-directed flow, drainage pressure, MAP, and CVP to approximately baseline. The automated tolerance is 1% relative error.

This checks reversibility and guards against scenario code that merely patches displayed numbers.

## RPM-escalation branch

While the patient remains volume depleted, raise pump speed from 2200 to 3000 RPM.

Required behavior:

- drainage pressure becomes substantially more negative;
- chatter may/does activate for this canonical stimulus;
- patient-directed ECMO flow must not improve by more than 2% while the circuit remains drainage-limited;
- MAP must not recover to the original euvolemic baseline solely because RPM was increased.

This is the key teaching relationship: **more RPM is not equivalent to more effective patient flow when venous drainage/preload is limiting.**

## Allowed exceptions / scope

- Different RPM, cannula, patient-size, or volume combinations may not chatter.
- Extreme vasoplegia or additional pathology can change MAP direction/magnitude and needs its own contract.
- Opening bridge/shunt paths can change gross circuit flow without increasing patient drainage capacity.
- Learner-displayed values may lag the true state because the dynamic display layer intentionally smooths monitor response.
- This contract does not yet claim a validated resuscitation volume, transfusion strategy, or clinical treatment endpoint.

## Exit criteria

The contract is **automated/passing** when all directional and recovery assertions pass against the authoritative model. It becomes **clinically validated** only after expert review accepts the preconditions, expected relationships, and allowed exceptions.

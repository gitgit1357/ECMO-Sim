# Coupling Stage 6 — Dynamic response and consequence signals

Added `neoecmocoupling.dynamics` around the Stage-5 time-stepped coordinator.

## Design boundary

- The Stage-5 coordinator remains authoritative for patient and ECMO physiology.
- Stage 6 owns elapsed simulation time, learner-display response, and advisory timing only.
- True values remain immediately available for safety logic and scenario consequences.
- Displayed values are intentionally smoothed and may lag true values.

## Display response

Default isolated behavior settings:

- Patient and total ECMO flow: 15-second response constant
- Circuit and patient pressures: 4-second response constant
- Patient oxygenation: 12-second response constant
- Patient CO2: 18-second response constant

These are provisional simulator behavior settings, not device specifications.

## Advisories

The first reduced-order consequence signals are:

- LOW EFFECTIVE VENOUS VOLUME
- DRAINAGE CHATTER
- LOW PATIENT-DIRECTED ECMO FLOW
- EXCESSIVE NEGATIVE DRAINAGE PRESSURE

Thresholds are isolated in `DynamicResponseConfig` for later clinical/scenario tuning.

## Chatter timing

True chatter is available immediately to the simulation engine. The learner-facing chatter indication has configurable activation and clearing delays to avoid one-frame flicker.

## Validation

- 6 new Stage-6 dynamic tests passed.
- 16 existing Stage-3/4/5 hydraulic, MAP, preload, and time-step tests passed.

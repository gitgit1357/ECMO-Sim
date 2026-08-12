# ECMO Learner Workspace GUI v0.2

This iteration uses only `neonatal-modular-patient-COMPLETE-HANDOFF-2026-07-27.zip` as its canonical model base.

## Functional controls

- Pump start / stop
- Commanded RPM: ±50, ±100, and direct entry
- Sweep gas: ±0.05 L/min, ±0.10 L/min, and direct entry from 0.00–10.00 L/min
- FdO2: ±5%, ±10%, and direct entry from 21–100%
- Bridge opening: close, ±10%, and fully open
- Shunt configuration
- Scuffing / filtration state

## Live solver-driven displays

- Total circuit flow
- Patient flow
- Shunt flow
- Bridge flow
- Actual RPM
- P1, P2, P3
- Oxygenator delta pressure
- Pump head and junction pressure difference
- Post-oxygenator saturation and PaCO2
- CDI SvO2, PCO2, and recirculation fraction

## Reserved, not yet functional

- Main circuit clamp
- Drain and return cannula clamps
- Flow-probe relocation
- Bubble-detector state and reset
- General alarm logic
- Patient-monitor integration

Reserved controls are visibly labeled `NOT YET MODELED` and do not silently accept learner input.

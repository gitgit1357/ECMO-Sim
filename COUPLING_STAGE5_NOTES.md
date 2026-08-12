# Coupling Stage 5 — Time-stepped VA-ECMO patient integration

Added `neoecmocoupling.time_step.CoupledVaEcmoPatient` as a separate coordinator.

## Implemented behavior
- Solves the live patient boundary against the volume-limited VA-ECMO circuit.
- True patient-directed ECMO drainage can reduce native cardiac contribution through a bounded preload-diversion rule.
- True arterial ECMO return supports patient MAP and systemic flow.
- Patient arterial gases use ECMO-return blood mixed with the remaining native cardiac contribution.
- Renal urine and CKRT net fluid removal update the compact volume ledger over time.
- The next ECMO solve consumes the updated effective venous volume and can worsen drainage limitation/chatter.
- Bridge and shunt recirculation remain excluded from systemic support.

## Deliberate scope
This is a reduced-order teaching model. It does not attempt beat-to-beat ventricular mechanics, detailed venous collapse, or exact patient-specific pressure-volume physiology. All response gains are isolated for later scenario-specific tuning.

## Validation
- 4 new integrated time-step tests passed.
- 22 existing hydraulic, closed-loop MAP, preload, and coupling-contract tests passed.
- Some older full-patient tests remain slow enough to exceed the execution window; no failure was observed before timeout.

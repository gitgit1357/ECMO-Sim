# Phase 2d Ventilator Contract

Date: 2026-08-10  
Roadmap authority: `FIX_MAP_v4.md` Phase 2 — Patient Monitor -> Interventions -> Labs -> **Ventilator** -> Scenario Log.

## Purpose

Phase 2d turns the Ventilator tab into a learner-operable surface only after extending the authoritative airway backend. The GUI must never expose rate or inspiratory-time controls that are presentation-only.

## Supported production mode

`neoventilator.PressureControlSettings` is the production pressure-control contract. It owns the deterministic airway pressure waveform and these learner settings:

- PIP (cmH2O)
- PEEP (cmH2O)
- respiratory rate (/min)
- inspiratory time (s)
- FiO2 (0.21-1.00)

The object does **not** own lung physiology. `neolung` continues to own mechanics and gas exchange; `neocoupling` applies the ventilator waveform to the lung solve.

Native/spontaneous breathing remains the unchanged default when `AirwayPort.pressure_control is None`.

## Integration rules

1. `AirwayPort` may carry an optional immutable pressure-control settings object.
2. The native-physiology cache key includes every pressure-control setting that can change the equilibrium.
3. The asynchronous worker reconstructs pressure control from primitive cache-key values; no live patient object crosses the process boundary.
4. Pressure control suppresses the model's spontaneous inspiratory muscle swing and drives airway opening pressure with the ventilator waveform.
5. The production pressure-control solve uses at least 20 s of internal lung stepping so the existing trailing 15 s lung-metric window excludes startup transients. This is an equilibrium calculation and does not advance learner simulation time.
6. Unified patient snapshots expose modeled respiratory rate, tidal volume, minute ventilation, and active ventilator mode.
7. Learner changes emit structured `control.changed` events targeting `ventilator`.
8. The Ventilator GUI contains no physiology equations or direct patient/monitor patches.

## Learner-visible behavior

The Ventilator tab provides pressure-control settings and modeled delivery/patient readback. PIP and rate changes must reach actual lung mechanics/gas exchange rather than merely updating labels. FiO2 must reach native gas exchange.

The tab indicates when native physiology is recalculating; during that interval readback may be the last-known equilibrium and is visibly marked `updating`.

## Explicitly not modeled in Phase 2d

- volume-control ventilation
- pressure support / patient-trigger synchrony
- SIMV or other named device modes
- ventilator alarm engine
- ETCO2 monitoring
- dynamic ventilator waveform display
- persistent recruitment/derecruitment state
- barotrauma/VILI
- pneumothorax
- device-specific delivered-volume accuracy

## Existing behavior-contract limitation remains binding

CBC07 remains unresolved for **PEEP-to-ECMO drainage coupling**. The VA preload interface consumes measured CVP and does not yet distinguish transmural venous pressure from intrathoracic pressure. Phase 2d therefore does not claim that the modeled direction/magnitude of ECMO drainage response to ventilator PEEP is clinically valid.

## Exit criteria

Phase 2d is complete when:

- pressure-control settings are production code, not bench-only;
- PIP/PEEP/rate/Ti/FiO2 are integrated through `UnifiedNeonatalPatient`;
- the spawned native solver reconstructs pressure-control settings correctly;
- the Ventilator tab is learner-operable and readback comes from authoritative state;
- prior static airway/PEEP behavior remains regression-clean;
- unsupported ventilator features remain explicit rather than simulated by surrogates.

# Clinical Behavior Contract 09 Completion — Bridge Recirculation / Flow Diversion

**Date:** 2026-08-10  
**Contract:** `cbc.ecmo.bridge-recirculation-flow-diversion.v1`  
**Status:** automated behavior contract implemented/passing; expert clinical review pending

## Decision

CBC09 was selected from the living capability matrix because bridge management is already authoritative, integrated, learner-operable, and independently represented in the circuit, VA MAP coupling, and venous CDI model.

The contract protects bridge recirculation as a diversion of circuit flow rather than patient support. It does not define a clinical bridge-flow prescription or persistent bridge fault.

## Defect discovered during probing

`solve_bridge_clamp_position_for_target_flow()` correctly included live patient arterial pressure, venous pressure, and residual patient-path resistance while root-finding the clamp position. After finding that clamp position, however, the final returned operating point was recomputed without those live patient-boundary arguments.

In the coupled VA model this caused target misses: before repair, requested bridge targets of 25/50/100 mL/min could return approximately 30/60/120 mL/min at the settled live boundary.

## Narrow repair

The final `solve_main_circuit_full_operating_point()` call now receives the same:

- `patient_arterial_pressure_mmhg`
- `patient_venous_pressure_mmhg`
- `live_patient_residual_vasculature_resistance_mmhg_per_ml_min`

used during the root search.

No pump, cannula, shunt, bridge-resistance, MAP-support, CDI-mixing, or patient-physiology equations were changed.

## Canonical probe after repair

At 3000 RPM with a 3.0 kg reduced-order VA boundary (MAP 42 mmHg, CVP 5 mmHg, native output 300 mL/min, venous saturation 0.65, venous pCO2 55 mmHg):

| Requested bridge flow | Solved bridge flow | Patient ECMO flow | Settled MAP | CDI saturation | CDI pCO2 | CDI recirc fraction |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.000 | 547.70 | 51.12 | 0.6500 | 55.00 | 0.0000 |
| 25 | 25.000 | 539.85 | 50.99 | 0.6655 | 53.80 | 0.0443 |
| 50 | 49.999 | 531.89 | 50.85 | 0.6800 | 52.70 | 0.0859 |
| 75 | 74.998 | 523.82 | 50.72 | 0.6938 | 51.70 | 0.1252 |
| 100 | 100.000 | 515.64 | 50.58 | 0.7068 | 50.79 | 0.1624 |
| 150 | 150.002 | 498.93 | 50.30 | 0.7308 | 49.18 | 0.2312 |

Exact magnitudes are reduced-order regression outputs. The protected relationships are target-flow accuracy under the live boundary, reduced patient-directed support with increasing bridge recirculation, branch conservation, and the expected CDI mixing direction.

## Learner-facing interpretation

CBC09 protects a multi-signal relationship:

- total pump flow is not equivalent to systemic support;
- bridge flow never counts as patient return;
- increasing bridge flow can reduce patient-directed ECMO support and MAP;
- the venous CDI can simultaneously look more oxygenated and less hypercarbic because it is increasingly contaminated by bridge-recirculated post-oxygenator blood.

This is bridge-specific recirculation and is not a VV recirculation model.

## Restoration semantics

Returning the bridge target to zero reproduces the closed-bridge solution for the same immutable patient/control boundary. This is deterministic control reversal, not proof of recovery from a persistent accidental-unclamping, bridge-clot, or stopcock fault.

## Source changes

Exactly one non-generated source file differs from v0.17.11:

- `src/neoecmo/main_circuit_full.py`

## Files added/changed for CBC09

- `clinical_behavior_contracts/BRIDGE_RECIRCULATION_FLOW_DIVERSION_V1.md`
- `clinical_behavior_contracts/bridge_recirculation_flow_diversion_v1.json`
- `tests/test_clinical_behavior_contract_bridge_recirculation.py`
- `tests/test_bridge_clamp_inverse_solver.py` (one live-boundary regression added)
- capability matrix mirrors updated

## Capability matrix

The living matrix now contains 74 unique rows and continues to embed the unchanged Phase 1b backing inventory: 79 actions / 36 complications / 28 scenario ID migrations.

## Fresh verification

Zero-exit bounded batches:

- CBC01-CBC09: 37/37 passed
- bridge / inverse solver / CDI / closed-loop VA / coupled time-step / workspace bridge regressions: 50/50 passed

**Total fresh zero-exit verification: 87 passed, 0 failed.**

The exact tree collects **387 tests**.

# Clinical Behavior Contract 08 Completion — ECMO FdO2 Oxygen-Fraction Control

**Date:** 2026-08-10  
**Contract:** `cbc.ecmo.fdo2-oxygen-fraction-control.v1`  
**Status:** automated behavior contract implemented/passing; expert clinical review pending

## Decision

CBC08 was selected from the living capability matrix because ECMO FdO2 is already an authoritative, integrated, learner-operable control and CBC02 had deliberately left FdO2-only behavior separate from sweep-gas failure.

The contract is limited to the membrane/console boundary. It does not create a persistent blender/oxygen-source fault and does not assert a coupled-patient oxygenation response while the patient-to-ECMO adapter still uses arterial saturation as a temporary venous surrogate.

## Defect discovered during probing

Before CBC08, `outlet_o2_saturation()` and `outlet_po2_mmhg()` were independent reduced-order transfer approximations. With representative inlet saturation 0.65 and fixed nonzero sweep, intermediate FdO2 settings could therefore report a venous-like post-oxygenator saturation while simultaneously reporting a strongly oxygenated pO2.

That was an internal state-coherence defect rather than a clinical threshold problem.

## Narrow repair

`outlet_po2_mmhg()` remains the existing provisional FdO2/transfer-efficiency calculation. A new `saturation_from_po2_mmhg()` helper implements the inverse of the existing Hill approximation, and `outlet_o2_saturation()` now derives saturation from the same outlet pO2 state.

The repair does not change blood-side hydraulics, sweep-driven CO2 clearance, FdO2 blender limits/rounding, or the provisional device-specific pO2 targets. It removes the contradictory dual-O2-state representation.

## Canonical probe after repair

At 2200 RPM, 600 mL/min sweep, bridge closed, inlet saturation 0.65, and inlet pCO2 58 mmHg:

| FdO2 | post-oxy pO2 (mmHg) | post-oxy O2 sat | post-oxy pCO2 (mmHg) | patient flow (mL/min) |
|---:|---:|---:|---:|---:|
| 1.00 | 450.00 | 0.99951 | 20.00 | 243.185 |
| 0.80 | 361.39 | 0.99911 | 20.00 | 243.185 |
| 0.60 | 272.78 | 0.99810 | 20.00 | 243.185 |
| 0.40 | 184.18 | 0.99454 | 20.00 | 243.185 |
| 0.21 | 100.00 | 0.97222 | 20.00 | 243.185 |

The exact magnitudes remain reduced-order/provisional. The protected behavior is direction and internal consistency: lower FdO2 lowers the modeled outlet O2 state while fixed sweep preserves modeled CO2 clearance and fixed blood-side conditions preserve flow.

## Coupled-patient boundary remains blocked

A direct coupled probe still shows the existing limitation: the patient-to-ECMO adapter supplies near-fully-saturated patient arterial blood as the temporary venous inlet state. Because the oxygenator model does not actively deoxygenate blood whose inlet pO2 already exceeds the FdO2-derived target, changing FdO2 can be completely masked in the coupled patient.

CBC08 therefore adds/retains an explicit blocked capability for `FdO2-to-coupled-patient oxygenation via true venous inlet state`. This requires an authoritative central-venous oxygen state before a coupled CBC is legitimate.

## Restoration semantics

Restoring FdO2 to 1.00 reproduces the baseline membrane result. As with CBC03/CBC05A, this is immutable-control deterministic re-evaluation, not proof of stateful blender/gas-source fault recovery. A future persistent fault mechanism must be tested through activation and clear/reset in the same runtime state.

## Source changes

Only two non-generated files under `src/` differ from v0.17.10:

- `src/neoecmo/oxygenator_gas_exchange.py`
- `src/neoecmo/__init__.py`

The second change exports the new inverse Hill helper.

## Files added

- `clinical_behavior_contracts/FDO2_OXYGEN_FRACTION_CONTROL_V1.md`
- `clinical_behavior_contracts/fdo2_oxygen_fraction_control_v1.json`
- `tests/test_clinical_behavior_contract_fdo2.py`

The prior gas-exchange unit test that encoded an obsolete absolute saturation cutoff was changed to protect the actual invariant: transfer at far-above-rated blood flow must be worse than at low flow under otherwise identical conditions.

## Capability-matrix changes

The living matrix now:

- marks ECMO FdO2 control as CBC08 automated/passing;
- updates oxygenator gas exchange to include the single-state O2 coherence guarantee;
- adds CBC08 as its own contract capability;
- explicitly blocks coupled-patient FdO2 behavior pending a true venous oxygen state.

Phase 1b backing data remain unchanged at 79 actions / 36 complications / 28 scenario IDs.

## Fresh verification

Zero-exit bounded batches:

- CBC01-CBC08 contracts: 32/32 passed
- gas exchange / console / post-oxy CDI / oxygenator regressions: 76/76 passed
- coupled patient / cache / preload / MAP regressions: 27/27 passed
- workspace / ready scenarios / Tier-A / scenario primitives: 44/44 passed

**Total fresh zero-exit verification: 179 passed, 0 failed.**

The exact tree collects **381 tests**. Source comparison against v0.17.10 confirms **93 non-generated source files**, with exactly the two intended files above modified.

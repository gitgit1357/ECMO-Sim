# Clinical Behavior Contract 03 Completion — Oxygenator Dysfunction

**Date:** 2026-08-10  
**Contract:** `cbc.ecmo.oxygenator-dysfunction.v1`  
**Legacy reference:** `ce-03-oxygenator`

## Decision

CBC03 does not model one generic "oxygenator failure" switch. It protects only two behaviors already present in the Python model and keeps them explicitly separable:

1. blood-path obstruction / hydraulic burden;
2. membrane gas-transfer impairment.

This preserves a clinically useful troubleshooting distinction and avoids forcing a synthetic one-to-one relationship between pressure gradient and exchange failure.

## Automated behavior

### Hydraulic branch
At fixed 2200 RPM and otherwise unchanged circuit settings, moving the internal hydraulic obstruction proxy from 0.0 to 0.60 must:

- increase oxygenator `P2-P3` pressure drop;
- reduce total ECMO circuit flow;
- reduce patient-directed ECMO flow;
- return to baseline when clean hydraulic parameters are restored.

### Gas-transfer branch
At fixed 1400 mL/min blood flow, inlet saturation 0.65, inlet pCO2 58 mmHg, FdO2 1.0, and sweep 600 mL/min, moving the gas-transfer obstruction proxy from 0.0 to 0.60 must:

- lower post-oxygenator saturation;
- lower post-oxygenator pO2;
- reduce CO2 clearance / raise post-oxygenator pCO2;
- return to baseline when clean gas-transfer parameters are restored.

The fixed-flow branch intentionally isolates membrane performance from the hydraulic reduction in flow.

## Validation boundary

The obstruction fraction is an internal reduced-order regression variable, not a measurable clot percentage. No universal oxygenator delta-P threshold, exchange threshold, lifetime, or replacement criterion is asserted. Device-specific pressure-flow and gas-transfer magnitudes remain provisional. Expert clinical review remains separate from automated behavior-contract status.

## External source framing

- Eurosets describes its infant/newborn oxygenator family as a blood oxygenator with gas-transfer function and publishes newborn ECMO configurations as a distinct device class. The public product pages do not provide the detailed AMG PMP Infant pressure-flow/transfer curves needed to validate the simulator's numeric proxy coefficients.
- ELSO separately recognizes oxygenator failure and circuit-component thrombosis/clots as ECMO complications. CBC03 therefore preserves the distinction between a modeled oxygenator dysfunction signature and a universal diagnostic threshold.

## CBC02 conversational-number correction carried forward

A conversational summary during CBC02 referred to approximately 760 mmHg when describing the pre-fix oxygenator output. The packaged model's explicit pure-O2 post-oxygenator target is 450 mmHg. CBC02's actual acceptance rule was qualitative (zero sweep must not continue O2 addition), so the numeric prose error did not affect its code or regression result. The CBC02 completion record now contains an append-only clarification.

## Source-change discipline

CBC03 required **no new physiology change**. It formalizes already-existing hydraulic and gas-transfer behavior. The only Python addition in this block is the CBC03 regression test.

## 2026-08-10 — Restoration-semantics clarification
CBC03's current "restoration" assertions are **pure-function determinism checks**, not state-reversal tests. `OxygenatorHydraulicParameters` and `OxygenatorGasExchangeParameters` are immutable values supplied fresh to deterministic model calls; restoring the baseline parameter object therefore re-evaluates the baseline function rather than clearing persistent oxygenator fault state.

This is acceptable for the current architecture, but it is a future invalidation/retest condition: if oxygenator dysfunction later becomes a persistent mutable scenario/device state, CBC03's recovery branch must be rewritten to activate and clear that real stateful fault. The current pure-function restoration assertion must not be treated as proof that a future fault-clear path works.

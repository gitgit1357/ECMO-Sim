# Clinical Behavior Contract 02 Completion — Complete Sweep-Gas Failure

**Date:** 2026-08-10  
**Contract:** `cbc.ecmo.sweep-gas-failure.v1`  
**Legacy scenario reference:** `ce-04-sweep-gas`

## Decision

CBC02 treats complete sweep-gas loss (`effective sweep = 0`) as loss of gas-side membrane exchange: no oxygen addition and no carbon-dioxide removal. This is deliberately narrower than oxygenator thrombosis, blood-path obstruction, or an FdO2-only failure.

## Model defect found and repaired

Before CBC02, `outlet_paco2_mmhg()` correctly returned inlet pCO2 when sweep was zero, but post-oxygenator oxygenation was still calculated from FdO2 and blood flow alone. Therefore the simulator could report a hyperoxic post-oxygenator pO2 despite zero sweep-gas flow.

The repair is intentionally narrow in `src/neoecmo/ecmo_console.py`:

- `sweep_gas_flow_ml_min > 0`: existing oxygenation and CO2 behavior unchanged;
- `sweep_gas_flow_ml_min <= 0`: post-oxygenator O2 state equals inlet venous O2 state and post-oxygenator pCO2 naturally equals inlet pCO2 through the existing CO2 model.

RPM and blood flow remain independent outcomes of the hydraulic solve; sweep does not become a flow control.

## Known coupled-patient limitation

The current unified-patient native venous saturation can calculate near 100% in the canonical baseline. That can mask the patient-level oxygenation consequence of sweep loss even though the membrane-boundary behavior is now correct. CBC02 therefore:

- asserts O2 transfer loss at a representative membrane inlet (SvO2 0.65);
- asserts patient pCO2 rise/recovery in the coupled patient;
- does **not** assert a coupled-patient pO2 fall in v1.

That limitation is left explicit for a future patient gas-state contract instead of being silently repaired as part of CBC02.

## Validation boundary

Automated behavior: passing.  
Expert clinical review: pending.  
Device-specific gas-transfer magnitude validation: still partial/proxy.

## Fresh verification

- CBC01 + CBC02 + console/gas behavior: 24 passed
- dynamic/time-step/coupling contracts: 15 passed
- native physiology cache/async: 5 passed
- hydraulic/MAP/preload: 17 passed
- bridge/fixed-shunt: 32 passed
- gas module/workspace/scenario primitive/catalog: 46 passed

**Total: 139 passed, 0 failed.**

## 2026-08-10 conversational-number clarification

A later review correctly noted a discrepancy in the conversational summary of CBC02: it referred to an approximately 760 mmHg pre-fix post-oxygenator PO2, while the current explicit `outlet_po2_mmhg()` pure-O2 target used by the packaged CBC02 model is **450 mmHg**. The contract and test artifacts do not rely on the 760 mmHg conversational value. The relevant defect was qualitative: zero sweep incorrectly retained oxygen addition. This clarification is append-only and does not alter CBC02 behavior.

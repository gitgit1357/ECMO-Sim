# Clinical Behavior Contract 01 Completion — Hypovolemia / Preload-Limited Low Flow

**Date:** 2026-08-10  
**Contract:** `cbc.lowflow.hypovolemia.v1`  
**Automation:** PASS  
**Clinical expert review:** PENDING

## What was added

- Machine-readable contract: `clinical_behavior_contracts/hypovolemia_preload_low_flow_v1.json`
- Human-readable contract: `clinical_behavior_contracts/HYPOVOLEMIA_PRELOAD_LOW_FLOW_V1.md`
- Automated regression: `tests/test_clinical_behavior_contract_hypovolemia.py`
- Capability matrix updated as the single living status authority.

## Empirical canonical behavior

For the 3.0 kg baseline at 2200 RPM / sweep 600 mL/min, the model starts without chatter. Removing 15% of modeled baseline blood volume (38.7 mL with the current 86 mL/kg default) produces the required directional response: lower preload, lower patient-directed ECMO flow, lower MAP, lower CVP, and more-negative drainage pressure.

With volume still depleted, increasing RPM to 3000 drives drainage pressure to the suction-limited region and activates chatter while patient-directed flow remains drainage-limited rather than meaningfully increasing. Returning RPM to baseline and replacing the removed intravascular volume restores the isolated model state to baseline within the contract tolerance.

## Important validation boundary

The 15% loss is an automated regression stimulus selected to exercise the mechanism clearly and reproducibly. It is not a claim that 15% blood loss is a validated neonatal clinical threshold, nor does this contract prescribe a resuscitation dose. Passing the test means the software produces the agreed direction/range behavior under stated preconditions. Clinical expert acceptance remains separate.

## Model changes

None. The existing physiology/coupling behavior already satisfied the first contract; only contract artifacts, tests, capability status, and handoff documentation were added.

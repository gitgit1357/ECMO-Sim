# Clinical Behavior Contract — Oxygenator Dysfunction v1

**Contract ID:** `cbc.ecmo.oxygenator-dysfunction.v1`  
**Scenario family:** `circuit-oxygenator-dysfunction` (`legacy_id: ce-03-oxygenator`)  
**Automation status:** implemented and regression-tested  
**Clinical review status:** expert review pending

## Purpose

Protect two learner-facing relationships that the current reduced-order oxygenator model can genuinely represent without collapsing every membrane-lung problem into one generic failure state:

1. **blood-path obstruction / rising hydraulic resistance**, and
2. **loss of effective membrane gas-transfer capacity**.

CBC03 deliberately tests those branches separately. It does **not** assert that a particular pressure gradient proves membrane failure, that every clot produces the same gas-transfer defect, or that gas-transfer failure must be accompanied by a large pressure rise.

## Clinical framing

An oxygenator is both a blood-path hydraulic component and a membrane gas-exchange component. A deteriorating oxygenator may therefore present through changing blood-side pressure/flow behavior, impaired gas exchange, or both. The bedside interpretation depends on trends, blood flow, gas settings, inlet blood state, and the rest of the circuit rather than a single universal threshold.

The current simulator intentionally uses reduced-order proxy parameters. Device-specific pressure-flow curves and transfer performance remain outside this contract.

## Branch A — blood-path obstruction / hydraulic burden

### Preconditions

- Pump RPM: 2200.
- Sweep: 600 mL/min.
- FdO2: 1.0.
- Bridge closed.
- Representative venous inlet saturation: 0.65.
- Representative venous inlet pCO2: 58 mmHg.
- Clean oxygenator hydraulic obstruction fraction: 0.0.

### Stimulus

Increase the oxygenator hydraulic obstruction proxy to **0.60** while leaving pump RPM and the rest of the circuit unchanged.

The value 0.60 is a regression stimulus chosen to produce a clear, reproducible model response. It is **not** a clinical clot-burden percentage and has no bedside numeric interpretation.

### Required response

At fixed RPM:

1. oxygenator blood-side pressure drop (`P2 - P3`) increases;
2. solved total circuit flow decreases;
3. patient-directed ECMO flow decreases;
4. restoring the clean hydraulic parameter returns those values approximately to baseline.

### Explicit non-rules

- No universal ΔP threshold is defined.
- A high ΔP alone does not diagnose oxygenator failure.
- The contract does not require gas-transfer impairment to occur in lockstep with the hydraulic branch.
- Learners should interpret a pressure-gradient **trend at the prevailing flow**, not a single isolated number.

## Branch B — membrane gas-transfer impairment

### Preconditions

To isolate gas-transfer capacity from the hydraulic consequence of obstruction, this branch holds blood flow fixed at **1400 mL/min** and uses:

- inlet saturation 0.65;
- inlet pCO2 58 mmHg;
- FdO2 1.0;
- sweep 600 mL/min;
- clean gas-transfer obstruction proxy 0.0.

These are test fixtures, not treatment targets.

### Stimulus

Increase the gas-transfer obstruction proxy to **0.60** while holding blood flow and gas settings fixed.

Again, 0.60 is an internal model stimulus, not a clinically measurable obstruction fraction.

### Required response

Compared with the clean membrane at the same blood flow and gas settings:

1. effective oxygen transfer decreases;
2. post-oxygenator O2 saturation decreases;
3. post-oxygenator pO2 decreases;
4. CO2 clearance decreases;
5. post-oxygenator pCO2 increases;
6. restoring the clean gas-transfer parameter returns gas outputs approximately to baseline.

## Why the branches are separated

In the present console model the hydraulic and gas-transfer parameters are distinct inputs even though they conceptually describe the same physical oxygenator. More importantly, rising blood-path resistance can reduce actual blood flow; lower flow can partially mask the gas-transfer impairment of a reduced membrane area in a reduced-order model. CBC03 therefore does not use a single coupled obstruction number to manufacture a predetermined combined bedside signature.

A future typed oxygenator fault mechanism may coordinate these domains, but only after its clinical behavior contract defines how the two evolve together.

## Scope / allowed exceptions

- Complete sweep-gas loss is CBC02, not CBC03.
- FdO2-only failure is distinct.
- Acute circuit rupture, air entrainment, pump failure, and cannula obstruction are distinct mechanisms.
- Clot appearance, hemolysis, D-dimer/fibrin trends, and laboratory evidence are not implemented by this contract.
- A clinically important oxygenator can fail gas exchange without a dramatic pressure-gradient rise; CBC03 intentionally does not prohibit that.
- Pressure-drop magnitudes and gas-transfer magnitudes remain provisional/device-specific proxies.
- The unified patient's current venous-gas limitation remains outside this contract; membrane gas behavior is tested at the oxygenator boundary.

## Validation boundary

Passing CBC03 demonstrates directional coherence of the simulator's **existing reduced-order hydraulic and gas-transfer behaviors**. It does not validate a specific oxygenator's clot threshold, exchange lifetime, pressure-drop limit, or replacement criterion. Expert clinical review and device-specific validation remain separate.

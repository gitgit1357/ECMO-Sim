# Priority-A Evidence Review Packet 02 — CBC02 Complete Sweep-Gas Failure

**Packet ID:** `phase5.validation.cbc02.evidence.v1`  
**Contract:** `cbc.ecmo.sweep-gas-failure.v1`  
**Prepared:** 2026-08-10  
**Product position:** simulation / training only  
**Disposition:** **external evidence packet complete; expert sign-off pending**

## 1. Review purpose

This packet asks whether external evidence supports the directional learner-facing relationships protected by CBC02 strongly enough to take the contract to expert review.

It does **not** validate the current regression sweep value, gas-transfer magnitudes, device-specific oxygenator performance, a clinical alarm threshold, or an instantaneous physical response at the exact moment sweep flow reaches zero.

## 2. Evidence hierarchy used

### Source A — ELSO ECMO circuit/gas-exchange framework

Extracorporeal Life Support Organization. **ELSO Guidelines for Adult and Pediatric Extracorporeal Membrane Oxygenation Circuits.** Current ELSO guideline index lists the circuit guideline as last updated February 2022.

ELSO's public ECMO educational material describes the oxygenator as the site where oxygen enters blood and carbon dioxide leaves blood through the gas side. This supports treating loss of effective gas-side flow as a gas-exchange failure rather than a blood-flow failure.

### Source B — primary clinical physiology: sweep controls CO2 removal

Schmidt M, et al. **Blood oxygenation and decarboxylation determinants during venovenous ECMO for respiratory failure in adults.** Intensive Care Medicine. 2013. PMID: `23291732`.

The published abstract identifies ECMO blood flow as the main determinant of oxygenation and sweep-gas flow as a determinant of CO2 elimination. This directly supports CBC02's nonzero-sweep rule: ordinary sweep titration is primarily a CO2-control mechanism rather than a blood-flow control.

### Source C — multi-system clinical oxygenator analysis

Lehle K, et al. **Technical performance of ECMO systems: analysis of 317 cases with four different ECMO systems.** 2014. PMID: `25323118`.

The published abstract reports that CO2 removal depended on sweep-gas flow and blood flow, with greater gas flow increasing CO2 elimination. This supports the direction of the sweep-to-CO2 relationship while also reinforcing that gas-transfer magnitude is device/system dependent.

### Source D — sweep-gas-off clinical trials

Na SJ, et al. **Duration of sweep gas off trial for weaning from venovenous extracorporeal membrane oxygenation.** Therapeutic Advances in Respiratory Disease. 2019;13:1753466619888131. DOI: `10.1177/1753466619888131`; PMID: `31736407`.

Sweep-gas-off trials are used clinically while maintaining extracorporeal blood flow to assess native lung function. The study reports significant blood-gas changes within the first hour after sweep was stopped. This supports CBC02's separation of blood flow from gas-side support.

### Source E — transient oxygen washout after sweep is stopped

Tahara T, et al. **A Novel Method for Predicting Recirculation by Sweep-Gas-Off Test.** Annals of Thoracic and Cardiovascular Surgery. 2026.

The in-vitro/animal work describes an early period after sweep is stopped in which post-oxygenator saturation falls toward pre-oxygenator saturation rather than changing instantaneously. This is important for CBC02: the simulator's zero-sweep acceptance state should be read as a **post-transient effective-zero-sweep equilibrium**, not a validated millisecond-by-millisecond gas-compartment washout model.

### Source F — manufacturer oxygenator performance boundary

Medtronic. **Nautilus ECMO oxygenator with Balance biosurface.** Public product information identifies oxygen transfer and carbon-dioxide transfer as distinct performance characteristics and directs users to the device instructions for use for operating details.

This supports keeping device-specific transfer curves and operating limits outside CBC02 unless a specific oxygenator/IFU is adopted as the training target.

## 3. Claim-by-claim disposition

| CBC02 behavior | Evidence disposition | Phase-5 decision |
|---|---|---|
| Sweep-gas flow is a primary control of membrane CO2 removal | **Strongly supported** by clinical physiology and multi-system data | Keep |
| Loss of effective sweep should not materially change the blood-side circuit flow by itself | **Supported by circuit separation**: gas flow and blood flow are distinct controls | Keep |
| At sustained effective zero sweep, membrane CO2 removal should cease | **Supported directionally** by sweep-off practice and gas-exchange physiology | Keep |
| At sustained effective zero sweep, post-oxygenator oxygenation should converge toward inlet state rather than remain indefinitely hyperoxic | **Supported as a steady/post-transient teaching state**; not validated as an instantaneous response | Keep, with transient caveat added |
| Ordinary nonzero sweep titration should predominantly affect CO2 rather than oxygenation | **Supported**; oxygenation is more strongly governed by blood flow, inlet O2 content, FdO2 and oxygenator function | Keep |
| Sweep loss alone should not be represented as blood-path obstruction or pump failure | **Supported by mechanism separation** | Keep |
| Coupled patient pCO2 should rise when extracorporeal CO2 removal is lost | **Directionally supported**, magnitude/time course patient-dependent | Keep directional rule; numeric recovery tolerance stays regression-only |
| Coupled patient pO2 fall is not asserted in v1 | **Appropriate limitation** because current model's venous inlet state can mask the effect | Keep blocked/non-claimed |

## 4. Contract refinement from evidence review

CBC02 now explicitly states that its zero-sweep membrane-boundary assertions represent a **sustained/effective-zero-sweep post-transient state**.

The simulator does **not** model the residual gas volume in the oxygenator or gas tubing, so it cannot represent the short washout period during which post-oxygenator oxygenation may remain temporarily elevated after sweep flow is stopped.

This refinement changes no physiology code and no regression target. It prevents the steady-state contract from being misread as an instantaneous device-time-response claim.

## 5. Numeric claims that remain explicitly unvalidated

The evidence review does **not** promote any of the following into clinical thresholds or prescriptions:

- 3.0 kg canonical patient size;
- 2200 RPM;
- 600 mL/min baseline/restored sweep;
- 0 mL/min as an alarm or procedural threshold rather than the modeled endpoint;
- FdO2 1.0;
- representative inlet saturation 0.65;
- representative inlet pCO2 58 mmHg;
- 0.5% blood-flow tolerance;
- 1% membrane-gas tolerance;
- 2% coupled-pCO2 recovery tolerance;
- any specific duration required before a zero-sweep state should be interpreted as equilibrated.

## 6. Expert-review questions carried forward

1. Is the teaching distinction correct: **sweep primarily controls CO2 clearance, while FdO2/blood flow/inlet oxygen state dominate oxygenation**?
2. Is it appropriate to represent sustained complete sweep loss as loss of effective membrane gas exchange while preserving blood-side flow?
3. Is the newly explicit residual-gas/washout caveat sufficient to prevent an instantaneous-response interpretation?
4. Should learner scenarios distinguish gas-source disconnection, blender failure and gas-line obstruction even when they converge on the same effective-zero-sweep endpoint?
5. Is the coupled-patient oxygenation limitation appropriately disclosed until an authoritative venous inlet state exists?
6. Are all regression numbers clearly separated from device operating specifications and bedside thresholds?

## 7. Final disposition

**CBC02 remains automated/passing. External evidence supports the core directional sweep/CO2 relationship and the use of sustained sweep-off as loss of extracorporeal gas support. Expert sign-off is still required. The zero-sweep oxygen assertion is explicitly post-transient rather than instantaneous.**

No CBC02 physiology source or acceptance tolerance is changed by this packet.

## 8. Future invalidation / retest conditions

Re-review CBC02 if:

- a dynamic gas-compartment/residual-volume model is added;
- a specific oxygenator and manufacturer IFU become the explicit training target;
- the unified patient gains an authoritative central-venous oxygen state;
- gas-source/blender/line-failure mechanisms become separate persistent scenario faults;
- oxygenator exhaust-gas sensing or additional gas-path alarms are added.

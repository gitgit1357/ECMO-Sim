# CBC08 FdO2 Oxygen-Fraction Control — External Evidence Review

**Date:** 2026-08-10  
**Contract:** `cbc.ecmo.fdo2-oxygen-fraction-control.v1`  
**Disposition:** **external evidence packet complete; expert sign-off pending**

## Review question

Does external evidence support CBC08's learner-facing separation that changing the oxygen fraction delivered to the membrane lung (FdO2/FbO2/FSO2) primarily changes extracorporeal oxygenation, while fixed sweep-gas flow preserves the CO2-removal control path and blood-side hydraulics remain independent of an FdO2-only change?

## Evidence summary

### 1. ELSO describes the gas blender as the oxygen-content control

ELSO's current ECMO overview describes the membrane oxygenator as adding oxygen and removing carbon dioxide and specifically depicts a **gas blender that changes oxygen content** on the gas side of the oxygenator. This supports the basic control identity used by CBC08: oxygen fraction delivered to the oxygenator is an oxygen-content control rather than a pump/hydraulic control.

- Extracorporeal Life Support Organization. *What is ECMO?*  
  https://www.elso.org/extracorporeal-membrane-oxygenation.aspx

This is an educational ELSO source, not a device-specific transfer curve or neonatal dose-response study.

### 2. ECMO gas-exchange literature separates FdO2-driven oxygenation from sweep-driven CO2 removal

Parekh, Abrams, and Brodie describe the gas supply as a mixture of oxygen and air with FdO2 set by a gas blender. Their review lists **fraction of oxygen delivered through the oxygenator** among the major determinants of oxygenation, while **sweep-gas flow rate** is the main determinant of carbon-dioxide removal at high blood flow. This directly supports the qualitative separation encoded by CBC08.

- Parekh M, Abrams D, Brodie D. *Extracorporeal techniques in acute respiratory distress syndrome.* Ann Transl Med. 2017;5(14):296. PMID: **28828371**. DOI: **10.21037/atm.2017.06.58**.  
  https://pubmed.ncbi.nlm.nih.gov/28828371/

This is a review, used for mechanism/control-role synthesis rather than quantitative device validation.

### 3. A randomized VA-ECMO trial directly manipulated oxygen fraction delivered to the oxygenator

The BLENDER randomized trial assigned adult VA-ECMO patients to conservative or liberal oxygen strategies using controlled oxygen administration through the ECMO gas blender. In the conservative arm, oxygen fraction delivered to the oxygenator was reduced and titrated to lower post-oxygenator oxygen targets. Reported post-oxygenator oxygen partial pressures/saturations were lower in the conservative group, while ECMO blood-flow values were similar between groups.

That is strong clinical support for CBC08's **directional/control-separation** assertion: changing gas-blender oxygen fraction can change post-oxygenator oxygenation without functioning as a blood-flow command.

- Burrell A, et al.; BLENDER Trial Investigators. *Conservative or liberal oxygen targets in patients on venoarterial extracorporeal membrane oxygenation.* Intensive Care Med. 2024;50(9):1470-1483. PMID: **39162827**. PMCID: **PMC11377512**. DOI: **10.1007/s00134-024-07564-8**.  
  https://pubmed.ncbi.nlm.nih.gov/39162827/

This trial is adult VA-ECMO evidence. It does not validate the simulator's neonatal transfer magnitudes or its reduced-order outlet-pO2 curve.

### 4. Post-oxygenator oxygenation depends on more than oxygen fraction alone

Winiszewski et al. emphasize that post-oxygenator oxygenation depends on several factors, including pre-oxygenator blood oxygen state, membrane-lung gas transfer, blood flow, and sweep-gas oxygen fraction. They also note that sweep **flow rate itself** has little effect on post-oxygenator PO2 across ordinary nonzero settings compared with its major effect on CO2 removal.

- Winiszewski H, et al. *Optimizing PO2 during peripheral veno-arterial ECMO: a narrative review.* Crit Care. 2022;26:226. PMID: **35883117**. DOI: **10.1186/s13054-022-04102-0**.  
  https://pubmed.ncbi.nlm.nih.gov/35883117/

This supports CBC08's decision to hold sweep flow and blood-side conditions fixed when isolating FdO2 behavior, and it reinforces that FdO2 should not be treated as the sole determinant of post-oxygenator oxygenation.

### 5. Manufacturer evidence supports gas exchange as the oxygenator function, not this simulator's transfer curve

Medtronic's public Nautilus ECMO product information identifies physiologic gas exchange as **oxygenation and carbon-dioxide removal** and directs users to the device instructions for use for operating details. It does not publicly validate CBC08's exact transfer curve or Hill-equation constants.

- Medtronic. *Nautilus ECMO oxygenator / Smart ECMO module product information.*  
  https://www.medtronic.com/en-us/products/product.48145E.html  
  https://www.medtronic.com/en-us/products/product.48135.html

Therefore manufacturer material supports only the device-function boundary here; quantitative transfer claims remain gated to device-specific IFU/performance evidence.

## Evidence disposition against CBC08

| CBC08 assertion | Evidence disposition |
|---|---|
| Lower oxygen fraction delivered to the oxygenator can lower post-oxygenator oxygenation | **Supported directionally**, including direct adult VA-ECMO gas-blender titration evidence |
| FdO2 is distinct from sweep-flow control of CO2 removal | **Supported as a core ECMO gas-exchange control distinction** |
| An FdO2-only change should not act as a pump-speed or blood-path resistance command | **Supported architecturally/physically**; BLENDER trial blood-flow similarity is consistent with this separation |
| Post-oxy saturation and pO2 should represent one internally coherent oxygen state | **Model-consistency requirement**, not an external clinical threshold claim |
| 1.00/0.80/0.60/0.40/0.21 are validated neonatal operating targets | **Not supported**; regression settings only |
| The model's exact post-oxy pO2/saturation values are device validated | **Not supported** |
| pCO2 must be numerically identical for every real-world FdO2 change | **Not established as a universal bedside equality**; retained as the isolated simulator regression expectation with sweep/blood conditions held fixed |
| Coupled-patient oxygenation response is validated | **No — explicitly blocked** until the patient-to-ECMO boundary has an authoritative central-venous oxygen state |

## Required contract interpretation

CBC08 should be read as a **controlled educational isolation of gas-control roles**:

> With sweep flow and blood-side conditions held fixed, reducing the oxygen fraction delivered to the membrane lung should reduce the modeled post-oxygenator oxygen state without behaving like a hidden sweep, RPM, or resistance control.

It should **not** be read as:

> The simulator's exact post-oxygenator PO2 curve predicts a specific neonatal ECMO oxygenator at each FdO2 setting.

The existing saturation-from-pO2 coherence rule remains an internal consistency rule. It prevents contradictory paired O2 outputs but is not evidence that the reduced-order curve is device-specific or clinically calibrated.

## Coupled-patient boundary remains open

CBC08 deliberately stops at the membrane boundary because the current patient-to-ECMO adapter uses arterial saturation as a temporary venous surrogate. External evidence does not justify bypassing that missing central-venous oxygen state with another proxy. A future coupled-patient FdO2 claim requires an authoritative venous inlet state and a new same-runtime behavior review.

## Expert-review questions still open

1. Is the FdO2-versus-sweep educational separation stated appropriately for neonatal ECMO training?
2. Should CBC08 preserve the current strict pCO2 invariance tolerance, or should expert review define an allowed nonzero interaction band while maintaining the control-role distinction?
3. Are the canonical FdO2 values acceptable purely as regression probe points without implying recommended bedside settings?
4. Is deriving saturation from the same modeled outlet pO2 acceptable as an internal-consistency requirement pending device-specific transfer validation?
5. Is the central-venous-state block strong enough before CBC08 is used for external learner training?

## Claim boundary

This packet does **not** establish:

- a neonatal FdO2 prescription or titration protocol;
- a post-oxygenator PO2 target;
- a device-specific oxygen-transfer curve;
- validation of the model's Hill constants or 450 mmHg pure-O2 target;
- exact independence of all real-world CO2 behavior from oxygen fraction;
- a validated coupled-patient oxygenation response;
- expert clinical sign-off or external-training approval.

**Final status:** external evidence packet complete; expert sign-off pending.

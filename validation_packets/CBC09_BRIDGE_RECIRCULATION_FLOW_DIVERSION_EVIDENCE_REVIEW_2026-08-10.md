# CBC09 Bridge Recirculation / Flow Diversion — External Evidence Review

**Date:** 2026-08-10  
**Contract:** `cbc.ecmo.bridge-recirculation-flow-diversion.v1`  
**Disposition:** **external evidence packet complete; expert sign-off pending**

## Review question

Does external evidence support CBC09's learner-facing distinction that opening/titrating an arterial-to-venous ECMO bridge can preserve circuit/oxygenator flow while diverting flow away from the patient, and that recirculated post-oxygenator blood can bias venous-line gas/oximetry measurements?

## Evidence summary

### 1. ELSO directly supports the total-flow-versus-patient-flow distinction

The 2022 ELSO adult/pediatric circuit guideline describes an optional bridge connecting the venous side of the circuit to the arterial/post-oxygenator side. It states that bridges are used particularly during neonatal/pediatric VA-ECMO weaning to maintain circuit integrity. In the weaning section, ELSO explicitly notes that opening a bridge can increase blood flow through the oxygenator while maintaining low blood flow to the patient.

- Gajkowski EF, et al. *ELSO Guidelines for Adult and Pediatric Extracorporeal Membrane Oxygenation Circuits.* ASAIO J. 2022. PMID: **35089258**.  
  https://pubmed.ncbi.nlm.nih.gov/35089258/

This is the strongest direct evidence for CBC09's central teaching point: **displayed total/circuit flow cannot automatically be interpreted as patient-directed support when a bridge is open.**

### 2. ECMO circuit literature independently describes the bridge as an arterial-to-venous recirculation path

Lequier et al. describe the bridge as circuit tubing connecting the proximal venous access limb to the proximal arterial infusion limb. The circuit figure places the venous saturation sensor upstream of the pump and the bridge downstream of the oxygenator/heat exchanger, consistent with the physical possibility that opening the bridge returns recently oxygenated/decarboxylated blood toward the venous limb.

- Lequier L, Horton SB, McMullan DM, Bartlett RH. *Extracorporeal membrane oxygenation circuitry.* Pediatr Crit Care Med. 2013;14(5 Suppl 1):S7-S12. PMID: **23735989**.  
  https://pubmed.ncbi.nlm.nih.gov/23735989/

This supports the topology used by CBC09. It does not validate the simulator's exact bridge-flow targets, clamp-position relation, or CDI mixing fraction.

### 3. Recirculation is known to make venous-line oxygen saturation nonrepresentative of true mixed venous saturation

Walker et al. specifically describe recirculation as oxygenated ECMO blood being shunted back into the venous drainage limb and note that this causes venous-line oxygen saturation to cease being a faithful reflection of patient mixed venous saturation.

- Walker JL, et al. *Calculating mixed venous saturation during veno-venous extracorporeal membrane oxygenation.* Perfusion. 2009;24(5):333-339. PMID: **19948749**. DOI: **10.1177/0267659109354790**.  
  https://pubmed.ncbi.nlm.nih.gov/19948749/

This is VV-ECMO recirculation evidence, not a neonatal VA bridge trial. It supports the **measurement-contamination principle** used by CBC09: when post-oxygenator blood is routed back toward the pre-pump/venous measurement site, the sampled saturation can shift upward and cease to represent unmodified patient venous blood.

### 4. The modeled pCO2 shift is a topology-based inference, not a directly validated bridge-specific quantitative claim

The oxygenator adds oxygen and removes carbon dioxide. ELSO's circuit topology places the bridge between post-oxygenator and venous/pre-pump sides. Therefore, if post-oxygenator blood with lower pCO2 is recirculated toward a venous measurement site, a downward bias in measured venous-line pCO2 is physically consistent with mixing.

That relationship is retained as a **mechanistic inference** for education. This evidence review did not identify a bridge-specific neonatal study validating the simulator's exact CDI saturation or pCO2 shift magnitude.

### 5. The bridge target-flow values remain regression stimuli, not bedside targets

ELSO explicitly states that ECMO circuit configuration, flow-control maneuvers, and weaning practices depend on circuit design, manufacturer minimum-flow requirements, and institutional protocol. It does not provide universal bridge-flow prescriptions matching CBC09's 25/50/75/100/150 mL/min probe.

Accordingly, all bridge targets and solver tolerances in CBC09 remain software regression values only.

## Evidence disposition against CBC09

| CBC09 assertion | Evidence disposition |
|---|---|
| Opening/titrating a bridge can maintain circuit/oxygenator flow while reducing patient-directed flow | **Directly supported directionally by ELSO circuit guidance** |
| Total circuit flow is not equivalent to patient support when a bridge is open | **Directly supported as a circuit-accounting/teaching principle** |
| Less patient-directed VA flow should reduce the simulator's VA support contribution to MAP | **Supported as the intended VA-support interpretation; exact MAP magnitude is not externally validated here** |
| Recirculated post-oxygenator blood can raise venous-line saturation | **Supported as a recirculation/measurement-contamination principle**; bridge-specific magnitude not validated |
| Recirculated post-oxygenator blood can lower venous-line pCO2 | **Mechanistically consistent inference** from bridge topology + oxygenator CO2 removal; exact bridge-specific magnitude not validated |
| Bridge flow should track a requested software target under the live patient boundary | **Software/numerical contract**, not an external clinical claim |
| 25/50/75/100/150 mL/min are validated neonatal bridge targets | **Not supported**; regression stimuli only |
| Exact clamp positions or bridge resistance coefficients are clinically/device validated | **Not supported** |

## Required contract interpretation

CBC09 should be read as a **circuit-accounting and signal-interpretation contract**:

> When a bridge routes post-oxygenator blood back toward the venous side, circuit flow can remain substantial while less flow reaches the patient, and venous-line gas/oximetry measurements can be biased by recirculated blood.

It should **not** be read as:

> The simulator's bridge-flow targets, clamp positions, MAP changes, CDI mixing fractions, or flush intervals are validated bedside prescriptions for a specific neonatal ECMO circuit.

## Expert-review questions still open

1. Is the total-flow-versus-patient-flow distinction framed correctly for the intended neonatal/pediatric VA-ECMO teaching workflow?
2. Is using venous CDI saturation/pCO2 contamination as an interpretation cue appropriate for the exact sensor location in the intended circuit build?
3. Should the learner-facing wording distinguish bridge recirculation from VV cannula recirculation more explicitly to prevent conceptual conflation?
4. Are the canonical bridge target-flow probe values acceptable purely as regression points without suggesting bedside targets?
5. What institution/circuit-specific bridge-management, flash/flush, or weaning policy evidence is required before external training claims go beyond the directional contract?

## Claim boundary

This packet does **not** establish:

- a neonatal bridge-flow prescription;
- a validated bridge clamp position or resistance curve;
- a validated bridge flush/flash interval;
- a device-specific CDI mixing fraction;
- an exact MAP decrement for a given bridge flow;
- equivalence between bridge recirculation and VV cannula recirculation;
- expert clinical sign-off or external-training approval.

**Final status:** external evidence packet complete; expert sign-off pending.

# Priority-A Evidence Review Packet 01 — CBC01 Hypovolemia / Preload-Limited ECMO Low Flow

**Packet ID:** `phase5.validation.cbc01.evidence.v1`  
**Contract:** `cbc.lowflow.hypovolemia.v1`  
**Prepared:** 2026-08-10  
**Product position:** simulation / training only  
**Disposition:** **external evidence packet complete; expert sign-off pending**

## 1. Review purpose

This packet asks a narrow question: does external evidence support the *directional learner-facing relationships* already protected by CBC01 strongly enough to take the contract to expert review?

It does **not** ask whether the current regression values are clinical thresholds, whether 15% blood-volume loss is a neonatal hemorrhage definition, whether 2200/3000 RPM are bedside targets, or whether a 2% flow-change limit should be used clinically.

## 2. Evidence hierarchy used

### Source A — ELSO adult/pediatric ECMO circuit guideline

Gajkowski EF, Herrera G, Hatton L, et al. **ELSO Guidelines for Adult and Pediatric Extracorporeal Membrane Oxygenation Circuits.** ASAIO Journal. 2022;68(2):133-152. DOI: `10.1097/MAT.0000000000001630`.

ELSO states that centrifugal-pump performance is related to RPM and depends on preload and afterload. The guideline defines pump-inlet pressure (P1) as the negative pressure generated while pulling blood from the patient toward the pump and discusses excessive drainage-catheter suction/negative venous-line pressure as a recognized circuit concern.

Local provenance check for the public ELSO PDF downloaded on 2026-08-10:

`SHA-256 ab37a61b162bf397c5ef105dd34c4170e61f19de4593f1b31a5cbf5513d6cb31`

### Source B — primary ECLS volume-depletion experiment

Simons AP, Reesink KD, Lancé MD, et al. **Reserve-driven flow control for extracorporeal life support: proof of principle.** Perfusion. 2010;25(1):25-29. DOI: `10.1177/0267659109360284`; PMID: `20118166`.

This animal proof-of-principle study reports that ECLS systems have limited volume-buffering capacity and that an acute reduction in circulatory volume reduced support flow. The published abstract reports a 10-15% acute volume reduction with pump flow falling from 4.1 to 1.9 L/min in that experimental system.

This source supports *directionality and mechanism*. It does **not** validate the neonatal magnitude used by CBC01, because the experimental species, size, circuit, pump, cannulae, pressures, and baseline conditions are not the simulator's neonatal configuration.

### Source C — primary venous-collapse experiment

Simons AP, Reesink KD, Molegraaf GV, et al. **An in vitro and in vivo study of the detection and reversal of venous collapse during extracorporeal life support.** Artificial Organs. 2007;31(2):154-159. DOI: `10.1111/j.1525-1594.2007.00356.x`; PMID: `17298406`.

This experimental work directly addresses venous collapse associated with ECLS drainage. It supports keeping suction/collapse as a drainage-limitation phenomenon rather than assuming RPM commands guarantee forward flow.

## 3. Claim-by-claim disposition

| CBC01 behavior | Evidence disposition | Phase-5 decision |
|---|---|---|
| Reduced available intravascular volume can reduce ECMO support flow | **Supported** by ELSO pump preload-dependence and primary ECLS volume-depletion work | Keep |
| Centrifugal-pump flow depends on RPM *and* filling/preload rather than RPM alone | **Directly supported** by ELSO circuit guidance | Keep |
| Drainage limitation can generate increasingly negative pump-inlet pressure / excessive suction | **Supported** by ELSO P1/suction description and venous-collapse experimental work | Keep |
| Increasing RPM during a preload-limited state may worsen suction/collapse without restoring effective support | **Supported as a directional teaching relationship**; exact RPM pair and 2% cap are not externally validated | Keep directional rule; keep numeric values as regression-only |
| Chatter/collapse need not occur at every hypovolemic state | **Supported by mechanism dependence on circuit/patient conditions**; no universal threshold found | Keep as allowed exception, not required baseline sign |
| Equal isolated volume replacement restores the simulator close to its own baseline | **System/model reversibility assertion**, not a clinical evidence claim | Keep 1% tolerance as regression invariant only |
| MAP decreases in the canonical isolated hypovolemia path | **Conditionally plausible but not upgraded to a universal clinical claim**; vascular tone/native output can alter response | Keep with existing allowed exceptions; expert sign-off required |
| CVP decreases in the canonical isolated hypovolemia path | **Conditionally plausible but not a generic volume-status rule**; measured CVP is affected by thoracic pressure and other factors | Keep only under CBC01 preconditions; expert sign-off required |

## 4. Numeric claims that remain explicitly unvalidated

The evidence review does **not** promote any of the following into clinical thresholds or prescriptions:

- 3.0 kg canonical patient size;
- 2200 RPM canonical baseline;
- 3000 RPM escalation branch;
- 600 mL/min sweep;
- 15% modeled blood-volume-loss stimulus;
- 2% maximum-flow-improvement regression criterion;
- 1% restoration tolerance;
- a specific P1 threshold for chatter, collapse, hemolysis, or intervention;
- a specific fluid bolus/resuscitation dose or product.

The fact that the Simons 2010 experiment used a 10-15% acute volume reduction makes CBC01's 15% stress magnitude *plausible as a test stimulus*, but it is **not a neonatal clinical threshold**.

## 5. Expert-review questions carried forward

CBC01 is ready for expert sign-off on these questions:

1. Is the core teaching statement correct: **more RPM is not equivalent to more effective patient flow when venous drainage/preload is limiting**?
2. Are falling patient-directed flow and increasingly negative drainage pressure appropriate primary learner cues for this isolated preload-loss scenario?
3. Are MAP and CVP directional expectations acceptably bounded by the current preconditions and allowed exceptions?
4. Is it appropriate that chatter is conditional rather than mandatory at the moderate baseline?
5. Is the contract sufficiently explicit that volume replacement is one mechanism-specific response, not a universal answer to every low-flow state?
6. Are the regression numbers clearly separated from bedside thresholds and treatment prescriptions?

## 6. Final disposition

**CBC01 remains automated/passing. External evidence now supports the core directional teaching relationships. Expert sign-off is still required before the contract is labeled expert-reviewed or used to justify stronger clinical claims.**

No CBC01 physiology, thresholds, or test assertions are changed by this packet.

## 7. Future invalidation / retest conditions

Re-review CBC01 if any of the following changes:

- the venous/preload model gains a transmural-pressure interface;
- the drainage cannula model becomes device-specific;
- a persistent bleeding-rate state replaces discrete blood-loss events for this scenario;
- volume interventions gain product-specific composition/transfusion physiology;
- the circuit topology changes in a way that materially changes patient-directed versus recirculating flow;
- institution-specific neonatal ECMO troubleshooting policy is adopted as an explicit training target.

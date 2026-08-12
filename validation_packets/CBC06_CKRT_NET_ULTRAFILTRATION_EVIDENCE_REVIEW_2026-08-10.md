# Priority-A Evidence Review Packet 03 — CBC06 CKRT Net Ultrafiltration / Fluid Removal

**Packet ID:** `phase5.validation.cbc06.evidence.v1`  
**Contract:** `cbc.ecmo.ckrt-net-ultrafiltration.v1`  
**Prepared:** 2026-08-10  
**Product position:** simulation / training only  
**Disposition:** **external evidence packet complete; expert sign-off pending**

## 1. Review purpose

This packet asks whether external evidence supports the directional learner-facing relationships protected by CBC06 strongly enough to take the contract to expert review.

It does **not** validate the current CKRT blood-flow setting, net-ultrafiltration setting, treatment duration, a device-specific prescription range, solute-clearance dose, access-pressure target, or a universal clinical rule that the simulator's exact `CKRT selected + Qb > 0` state gate is how all bedside CKRT systems determine whether prescribed net UF is active.

## 2. Evidence hierarchy used

### Source A — ELSO fluid overload / AKI / electrolyte guideline

Bridges BC, Dhar A, Ramanathan K, Steflik HJ, Schmidt M, Shekar K. **Extracorporeal Life Support Organization Guidelines for Fluid Overload, Acute Kidney Injury, and Electrolyte Management.** ASAIO Journal. 2022;68(5):611-618. PMID: `35348527`; DOI: `10.1097/MAT.0000000000001702`.

ELSO maintains a dedicated guideline for fluid overload, acute kidney injury, and electrolyte management during ECMO. That establishes fluid balance and kidney-support management as legitimate ECMO care domains, but it does not make CBC06's regression settings universal prescriptions.

### Source B — pediatric ECMO + CRRT fluid-removal cohort

Selewski DT, et al. **Fluid overload and fluid removal in pediatric patients on extracorporeal membrane oxygenation requiring continuous renal replacement therapy.** Critical Care Medicine. 2012;40(9):2694-2699. PMID: `22743776`; DOI: `10.1097/CCM.0b013e318258ff01`.

This pediatric ECMO cohort directly studied fluid overload, CRRT fluid removal, and the kinetics of fluid removal. The study supports treating net fluid removal as a clinically meaningful state trajectory during ECMO. It also cautions against turning any particular fluid-overload correction target into a guaranteed outcome rule: correction to a specified threshold was not independently associated with improved survival in that cohort.

### Source C — accuracy of delivered versus prescribed ultrafiltration during ECLS

Symons JM, et al. **Continuous renal replacement therapy with an automated monitor is superior to a free-flow system during extracorporeal life support.** Pediatric Critical Care Medicine. 2013;14(9):e404-e408. PMID: `23965637`; DOI: `10.1097/PCC.0b013e31829f5c09`.

In infants and children on ECLS, integrated CRRT provided substantially more accurate fluid management than free-flow ultrafiltration when prescribed and actual fluid loss were compared. This strongly supports CBC06's insistence that cumulative removal be derived from the active UF setting and elapsed time rather than inferred from a monitor number or silently applied while the therapy is inactive.

### Source D — pediatric CKRT practice / hemodynamic tolerance evidence

Fuhrman DY, Gist KM, Akcan-Arikan A. **Current practices in pediatric continuous kidney replacement therapy: a systematic review-guided multinational modified Delphi consensus study.** Pediatric Nephrology. 2023;38(8):2817-2826. PMID: `36625932`; DOI: `10.1007/s00467-022-05864-z`.

Current pediatric CKRT practice literature emphasizes fluid balance and hemodynamic status when initiating and adjusting net ultrafiltration, and reports reduction of net UF as a common response to hemodynamic instability. This supports CBC06's directional teaching relationship that net fluid removal can reduce effective circulating volume and hemodynamic reserve. It does not validate the simulator's exact MAP/CVP/ECMO-flow magnitude.

### Source E — neonatal/small-child ultrafiltration accuracy boundary

Ricci Z, et al. **Management of fluid balance in continuous renal replacement therapy: technical evaluation in the pediatric setting.** International Journal of Artificial Organs. 2007. PMID: `17992650`.

This work evaluated delivered-versus-prescribed net ultrafiltration in neonates and small children, including use during ECMO. It reinforces that small absolute fluid-balance errors can matter in small patients and that fluid-removal accounting should be explicit rather than approximate.

## 3. Claim-by-claim disposition

| CBC06 behavior | Evidence disposition | Phase-5 decision |
|---|---|---|
| CKRT/CRRT may be used during pediatric ECMO to manage fluid overload / remove fluid | **Strongly supported** | Keep |
| Prescribed net UF should only change patient fluid state when the therapy is actually active | **Strong system-safety principle; exact simulator state gate is implementation-specific** | Keep gate, require expert workflow review |
| Cumulative CKRT removal should equal delivered net UF integrated over active treatment time | **Strongly supported conceptually**, especially by delivered-vs-prescribed UF accuracy literature | Keep |
| Active net UF lowers net body fluid and can reduce effective circulating volume/hemodynamic reserve | **Supported directionally** | Keep directional rule |
| Lower preload can reduce patient-directed ECMO flow and make drainage pressure more negative | **Supported by the simulator's already-reviewed preload mechanism/CBC01**, not by CKRT evidence alone | Keep as composed-model behavior; do not claim CKRT-specific magnitude |
| MAP/CVP may fall during isolated net fluid removal | **Directionally plausible/supported by hemodynamic-tolerance literature**, patient-dependent | Keep isolated canonical direction; no threshold/magnitude claim |
| Setting UF to zero stops further CKRT fluid removal but does not replace already removed volume | **Strongly supported by mechanism separation** | Keep |
| Returning equivalent fluid can restore the modeled volume/preload state | **Model-state reversibility**, not a clinical resuscitation prescription | Keep as regression/reversibility check only |
| Qb itself is currently informational with negligible fixed-shunt hydraulic effect | **Simulator-specific limitation**, not a clinical CKRT claim | Keep disclosed/non-claimed |
| CBC06 validates solute clearance, dose, electrolyte correction or anticoagulation | **Not supported because those mechanisms are absent** | Continue explicit non-claim |

## 4. Contract bookkeeping correction from Phase 2b

CBC06 was authored before Phase 2b. Its original scope text said learner CKRT prescription controls were not yet implemented. That statement became stale when Phase 2b made CKRT Qb and net-UF learner-operable.

The contract documentation and JSON are corrected to reflect the current runtime. This is a **bookkeeping correction only**: no CBC06 acceptance behavior, physiology, tolerance or regression stimulus changes.

## 5. Activation-gate interpretation

CBC06 requires both:

1. the simulator's fixed shunt is configured as `CKRT`; and
2. CKRT blood flow is greater than zero.

This gate is retained because it prevents a stale stored UF value from silently removing patient volume while the simulator has no active CKRT blood path.

External evidence supports the broader principle that delivered ultrafiltration depends on an operating renal-support system and that accurate delivered-versus-prescribed fluid accounting matters. It does **not** establish `configuration == CKRT and Qb > 0` as a universal device-independent bedside rule.

Therefore the exact gate remains an **intended-simulator workflow rule requiring expert review**, not a clinical/device claim.

## 6. Numeric claims that remain explicitly unvalidated

The evidence review does **not** promote any of the following into clinical thresholds or prescriptions:

- 3.0 kg canonical patient size;
- 2200 RPM or 600 mL/min ECMO sweep;
- CKRT blood flow 30 mL/min;
- net UF 0.4 mL/min;
- 20-minute active-UF interval;
- 20-minute replacement interval;
- 0.1% relative / 0.01 absolute counterfactual recovery tolerances;
- any exact change in preload, P1, ECMO flow, MAP or CVP;
- a treatment target for percent fluid overload;
- a universal safe UF rate.

These remain regression stimuli and model tolerances only.

## 7. Expert-review questions carried forward

1. Is the learner workflow gate `CKRT selected + Qb > 0` appropriate for this simulator's intended circuit and operational model?
2. Is it appropriate to teach that active net UF removes patient fluid continuously and that stopping UF prevents further CKRT removal without replacing prior losses?
3. Are the matched-control preload, patient-flow, drainage-pressure, MAP and CVP directions appropriate under the intentionally isolated canonical conditions?
4. Is the separation between **fluid removal** and unmodeled **solute clearance/dialysis dose** clear enough for learners?
5. Should the current learner controls have institution/device-specific bounds before external training use?
6. Are the existing Qb/UF/time values clearly separated from bedside prescriptions?
7. Is the matched-counterfactual fluid-return branch acceptable strictly as a reversibility test rather than a resuscitation recommendation?

## 8. Final disposition

**CBC06 remains automated/passing. External evidence supports CKRT/CRRT as a pediatric ECMO fluid-management strategy, supports explicit delivered-UF accounting, and supports the directional risk that net fluid removal can reduce circulating-volume/hemodynamic reserve. Expert sign-off is still required for the simulator workflow gate and teaching interpretation. Prescription values and device-specific limits remain unvalidated.**

No CBC06 physiology source, acceptance tolerance or regression stimulus is changed by this packet.

## 9. Future invalidation / retest conditions

Re-review CBC06 if:

- a stateful CKRT device running/stopped/alarm model is added;
- solute-clearance/dialysis-dose physiology is added;
- CKRT access pressure or recirculation becomes modeled;
- device-specific Qb/UF operating ranges are adopted;
- the body-fluid-to-intravascular partition model changes;
- replacement-fluid/dialysate composition physiology is added;
- external training adopts an institutional CKRT workflow that differs from the current simulator gate.

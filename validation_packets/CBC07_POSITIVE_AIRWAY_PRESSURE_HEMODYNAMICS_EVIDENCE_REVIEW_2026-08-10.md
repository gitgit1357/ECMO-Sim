# CBC07 Positive-Airway-Pressure Hemodynamics — External Evidence Review

**Date:** 2026-08-10  
**Contract:** `cbc.patient.positive-airway-pressure-hemodynamics.v1`  
**Disposition:** **external evidence packet complete; expert sign-off pending**

## Review question

Does the external literature support CBC07's learner-facing teaching relationship that positive airway pressure can reduce native forward output while measured CVP rises, without implying that the simulator's exact PEEP levels or monotonic MAP/CO response are universal neonatal bedside rules?

## Evidence summary

### 1. Pediatric cardiac-output response to graded PEEP

Ingaramo et al. prospectively studied 50 mechanically ventilated, hemodynamically stable children while PEEP was changed in random order to 0, 4, 8, and 12 cmH2O. Cardiac index decreased statistically as PEEP increased, but the median change from 0 to 12 cmH2O was only about 0.4 L/min/m2 (<10%), and blood pressure did not significantly change. This supports the **possibility/direction** of reduced forward output with higher PEEP while directly warning against treating a monotonic MAP fall or a large hemodynamic effect as universal.

- Ingaramo OA, Ngo T, Khemani RG, Newth CJL. *Impact of positive end-expiratory pressure on cardiac index measured by ultrasound cardiac output monitor.* Pediatr Crit Care Med. 2014;15(1):15-20. PMID: **24389709**. DOI: **10.1097/PCC.0b013e3182976251**.
- PubMed: https://pubmed.ncbi.nlm.nih.gov/24389709/

### 2. Direct neonatal evidence shows a real but heterogeneous response

de Waal et al. studied 50 ventilated newborns before and after PEEP was increased from 5 to 8 cmH2O and again after return to baseline. Right-ventricular output fell significantly by 17 mL/kg/min on average, while the mean change in superior-vena-cava flow was not significant. The authors also reported clinically important flow changes in a substantial minority and found that changes in lung compliance were related to changes in SVC flow. This supports CBC07's caution that the response depends on cardiopulmonary context and recruitment rather than following one universal dose-response.

- de Waal KA, Evans N, Osborn DA, Kluckow M. *Cardiorespiratory effects of changes in end expiratory pressure in ventilated newborns.* Arch Dis Child Fetal Neonatal Ed. 2007;92:F444-F448. PMID: **17460022**. DOI: **10.1136/adc.2006.103929**.
- PubMed: https://pubmed.ncbi.nlm.nih.gov/17460022/

### 3. Measured CVP is pressure-context dependent under PEEP

Clinical studies in mechanically ventilated patients demonstrate that increasing PEEP can increase measured CVP. That observation supports CBC07's **interpretive guardrail**: a higher measured CVP after raising airway/intrathoracic pressure is not equivalent to proof of increased circulating blood volume or effective transmural preload.

- Shojaee M, Sabzghabaei A, Alimohammadi H, Derakhshanfar H, Amini A, Esmailzadeh B. *Effect of Positive End-Expiratory Pressure on Central Venous Pressure in Patients under Mechanical Ventilation.* Emerg (Tehran). 2017;5(1):e1. PMCID: **PMC5325877**.
- Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC5325877/

This source is adult rather than neonatal and is used only for the pressure-measurement mechanism, not for a neonatal quantitative CVP increment.

## Evidence disposition against CBC07

| CBC07 assertion | Evidence disposition |
|---|---|
| Positive airway pressure can reduce native forward output | **Supported directionally** by pediatric and neonatal clinical physiology studies |
| Higher measured CVP does not prove increased blood volume/transmural preload | **Supported as an interpretation principle**; quantitative neonatal CVP response not established here |
| Native CO must fall monotonically at every PEEP step | **Not established as universal**; retained only as the simulator canonical isolated regression path |
| MAP must fall monotonically at every PEEP step | **Not externally established as universal**; stable pediatric data found no significant BP change |
| 0/5/8/12 cmH2O are clinically validated neonatal settings | **Not supported**; regression stimuli only |
| Exact CO/MAP/CVP magnitudes are clinically validated | **Not supported** |
| PEEP-to-ECMO-drainage direction in this simulator is validated | **No — explicitly blocked** until transmural preload exists |

## Required contract interpretation

CBC07 should be read as a **controlled educational path** under explicit simulator preconditions:

> Raising PEEP can reduce native forward output while measured CVP rises, and that rise in measured CVP must not be interpreted as proof that circulating volume or effective transmural preload improved.

It should **not** be read as:

> Every neonate at every PEEP increase will show a clinically important monotonic fall in cardiac output and MAP.

That distinction is now explicit in the CBC07 Markdown/JSON and capability matrix.

## Phase 2d bookkeeping correction

CBC07 originally predated Phase 2d and listed unified ventilator rate/mode/inspiratory-time inputs and learner ventilator controls as absent. Phase 2d subsequently implemented learner-operable pressure-control ventilation (PIP/PEEP/rate/Ti/FiO2). Those stale limitations are removed. This is a documentation/status correction only; CBC07's PEEP stimulus, acceptance assertions, tolerances, and blocked ECMO-transmural-preload boundary are unchanged.

## Expert-review questions still open

1. Is the canonical isolated path (CO/MAP down, measured CVP up) appropriate as a teaching example when explicitly labeled non-universal?
2. Should CBC07 preserve MAP as a required simulator direction, or should future expert review reduce the required contract to forward-output/CVP interpretation only?
3. Are the current PEEP stimuli suitable for regression without suggesting prescription ranges?
4. Is the blocked PEEP-to-ECMO-drainage/transmural-preload boundary stated strongly enough for learner-facing use?

## Claim boundary

This packet does **not** establish:

- a neonatal PEEP prescription;
- a threshold at which PEEP becomes hemodynamically harmful;
- a universal MAP or cardiac-output response;
- device-specific ventilator accuracy;
- a validated PEEP-to-ECMO-drainage relationship;
- clinical validation or expert sign-off.

**Final status:** external evidence packet complete; expert sign-off pending.

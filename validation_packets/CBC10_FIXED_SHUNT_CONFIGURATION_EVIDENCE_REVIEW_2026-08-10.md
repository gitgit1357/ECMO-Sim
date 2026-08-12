# CBC10 Fixed-Shunt Configuration / Hemofilter Hydraulics — External Evidence Review

**Date:** 2026-08-10  
**Contract:** `cbc.ecmo.fixed-shunt-configuration.v1`  
**Disposition:** **external evidence packet complete; expert sign-off pending**

## Review question

Does external evidence support CBC10's learner-facing distinction among an OPEN fixed shunt, an inline HEMOFILTER configuration, and a side-port CKRT configuration, while preserving the boundary that the simulator's exact resistance coefficients and hydraulic equivalence assumptions are reduced-order model choices rather than device-validated claims?

## Evidence summary

### 1. ECMO literature supports in-line hemofilter and CRRT configurations as physically distinct circuit topologies

Reviews of renal support during ECMO describe an **in-line hemofilter** as a configuration in which ECMO blood is deliberately shunted through the filter and then returned to the ECMO circuit. They also describe separate CRRT-machine connection strategies, including series and parallel/side-port approaches.

- Selewski DT, et al. *Continuous renal replacement therapy in patients treated with extracorporeal membrane oxygenation.* Semin Dial. 2021. PMCID: **PMC8250911**.  
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8250911/
- Canter MO, et al. *Adjunctive Therapies During Extracorporeal Membrane Oxygenation to Enhance Multiple Organ Support in Critically Ill Children.* Front Pediatr. 2018.  
  https://www.frontiersin.org/journals/pediatrics/articles/10.3389/fped.2018.00078/full

These sources support CBC10's core **configuration distinction**: placing a filter in the blood path is not the same hydraulic topology as leaving that path unobstructed, and connecting a separate renal-support device through other circuit ports is a different topology again.

### 2. Connection topology can affect ECMO-circuit pressure/resistance behavior

The pediatric ECMO/CRRT literature explicitly discusses hemodynamic consequences of connection location. Canter et al. summarize reports in which series versus parallel connection strategies were selected partly to reduce blood-flow resistance/turbulence, and note experimental work showing that some configurations have little measurable effect on ECMO hemodynamics with a centrifugal pump.

This supports the general principle that **added components and their location can alter circuit resistance/pressure-flow behavior**, and that a side-port/parallel configuration can be designed to minimize disturbance of the primary ECMO path.

It does **not** externally validate CBC10's exact shunt resistance coefficient, exact flow redistribution, or the assertion that every real CKRT side-port arrangement is hydraulically identical to an OPEN shunt.

### 3. CBC10's HEMOFILTER flow redistribution is a hydraulic inference, not a device-performance claim

In CBC10, the inline HEMOFILTER adds resistance to the modeled fixed-shunt branch. At the same pump RPM and patient boundary, that increased branch resistance reduces shunt diversion and redistributes some flow toward the patient branch.

That direction follows ordinary parallel-branch hydraulic reasoning and is consistent with the literature's recognition that adding a hemofilter changes the blood path and resistance environment. This review did not identify a neonatal study validating the simulator's exact change in shunt flow, patient flow, MAP support, or filter resistance.

Therefore, CBC10's **directional hydraulic accounting** is supportable as a reduced-order teaching relationship; its magnitudes remain model-specific regression behavior.

### 4. Filter presence and filtration activity should remain conceptually separate

The literature distinguishes the physical hemofilter/circuit connection from the prescribed fluid-removal process. In-line hemofilter techniques use the filter as a blood-path component, while ultrafiltrate removal is controlled separately and requires its own prescription/accounting.

That supports CBC10's separation between:

- **filter presence** — owns the modeled inline hydraulic resistance; and
- **`scuffing_active` / filtration activity** — does not, by itself, alter the blood-path resistance in the current model.

The evidence does not establish the simulator's specific `scuffing_active` Boolean as a universal device state; it supports only the conceptual separation between circuit hardware and prescribed filtrate removal.

### 5. Keeping hemofilter fluid removal blocked in the coupled patient remains appropriate

The current CBC10 intentionally refuses to promote the lower-level hemofilter-removal helper into patient physiology because no clinically bounded learner prescription is attached to that pathway. ECMO/CRRT reviews emphasize that ultrafiltration must be prescribed and accurately accounted for and that connection/device details vary by center and technology.

Accordingly, keeping hemofilter patient-volume removal **blocked** until there is an explicit, clinically reviewed prescription/coupling path is consistent with the evidence and with the project's claim discipline.

### 6. CKRT = OPEN hydraulic equivalence is a simulator-specific reduced-order assumption

Published ECMO/CRRT literature supports multiple connection topologies and includes configurations intended to minimize interference with ECMO hemodynamics. It does **not** support a universal statement that every side-port CKRT connection has literally zero hydraulic effect.

CBC10's assertion that side-port CKRT is hydraulically equivalent to OPEN should therefore be read as:

> In this simulator's current three-way side-port reduced-order architecture, CKRT does not occupy the inline fixed-shunt resistance path, so the primary shunt hydraulics are intentionally modeled as equivalent to OPEN.

It should **not** be read as a device- or institution-independent clinical claim.

## Evidence disposition against CBC10

| CBC10 assertion | Evidence disposition |
|---|---|
| Inline HEMOFILTER is a physically different circuit topology from an unobstructed/open shunt | **Directly supported** by ECMO renal-support literature |
| Adding an inline filter can alter resistance/pressure-flow behavior | **Supported directionally/mechanistically**; exact magnitude not validated |
| Increased inline shunt resistance can reduce shunt diversion and redistribute flow toward another parallel branch | **Hydraulic inference consistent with topology**; exact patient-flow/MAP change is model-specific |
| Filter presence can be separated from prescribed filtrate removal | **Supported conceptually** |
| `scuffing_active` has no hydraulic effect in this simulator | **Software/model-state contract**, not a universal device claim |
| Side-port CKRT is hydraulically equivalent to OPEN in this simulator | **Reduced-order architecture assumption**; not externally validated as universally true |
| CBC10's filter-resistance coefficient is device validated | **Not supported** |
| Hemofilter patient UF should remain blocked until a bounded prescription/coupling path exists | **Consistent with evidence and claims discipline** |

## Required contract interpretation

CBC10 should be read as a **configuration-level hydraulic accounting contract**:

> Adding an inline hemofilter changes the modeled shunt branch by adding resistance; filtration activity is a separate concept; and the current side-port CKRT arrangement is intentionally modeled as not adding inline shunt resistance.

It should **not** be read as:

> The simulator reproduces the pressure-flow curve, resistance, ultrafiltration behavior, or hydraulic neutrality of a specific commercial hemofilter/CKRT circuit.

## Expert-review questions still open

1. Does OPEN vs inline HEMOFILTER vs side-port CKRT match the intended neonatal/pediatric circuit layout used for training?
2. Is it appropriate for the learner model to teach the hemofilter's **presence** as a hydraulic-resistance change while treating filtration activity separately?
3. Is the current assumption that side-port CKRT has negligible effect on fixed-shunt hydraulics acceptable for the intended training circuit, or should a small device/line resistance eventually be represented?
4. Is leaving hemofilter patient UF blocked appropriate until a learner-settable, clinically bounded prescription exists?
5. What device- or institution-specific pressure-flow/resistance data would be required before making quantitative hemofilter or CKRT hydraulic claims?

## Claim boundary

This packet does **not** establish:

- a device-specific hemofilter resistance or pressure-flow curve;
- a universal increase in patient flow or MAP caused by installing a hemofilter;
- universal hydraulic equivalence of side-port CKRT and an open shunt;
- a hemofilter ultrafiltration prescription;
- TMP-driven filtrate behavior;
- priming-volume, blood-sequestration, hemoconcentration, solute-clearance, electrolyte, anticoagulation, clot-propagation, or device-alarm behavior;
- expert clinical sign-off or external-training approval.

**Final status:** external evidence packet complete; expert sign-off pending.

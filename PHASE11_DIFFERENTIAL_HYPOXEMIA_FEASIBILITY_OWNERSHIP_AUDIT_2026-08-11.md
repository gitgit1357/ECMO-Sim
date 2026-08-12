# Phase 11 — VA Differential Hypoxemia / Regional Oxygenation Feasibility & Ownership Audit
Date: 2026-08-11
Status: **STOP / RESCOPE before physiology implementation**

## Question
Can the current neonatal VA-ECMO simulator add a clinically defensible upper-body/right-radial versus lower-body differential-hypoxemia mechanism now, without inventing an unsupported cannulation topology or creating a second oxygen solver?

## Finding
**No — not as the currently named generic “Harlequin / North-South” mechanism.**

The present Python model has:
- one native arterial gas state;
- one ECMO-return gas state;
- one whole-patient arterial mixing result;
- no arterial return-site/topology state;
- no aortic mixing-zone location;
- no distinct proximal/right-radial versus distal/lower-body arterial compartments.

The project is explicitly neonatal and its established VA configuration is right internal-jugular drainage with right-carotid arterial return. The ELSO Red Book passages located for classic differential hypoxemia describe **peripheral femoral VA ECMO**, where antegrade native LV ejection and retrograde femoral ECMO return meet at a moving aortic mixing point. Reduced right-radial PaO2 is used as a proximal warning signal. That mechanism cannot be transplanted unchanged into a carotid-return neonatal topology.

## Source-supported clinical boundary
ELSO Red Book, 6th ed.:
- Chapter 5 describes differential circulation in femoral-femoral VA ECMO, with lower-body perfusion by highly oxygenated extracorporeal blood and upper-body perfusion by desaturated native cardiac output when lung function is poor.
- The same chapter describes the opposing antegrade native and retrograde femoral-return streams meeting at an aortic mixing point.
- Chapter 28 states differential hypoxemia becomes more pronounced with poor pulmonary gas exchange plus preserved/improving LV ejection and recommends right-arm pulse oximetry/right-radial sampling as a proximal-aortic monitor.
- Chapter 28 describes pulmonary-oxygenation measures and, for sustained/worsening cases, cannula reconfiguration strategies.

These passages support a **topology-dependent regional oxygenation mechanism**. They do not support a universal rule that any VA ECMO patient should develop a “blue head/red feet” split.

## Ownership audit
### Existing owners that should remain authoritative
- Native lung/native arterial gas: `neocoupling` / patient cardiopulmonary solve.
- Native mixed-venous oxygen: Phase 9a `VenousState` boundary, sourced from native coupling.
- ECMO post-oxygenator gas: existing ECMO oxygenator gas-exchange path.
- ECMO patient-directed flow: existing closed-loop circuit/hydraulic solve.
- Whole-patient reduced-order arterial mixing: `neoblood.mix_native_and_ecmo_arterial_blood`.

### Missing authority required before regional mixing can exist
A topology-aware **arterial return / regional perfusion boundary** is absent. At minimum, a future implementation needs to distinguish:
1. return topology/site capable of producing opposing aortic streams;
2. native antegrade ejection magnitude;
3. ECMO return-flow magnitude;
4. native-lung oxygenation of LV ejectate;
5. a reduced-order mixing-zone/regional exposure state.

This should be a derived regional-distribution layer consuming existing authoritative flows/gases, not a new gas solver.

## Why immediate implementation is unsafe
Adding `right_radial_pao2` and `lower_body_pao2` by applying arbitrary fractions to the current global PaO2 would violate the project’s core rule against direct monitor-number patches. Likewise, using the current whole-patient mixing fraction as a proxy for aortic mixing-point location would falsely claim topology the model does not possess.

The simulator could pass software tests while teaching the wrong mechanism.

## Required rescope before implementation
Phase 11 should be split:

### Phase 11a — VA return-topology / regional-perfusion foundation
Introduce an immutable topology descriptor and a derived regional-distribution state. It must explicitly distinguish the project’s neonatal carotid-return configuration from femoral arterial return. No regional gas numbers should be exposed until the topology is capable of supporting them.

### Phase 11b — Differential-hypoxemia behavior contract (CBC12)
Only for a topology where source evidence supports competing antegrade native and retrograde ECMO streams:
- worsening native-lung oxygenation at preserved/improving native ejection lowers proximal/right-radial oxygenation;
- distal oxygenation may remain better supported by ECMO return;
- increasing ECMO dominance can move the mixing region proximally;
- improving native-lung oxygenation improves proximal oxygenation;
- effects must be directional, bounded, reversible, and explicitly non-quantitative.

### Phase 11c — Learner-facing monitoring/scenario activation
Expose regional values only when the selected cannulation topology supports the mechanism. A neonatal carotid-return case must not silently inherit a femoral-VA Harlequin scenario.

## Audit decision
**STOP / RESCOPE.**

Do not add Phase 11 regional oxygenation physiology to the current neonatal carotid-return model yet.

Recommended next authorized work: Phase 11a topology foundation audit/design, followed by a separate implementation authorization if that design can preserve existing ownership and clinical boundaries.

This STOP is a successful result under Fix Map v6’s audit-before-authority rule.

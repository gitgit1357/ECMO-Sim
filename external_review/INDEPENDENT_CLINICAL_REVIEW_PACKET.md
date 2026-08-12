# Phase 5e — Independent Clinical Review Packet

**Prepared:** 2026-08-10  
**Intended reviewer:** facility ECMO educator  
**Purpose:** independent clinical disposition before any external-training or go-live decision.

## Current review state

All 11 Clinical Behavior Contracts (CBC01–CBC11) have received a single-reviewer clinical review by the project author, a practicing ECMO specialist. That review is not independent. This packet is the handoff for the required facility-educator review. No independent disposition is pre-filled or implied.

## Reviewer task

For each CBC, choose exactly one disposition: **ACCEPT**, **ACCEPT WITH LIMITATION**, **REJECT / REWORK**, or **NOT APPLICABLE**. Record any limitation or required correction in writing. The simulator remains blocked from external-training/go-live until every current CBC has an independent disposition and no unresolved REJECT / REWORK item remains.

## Contracts in scope

### 1. cbc.lowflow.hypovolemia.v1 — Priority A
- Learner exposure: direct — generic intravascular volume and ECMO RPM are learner-operable
- Contract: `clinical_behavior_contracts/hypovolemia_preload_low_flow_v1.json`
- Evidence packet: `validation_packets/CBC01_HYPOVOLEMIA_PRELOAD_EVIDENCE_REVIEW_2026-08-10.md`
- Review domains: ECMO bedside practice, pediatric/neonatal hemodynamics
- Questions:
  - Are the preconditions a plausible non-chattering teaching baseline?
  - Are the expected directions for preload, patient flow, MAP, CVP and drainage pressure appropriate?
  - Is RPM escalation correctly framed as non-definitive/worsening drainage under preload limitation?
  - Are allowed exceptions and non-claims sufficient to prevent treating the regression stimulus as a treatment threshold?

### 2. cbc.ecmo.sweep-gas-failure.v1 — Priority A
- Learner exposure: direct — sweep is learner-operable
- Contract: `clinical_behavior_contracts/sweep_gas_failure_v1.json`
- Evidence packet: `validation_packets/CBC02_SWEEP_GAS_FAILURE_EVIDENCE_REVIEW_2026-08-10.md`
- Review domains: ECMO bedside practice, oxygenator gas-path physiology
- Questions:
  - Is complete zero sweep correctly represented as loss of both membrane O2 addition and CO2 removal?
  - Are nonzero sweep and FdO2 roles kept appropriately separate?
  - Is the membrane-boundary validation acceptable while coupled-patient venous-state limitations remain disclosed?

### 3. cbc.ecmo.ckrt-net-ultrafiltration.v1 — Priority A
- Learner exposure: direct — CKRT Qb and net UF are learner-operable
- Contract: `clinical_behavior_contracts/ckrt_net_ultrafiltration_v1.json`
- Evidence packet: `validation_packets/CBC06_CKRT_NET_ULTRAFILTRATION_EVIDENCE_REVIEW_2026-08-10.md`
- Review domains: ECMO bedside practice, CKRT practice, pediatric/neonatal fluid management
- Questions:
  - Is UF gating on CKRT selected + Qb>0 appropriate for the intended simulator workflow?
  - Are matched-control volume/preload consequences appropriate?
  - Is stopping UF correctly distinguished from replacing lost volume?
  - Are the current Qb/net-UF values clearly retained as regression stimuli rather than prescriptions?

### 4. cbc.patient.positive-airway-pressure-hemodynamics.v1 — Priority A
- Learner exposure: direct — pressure-control ventilation including PEEP is learner-operable
- Contract: `clinical_behavior_contracts/positive_airway_pressure_hemodynamics_v1.json`
- Evidence packet: `validation_packets/CBC07_POSITIVE_AIRWAY_PRESSURE_HEMODYNAMICS_EVIDENCE_REVIEW_2026-08-10.md`
- Review domains: neonatal/pediatric respiratory care, hemodynamics, ECMO bedside practice
- Questions:
  - Is higher positive airway pressure correctly taught as capable of lowering native output/MAP while measured CVP rises?
  - Is the non-volume interpretation of CVP clear?
  - Is the PEEP-to-ECMO drainage block adequate until transmural preload exists?
  - Are re-equilibration and recruitment/derecruitment limitations clearly separated?

### 5. cbc.ecmo.fdo2-oxygen-fraction-control.v1 — Priority A
- Learner exposure: direct — FdO2 is learner-operable
- Contract: `clinical_behavior_contracts/fdo2_oxygen_fraction_control_v1.json`
- Evidence packet: `validation_packets/CBC08_FDO2_OXYGEN_FRACTION_EVIDENCE_REVIEW_2026-08-10.md`
- Review domains: ECMO bedside practice, oxygenator gas exchange
- Questions:
  - Is the separation of FdO2-driven O2 effect from sweep-driven CO2 effect appropriate?
  - Is deriving saturation from the same modeled PO2 state acceptable as a consistency rule?
  - Is coupled-patient oxygenation correctly blocked until true venous inlet state exists?

### 6. cbc.ecmo.bridge-recirculation-flow-diversion.v1 — Priority A
- Learner exposure: direct — bridge control is learner-operable
- Contract: `clinical_behavior_contracts/bridge_recirculation_flow_diversion_v1.json`
- Evidence packet: `validation_packets/CBC09_BRIDGE_RECIRCULATION_FLOW_DIVERSION_EVIDENCE_REVIEW_2026-08-10.md`
- Review domains: ECMO circuit bedside practice
- Questions:
  - Is total-flow-versus-patient-flow diversion represented in the right direction?
  - Is venous CDI contamination by recirculated post-oxygenator blood an appropriate teaching relationship?
  - Are bridge target flows clearly regression stimuli rather than bedside targets?

### 7. cbc.ecmo.fixed-shunt-configuration.v1 — Priority A
- Learner exposure: direct — shunt configuration is learner-operable
- Contract: `clinical_behavior_contracts/fixed_shunt_configuration_v1.json`
- Evidence packet: `validation_packets/CBC10_FIXED_SHUNT_CONFIGURATION_EVIDENCE_REVIEW_2026-08-10.md`
- Review domains: ECMO circuit bedside practice, hemofilter/CKRT circuit setup
- Questions:
  - Does OPEN vs inline HEMOFILTER vs side-port CKRT match the intended circuit topology?
  - Is filter presence correctly separated from scuffing activity?
  - Is leaving hemofilter patient UF blocked appropriate until a bounded prescription exists?

### 8. cbc.ecmo.oxygenator-dysfunction.v1 — Priority B
- Learner exposure: indirect/headless — no complete persistent oxygenator-fault action yet
- Contract: `clinical_behavior_contracts/oxygenator_dysfunction_v1.json`
- Evidence packet: No external evidence packet required/completed for current Priority-B scope.
- Review domains: ECMO bedside practice, oxygenator performance
- Questions:
  - Is separating hydraulic obstruction from gas-transfer impairment correct?
  - Are universal Delta-P thresholds appropriately excluded?
  - Are restoration semantics correctly identified as deterministic while no persistent fault state exists?

### 9. cbc.patient.ongoing-major-bleeding.v1 — Priority B
- Learner exposure: indirect/headless — blood-loss mechanism exists but no learner bleeding-source control
- Contract: `clinical_behavior_contracts/ongoing_major_bleeding_v1.json`
- Evidence packet: No external evidence packet required/completed for current Priority-B scope.
- Review domains: ECMO bedside practice, pediatric/neonatal critical care
- Questions:
  - Are serial blood-loss and partial-replacement relationships appropriate?
  - Is cessation correctly represented only as absence of further loss events in the current model?
  - Are coagulation/transfusion/source-control limitations explicit enough?

### 10. cbc.ecmo.drainage-path-resistance.v1 — Priority B
- Learner exposure: indirect/headless — no typed kink/position fault action
- Contract: `clinical_behavior_contracts/drainage_path_resistance_v1.json`
- Evidence packet: No external evidence packet required/completed for current Priority-B scope.
- Review domains: ECMO bedside practice, cannula/circuit hydraulics
- Questions:
  - Is the always-open-shunt interpretation of patient-flow/shunt-fraction changes appropriate?
  - Is omitting a mandatory more-negative P1 response correct for this topology?
  - Are kink, common pre-pump obstruction and positional maldrainage correctly kept separate/blocked?

### 11. cbc.patient.myocardial-dysfunction.v1 — Priority B
- Learner exposure: headless/runtime mechanism — no learner inotrope or myocardial control
- Contract: `clinical_behavior_contracts/myocardial_dysfunction_v1.json`
- Evidence packet: No external evidence packet required/completed for current Priority-B scope.
- Review domains: neonatal/pediatric cardiac physiology, critical care hemodynamics
- Questions:
  - Are LV and RV directional failure phenotypes appropriate?
  - Is the nonlinear response across contractility scales acceptable for teaching?
  - What labels, if any, can be safely attached to scale values?
  - Are filling-pressure/chamber-volume interpretations appropriately bounded?

## Known blocked capabilities — not presented for approval

These are explicit exclusions. Independent review of the current supported simulator must not be interpreted as approval of these absent or blocked mechanisms.

- **VA differential hypoxemia / upper-vs-lower body oxygenation:** BLOCKED — mechanism/state absent. Current Python VA coupling has no distinct right-radial/upper-body versus lower-body oxygenation state or mixing-point mechanism. CBC candidate intentionally blocked rather than approximated with a generic gas target.
- **PEEP-to-ECMO drainage coupling via transmural preload:** BLOCKED — required mechanism absent. Current VA preload path consumes absolute measured CVP and has no separate transmural/intrathoracic-pressure boundary; higher PEEP can therefore increase modeled drainage capacity. CBC07 explicitly does not legitimize that artifact.
- **FdO2-to-coupled-patient oxygenation via true venous inlet state:** BLOCKED — authoritative venous oxygen state absent. Patient-to-ECMO adapter currently uses patient arterial saturation as a temporary venous surrogate. Near-saturated inlet blood can mask FdO2 changes in the coupled patient, so CBC08 intentionally stops at the membrane boundary until a true central-venous oxygen state exists.
- **Hemofilter net-fluid removal to coupled patient:** BLOCKED — clinically bounded prescription/coupling path absent. step_filtrate_removal() can accumulate hemofilter removal, but the console does not expose a hemofilter UF prescription and CoupledVaEcmoPatient does not apply the provisional hemofilter rate to patient volume. Do not promote the default 10 mL/min helper value into patient physiology without a bounded/validated prescription.
- **Phase 2b deferred formulary interventions:** BLOCKED — authoritative mechanisms absent. Vasoactive/inotrope, sedation/analgesia, calcium/electrolytes, and blood-component-specific transfusion are intentionally unavailable until clinically defensible unified-patient mechanisms exist.
- **Phase 2c deferred laboratory analytes/panels:** BLOCKED — authoritative analyte state absent. CBC/chemistry/coagulation/lactate and complete ABG acid-base values are intentionally unavailable until authoritative Hgb/Hct/electrolyte/pH/HCO3/lactate/coagulation state exists. No constants or guessed values are used.
- **Device alarm priority / acknowledge / silence architecture:** BLOCKED — alarm thresholds/priorities/device workflow not validated. Current LOW FLOW/LOW VOLUME/negative-P1/chatter messages remain simulator advisories and are explicitly labeled NOT DEVICE-VALIDATED. Do not add priority, acknowledge, silence, audio, or device-specific thresholds without an alarm contract and evidence.

## Required reviewer output

- Completed `INDEPENDENT_REVIEW_CHECKLIST.json` or equivalent signed/dated review record.
- Disposition for all 11 current CBCs.
- Written limitations for every ACCEPT WITH LIMITATION item.
- Required remediation for every REJECT / REWORK item.
- Explicit statement whether the current build is acceptable for the intended external simulation/training scope.

## Claims boundary

An ACCEPT disposition means the reviewer finds the represented teaching behavior appropriate for the stated simulator scope. It does not establish device equivalence, regulatory clearance, institutional policy approval, patient-specific prediction, treatment authority, or validation of blocked mechanisms or regression-only numeric stimuli.

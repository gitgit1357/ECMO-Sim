# Validation Review Queue — Current Disposition

> **Current review disposition (2026-08-10):** all 11 current CBCs have received a single-reviewer clinical review by the project author, a practicing ECMO specialist. This is not independent external expert attestation, device-specific quantitative validation, institutional policy approval, or regulatory clearance. Independent external review (planned reviewer: facility ECMO educator) remains required before external-training/go-live. Blocked/unimplemented mechanisms remain blocked.

The capability matrix remains the implementation/integration/status authority. This queue records review/evidence disposition only.

## Priority A

### cbc.lowflow.hypovolemia.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** direct — generic intravascular volume and ECMO RPM are learner-operable
- **Evidence packet:** `validation_packets/CBC01_HYPOVOLEMIA_PRELOAD_EVIDENCE_REVIEW_2026-08-10.md`
- **Device/policy evidence boundary:** not required for directional contract; local volume-resuscitation policy must be separate from regression stimuli
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Are the preconditions a plausible non-chattering teaching baseline?
  - Are the expected directions for preload, patient flow, MAP, CVP and drainage pressure appropriate?
  - Is RPM escalation correctly framed as non-definitive/worsening drainage under preload limitation?
  - Are allowed exceptions and non-claims sufficient to prevent treating the regression stimulus as a treatment threshold?

### cbc.ecmo.sweep-gas-failure.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** direct — sweep is learner-operable
- **Evidence packet:** `validation_packets/CBC02_SWEEP_GAS_FAILURE_EVIDENCE_REVIEW_2026-08-10.md`
- **Device/policy evidence boundary:** device/manufacturer gas-path operating evidence desirable before device-specific claims
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Is complete zero sweep correctly represented as loss of both membrane O2 addition and CO2 removal?
  - Are nonzero sweep and FdO2 roles kept appropriately separate?
  - Is the membrane-boundary validation acceptable while coupled-patient venous-state limitations remain disclosed?

### cbc.ecmo.ckrt-net-ultrafiltration.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** direct — CKRT Qb and net UF are learner-operable
- **Evidence packet:** `validation_packets/CBC06_CKRT_NET_ULTRAFILTRATION_EVIDENCE_REVIEW_2026-08-10.md`
- **Device/policy evidence boundary:** validated prescription ranges/institutional CKRT practice required before dose/range claims
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Is UF gating on CKRT selected + Qb>0 appropriate for the intended simulator workflow?
  - Are matched-control volume/preload consequences appropriate?
  - Is stopping UF correctly distinguished from replacing lost volume?
  - Are the current Qb/net-UF values clearly retained as regression stimuli rather than prescriptions?

### cbc.patient.positive-airway-pressure-hemodynamics.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** direct — pressure-control ventilation including PEEP is learner-operable
- **Evidence packet:** `validation_packets/CBC07_POSITIVE_AIRWAY_PRESSURE_HEMODYNAMICS_EVIDENCE_REVIEW_2026-08-10.md`
- **Device/policy evidence boundary:** device-specific ventilator accuracy not required for directional contract; local ventilation policy separate
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Is higher positive airway pressure correctly taught as capable of lowering native output/MAP while measured CVP rises?
  - Is the non-volume interpretation of CVP clear?
  - Is the PEEP-to-ECMO drainage block adequate until transmural preload exists?
  - Are re-equilibration and recruitment/derecruitment limitations clearly separated?

### cbc.ecmo.fdo2-oxygen-fraction-control.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** direct — FdO2 is learner-operable
- **Evidence packet:** `validation_packets/CBC08_FDO2_OXYGEN_FRACTION_EVIDENCE_REVIEW_2026-08-10.md`
- **Device/policy evidence boundary:** device-specific transfer data required before quantitative transfer claims
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Is the separation of FdO2-driven O2 effect from sweep-driven CO2 effect appropriate?
  - Is deriving saturation from the same modeled PO2 state acceptable as a consistency rule?
  - Is the Phase 10b directional coupled-patient oxygenation response appropriate when the membrane inlet is the authoritative native mixed-venous oxygen state, while quantitative magnitude remains non-validated?

### cbc.ecmo.bridge-recirculation-flow-diversion.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** direct — bridge control is learner-operable
- **Evidence packet:** `validation_packets/CBC09_BRIDGE_RECIRCULATION_FLOW_DIVERSION_EVIDENCE_REVIEW_2026-08-10.md`
- **Device/policy evidence boundary:** institution/circuit-specific bridge management and sensor-location policy required before target-flow, flush/flash, or device-specific CDI claims
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Is total-flow-versus-patient-flow diversion represented in the right direction?
  - Is venous CDI contamination by recirculated post-oxygenator blood an appropriate teaching relationship?
  - Are bridge target flows clearly regression stimuli rather than bedside targets?

### cbc.ecmo.fixed-shunt-configuration.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** direct — shunt configuration is learner-operable
- **Evidence packet:** `validation_packets/CBC10_FIXED_SHUNT_CONFIGURATION_EVIDENCE_REVIEW_2026-08-10.md`
- **Device/policy evidence boundary:** device-specific filter resistance and institutional setup evidence needed before quantitative/device claims
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Does OPEN vs inline HEMOFILTER vs side-port CKRT match the intended circuit topology?
  - Is filter presence correctly separated from scuffing activity?
  - Is leaving hemofilter patient UF blocked appropriate until a bounded prescription exists?

## Priority B

### cbc.ecmo.oxygenator-dysfunction.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** indirect/headless — no complete persistent oxygenator-fault action yet
- **Evidence packet:** not completed / not required for the current temporary expert-validation workflow assumption
- **Device/policy evidence boundary:** device-specific pressure/transfer curves required before thresholds or change criteria
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Is separating hydraulic obstruction from gas-transfer impairment correct?
  - Are universal Delta-P thresholds appropriately excluded?
  - Are restoration semantics correctly identified as deterministic while no persistent fault state exists?

### cbc.patient.ongoing-major-bleeding.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** indirect/headless — blood-loss mechanism exists but no learner bleeding-source control
- **Evidence packet:** not completed / not required for the current temporary expert-validation workflow assumption
- **Device/policy evidence boundary:** institutional transfusion/coagulation policies required before treatment claims
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Are serial blood-loss and partial-replacement relationships appropriate?
  - Is cessation correctly represented only as absence of further loss events in the current model?
  - Are coagulation/transfusion/source-control limitations explicit enough?

### cbc.ecmo.drainage-path-resistance.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** indirect/headless — no typed kink/position fault action
- **Evidence packet:** not completed / not required for the current temporary expert-validation workflow assumption
- **Device/policy evidence boundary:** device-specific cannula curves required before quantitative claims
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Is the always-open-shunt interpretation of patient-flow/shunt-fraction changes appropriate?
  - Is omitting a mandatory more-negative P1 response correct for this topology?
  - Are kink, common pre-pump obstruction and positional maldrainage correctly kept separate/blocked?

### cbc.patient.myocardial-dysfunction.v1
- **Status:** single-reviewer clinical review complete (practicing ECMO specialist, project author); independent external review pending
- **Learner exposure:** headless/runtime mechanism — no learner inotrope or myocardial control
- **Evidence packet:** not completed / not required for the current temporary expert-validation workflow assumption
- **Device/policy evidence boundary:** not device-specific; clinical phenotype/severity mapping requires expert review
- **External-training gate:** single-reviewer clinical review complete; independent external review by facility ECMO educator required before external-training/go-live; device/institution/regulatory-specific claims remain separately gated
- **Review questions retained for future independent review:**
  - Are LV and RV directional failure phenotypes appropriate?
  - Is the nonlinear response across contractility scales acceptable for teaching?
  - What labels, if any, can be safely attached to scale values?
  - Are filling-pressure/chamber-volume interpretations appropriately bounded?


# Phase 2c Labs & Diagnostics Contract
Date: 2026-08-10
Status: implemented / automated verification pending final package checks

## Purpose
Phase 2c adds a learner-orderable diagnostic workflow without turning laboratory data into continuously updating monitor channels.

## System behavior
1. A diagnostic result is frozen at sample/collection time.
2. `sample_time_s` and `available_time_s` are separate simulation-time fields.
3. Pending results do not expose their values in the learner GUI.
4. Result availability emits one `diagnostic.result_available` event; ordering emits a separate `diagnostic.ordered` event.
5. Result identifiers are deterministic sequential IDs; no uncontrolled randomness is used.
6. Patient-state collection is rejected while native physiology is updating so stale last-known physiology is not silently labeled current.
7. The current 30-second GUI turnaround is an orchestration placeholder only. It is not a clinical, institutional, or device turnaround claim.

## Phase 2c panels
### Patient arterial gas — partial
Authoritative values currently available:
- PaO2
- PaCO2
- SaO2

Explicitly unavailable:
- pH
- HCO3-
- base excess
- lactate

The UI names this panel as partial so it cannot be mistaken for a complete ABG.

### Post-oxygenator gas assessment
Authoritative current ECMO-model values:
- post-oxygenator PO2
- post-oxygenator PCO2
- post-oxygenator O2 saturation

These are model outputs. Device-specific transfer validation remains separate.

## Not modeled / intentionally deferred
- CBC / hemoglobin / hematocrit laboratory workflow
- chemistry/electrolytes
- coagulation studies
- lactate
- acid-base analytes not already owned by the unified patient
- institution-specific turnaround times
- physical sample draw volume/site complications

The existing sampling-loss mechanism is not automatically invoked because the current diagnostic order does not yet own a defined physical draw volume.

## Future retest conditions
Revalidate this contract when any of the following are added:
- stateful lab analytes (Hgb/Hct, electrolytes, pH/HCO3, lactate, coagulation)
- sample-volume definitions that should invoke `record_sampling_loss()`
- institution-specific turnaround policy
- specimen rejection/hemolysis/collection-quality state
- site-specific sampling contamination or line-draw behavior

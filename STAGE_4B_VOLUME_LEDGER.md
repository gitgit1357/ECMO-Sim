# Stage 4B — Reduced-order patient volume ledger

This stage adds only the volume behaviors needed for credible ECMO drainage and scenario response.

## Baseline
- Estimated pre-cannulation blood volume is weight based.
- Default: 86 mL/kg, preserving the existing 3.5 kg / 301 mL baseline.
- The value can be overridden by scenario or patient configuration.

## Tracked states
- Current intravascular blood volume
- Effective venous volume available to ECMO drainage
- Cumulative fluid input
- Urine output
- CKRT/external fluid removal
- Blood loss
- Sampling loss
- Third-space burden

## Scenario hooks
- `add_intravascular_input(volume_ml, intravascular_fraction=...)`
- `record_blood_loss(volume_ml)`
- `record_sampling_loss(volume_ml)`
- `move_to_third_space(volume_ml)`
- `return_from_third_space(volume_ml)`

## Modeling boundary
This is not a full fluid-compartment physiology engine. Third spacing is a scenario-sensitive modifier of effective venous availability. The coupling layer uses effective venous volume—not total fluid balance—to determine drainage capacity and chatter risk.

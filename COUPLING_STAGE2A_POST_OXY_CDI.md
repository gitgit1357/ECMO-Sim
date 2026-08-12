# Coupling Stage 2A — Post-Oxygenator Blood State and CDI

This stage adds an explicit circuit-owned blood state immediately after the oxygenator and before mixing with native patient blood.

## True post-oxygenator state
- PO2
- PCO2
- oxygen saturation
- hematocrit
- hemoglobin
- temperature

## Post-oxygenator CDI
The CDI is a sensor view of the true state, not the source of truth. The sensor API supports later addition of lag, offset, frozen readings, and invalid readings.

## Ownership boundary
- Venous CDI: patient venous blood at the drainage-limb sensor location, including bridge recirculation when present.
- Post-oxy CDI: oxygenator outlet blood before patient/native-flow mixing.
- Patient arterial blood gas: remains patient/coupling-owned and will be calculated after native and ECMO flows mix in a later stage.

## Important modeling note
Post-oxygenator PO2 is not inferred only from near-100% saturation because saturation does not uniquely determine PO2 in the hyperoxic range. The current reduced-order PO2 model uses FdO2, blood flow, and membrane transfer efficiency. Its room-air and pure-O2 targets are provisional and isolated for later device-specific validation.

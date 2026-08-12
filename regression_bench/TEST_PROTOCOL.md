# Preserved Modular-Patient Regression Protocol

Run this protocol before and after attaching every new patient system.

## Rule 1 — Never modify the old test to make a new system pass
The v1 matrix is frozen. A new lung, kidney, brain, endocrine, or other module must be tested against the same baseline patient and the same challenges.

## Rule 2 — Three possible outcomes
1. **Pass:** results remain inside the accepted envelope.
2. **Expected interaction:** the new system legitimately changes a metric. Document the mechanism, preserve the old snapshot, and create a new reference version only after review.
3. **Regression:** the new system changes unrelated physiology or breaks conservation/stability. Fix the integration; do not widen tolerances to hide it.

## Rule 3 — Preserve causal attribution
Each added system must be switchable off. With it off, the engine must reproduce the prior accepted NorthStar snapshot. This is the primary test for hidden cross-system conflicts.

## Required run sequence after each system addition
1. New system OFF -> compare against prior accepted snapshot.
2. New system ON at neutral/normal settings -> run same NorthStar matrix.
3. Run system-specific perturbations separately.
4. Save results with the new module version and manifest hash.
5. Accept a new snapshot only when the changed physiology is intentional and documented.

## Frozen v1 scenarios
- Stable normal-neonate baseline.
- Closed-loop RA-to-aortic VA flow: 0, 50, 100, 150, 200 mL/kg/min.
- External cannula fixture overlay: 9, 11, 13, 15 Fr.
- External synthetic centrifugal fixture: 2000, 3000, 4000, 5000 RPM.

The cannula/pump fixtures are test equipment and do not belong to patient physiology.

## Cross-system equipment gate — Combined Equipment NorthStar v1
After every new patient-system integration, rerun the frozen simultaneous ventilator + VA support bench **without changing its scenario definitions or tolerances**.

Required sequence:
1. Run the new system disabled/neutral and compare with the accepted combined snapshot.
2. Run the new system enabled in its normal state and document any intentional cross-system differences.
3. Do not overwrite the accepted snapshot or widen tolerances to make a new module pass.
4. Any intentional reference change requires a new NorthStar version and written rationale.

This gate exists to preserve causal attribution across modular integrations.

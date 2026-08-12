# Phase 4b — Oxygenator Proxy and Cannula Resistance Fidelity Disposition

**Date:** 2026-08-10  
**Roadmap:** FIX_MAP v4 Phase 4 — physiology fidelity gaps, behavior-first  
**Status:** CLOSED — no additional model complexity earned

## Why this block exists

FIX_MAP v4 explicitly says the oxygenator proxy and cannula resistance may require nothing beyond disclosure if their Behavior Contracts pass. Phase 4b therefore does not begin with a planned physiology rewrite. It asks whether CBC03 and CBC05A currently fail in a way that requires more model detail.

## Oxygenator disposition

CBC03 intentionally separates two behaviors the current reduced-order model can represent:

1. blood-path obstruction / increased hydraulic burden; and
2. impaired membrane gas-transfer capacity.

The focused Phase 4b rerun confirms those branches still pass. The simulator therefore does not earn a deeper oxygenator clot model, a universal Delta-P cutoff, or a forced one-to-one link between pressure rise and gas-transfer failure.

**Disposition:** retain the current reduced-order oxygenator model for the supported learner behaviors. Keep device-specific pressure-flow curves, transfer magnitudes, clot burden, lifetime, and replacement thresholds explicitly unvalidated/disclosed.

## Cannula/drainage-path disposition

CBC05A protects the behavior the current model genuinely owns: increased resistance in the patient drainage path reduces patient-directed and total ECMO flow and increases shunt diversion / patient-path pressure requirement. Its always-open-shunt topology intentionally does not require a more-negative P1.

The focused Phase 4b rerun confirms CBC05A and the underlying cannula tests still pass.

Two adjacent mechanisms remain absent and are not approximated with the available knobs:

- **common pre-pump obstruction:** blocked because the current pre-pump resistance does not participate in the branched operating-point solve in the required way;
- **position-sensitive maldrainage:** blocked because no body/cannula-position state exists.

**Disposition:** retain the current reduced-order drainage-cannula resistance model for CBC05A. Do not add device-specific curves or surrogate kink/position equations without a demonstrated Behavior Contract failure and an actual mechanism design.

## Verification

Focused zero-exit Phase 4b rerun:

- CBC03 oxygenator dysfunction
- CBC05A drainage-path resistance
- oxygenator hydraulics
- cannula hydraulics

Result: **30 passed, 0 failed**.

No `src/` or `tests/` files were modified in Phase 4b.

## Exit decision

Phase 4b is closed. The roadmap's behavior-first gate did its job: both simplified subsystems are adequate for the learner behaviors currently claimed, and their unsupported/device-specific limits remain explicit instead of being hidden behind added mathematical detail.

## Next primary-track work

Proceed to the Phase 4 **CKRT scope review**. Existing Qb/net-UF behavior is real and CBC06-protected; deeper solute/device/prescription physiology should be added only where a Behavior Contract or learner-loop requirement demonstrates the need.

# Phase 5d CBC08 Evidence Review Completion — 2026-08-10

**Status:** complete — external evidence packet prepared; expert sign-off pending.

## Deliverable

`validation_packets/CBC08_FDO2_OXYGEN_FRACTION_EVIDENCE_REVIEW_2026-08-10.md`

## Evidence disposition

External evidence supports CBC08's core learner-facing control separation: oxygen fraction delivered to the membrane lung is an oxygenation control; sweep-gas flow remains the dominant CO2-removal control; and an FdO2-only change is not a blood-side pump/resistance command. Adult VA-ECMO randomized evidence directly supports the direction that lower oxygenator gas-blender oxygen fraction lowers post-oxygenator oxygenation while ECMO blood flow remains similar.

The packet does **not** validate the simulator's exact FdO2 probe values, reduced-order pO2 curve, Hill-equation constants, device-specific transfer performance, or coupled-patient response. The central-venous-state block remains unchanged.

## Contract scope

No CBC08 stimulus, tolerance, or acceptance assertion was changed. The contract JSON gains an evidence-scope section only.

## Source scope

Phase 5d CBC08 is evidence/documentation/test work only. No `src/` file is intentionally changed.

## Roadmap

FIX_MAP v4 remains untouched. Phase 5d continues with the remaining Priority-A evidence packets.

## Verification

- CBC08 evidence packet + unchanged CBC08 behavior contract: **10/10 passed**.
- Phase-5d CBC01/CBC02/CBC06/CBC07/CBC08 evidence consistency: **29/29 passed**.
- CBC08 adjacent gas/console/CDI/oxygenator regression surface: **78/78 passed**.
- Exact repository collection after adding CBC08 evidence tests: **462 tests**.
- Capability matrix: **88 rows**, CSV/JSON mirrors identical.
- Embedded Phase-1b backing data remains **79 actions / 36 complications / 28 scenario IDs**.
- Validation queue remains **11 CBCs**.
- `src/` diff versus v0.20.4: **none** across non-generated source files.


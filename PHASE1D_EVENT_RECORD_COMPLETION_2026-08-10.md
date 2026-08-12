# Phase 1d Completion — Structured Event Record Contract
**Date:** 2026-08-10

## Decision
Phase 1d is implemented as a deliberately small infrastructure layer: immutable event records + append-only event stream + current ECMO workspace integration. It does not start the scenario engine.

## Implementation
Added `src/neoevents/` containing `EventRecord` and `EventStream`.

The record contract is JSON-portable and validates payloads before append. `EcmoWorkspaceModel` now owns the stream and emits structured events for real control changes while retaining the existing human-readable event strip.

## Phase 1b ledger consolidation
`CAPABILITY_MATRIX` remains the sole maintained capability-status source of truth. The three Phase 1b CSV ledgers were embedded into `CAPABILITY_MATRIX.json.backing_data` and moved unchanged into `archive/phase1b_ledgers/` as historical provenance. They are no longer parallel living documents.

## Scope boundary
No scenario triggers, scenario state machine, scoring, debrief runtime, or Scenario Log GUI was implemented. No physiology/circuit equations changed.

## Verification
Exact-tree collection with `PYTHONPATH=.:src`: **312 tests collected**.

Fresh Phase 1d/regression batches:
- event/workspace/async/cache: **20/20 passed**
- dynamic coupling/time-step/coupling contract: **15/15 passed**
- hydraulic/gas/MAP/preload coupling: **22/22 passed**
- ECMO console/component regression subset: **123/123 passed**

Total fresh assertions in these non-overlapping reported batches: **180 passed, 0 failed**. A first broad combined command timed out after progressing through many tests; the same relevant scope was then split into bounded batches above.

No physiology or circuit equations changed.

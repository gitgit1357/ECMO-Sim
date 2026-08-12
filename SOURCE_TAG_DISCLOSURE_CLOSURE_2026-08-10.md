# Source-Tag Disclosure Closure — 2026-08-10

## Decision

The learner-facing event projection must not expose the internal software actor tag `scenario-engine`.

`learner_event_view()` now normalizes:

- `scenario-engine` -> `system`

The authoritative `EventRecord` stored in the shared event stream is **not modified**. Instructor/debrief projections continue to preserve the original `source="scenario-engine"` value for provenance and debugging.

This is a presentation/disclosure rule, not a change to the Phase 1d durable event schema.

## Rationale

`scenario-engine` describes implementation provenance rather than information available to an ECMO learner at the bedside. Leaving it visible could disclose that an observation or change originated from hidden scenario orchestration even when diagnosis-bearing IDs and metadata had already been removed.

The generic `system` source preserves the useful distinction between learner-originated and simulator-originated information without leaking internal architecture.

## Verification

Fresh focused regression:

```text
PYTHONPATH=.:src pytest -q \
  tests/test_tier_a_orchestration.py \
  tests/test_tier_a_vertical_slice.py \
  tests/test_ready_scenario_catalog.py \
  tests/test_scenario_primitives.py \
  tests/test_event_stream.py
```

Result: **40 passed, 0 failed**.

New assertions verify both sides of the disclosure contract:

1. learner projection never exposes `source="scenario-engine"`;
2. instructor/debrief projection retains `source="scenario-engine"` unchanged.

## Status

The first `lowflow-hypovolemia` scenario family's disclosure boundary is now CLOSED for the currently identified diagnosis/source-tag leaks.

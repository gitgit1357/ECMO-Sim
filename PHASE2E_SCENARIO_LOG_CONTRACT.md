# Phase 2e — Scenario Log Contract

**Status:** implemented / automated passing / learner-facing read-only renderer

## Purpose
Render the canonical Phase 1d structured event stream as a learner-facing simulation timeline without creating a second log source or bypassing Tier-A disclosure rules.

## Contract
1. `EventStream` remains the authoritative append-only record. Scenario Log never mutates it.
2. Learner rendering MUST pass through `neoscenarios.disclosure.learner_event_view()`.
3. Diagnosis-bearing/internal scenario-engine events hidden by Tier-A disclosure MUST NOT appear in the learner table.
4. Internal `scenario-engine` provenance is normalized according to the existing learner disclosure policy; instructor/debrief records remain unchanged.
5. Display order follows canonical append order. Simulation time is read from event metadata and is not reconstructed from wall-clock timestamps.
6. The learner table may show event type, learner-safe source, target, action, and sanitized old/new detail.
7. Scenario Log owns no physiology, trigger progression, scoring, debrief analysis, or scenario state.
8. The UI may report that internal events were withheld, but it must not expose their contents or diagnosis-bearing identity.

## Explicit non-claims
- no scoring UI
- no instructor/debrief timeline UI
- no replay engine
- no persistent disk/network event store
- no event editing/deletion
- no diagnosis reveal
- no new scenario physiology

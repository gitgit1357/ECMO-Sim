# Tier-A Orchestration and Disclosure Contract

## Scope
This layer ports architecture-defining behavior from the retired legacy JS runtime without porting legacy physiology or numeric state patches.

## Locked contracts
- Scenario definitions contain data, not executable physiology.
- Every simulator mutation crosses `MechanismRegistry`.
- Trigger eligibility is distinct from event release.
- Once-only trigger state survives snapshot/restore and cannot re-fire after restore.
- Director concurrency, priority, and spacing are orchestration policy, not clinical truth.
- Time-based event-state transitions use time since entry into the current state.
- Learner disclosure must not reveal hidden fault identity, internal state, rationale, scores, educator setup, or trigger policy.
- Instructor/debrief data retains the full structured event record.
- Ordered observations freeze the value at sample time; availability time is separate.
- Scenario randomness is seeded and snapshot/restorable.

## Generic trigger policies now available
`at_start`, `elapsed_time`, `time_window`, `event`, `action_count`, `context`, `manual`, `all`, `any`, plus `time_in_state` for event-state machines.

## Vertical slice
`tier-a-hypovolemia-slice` is intentionally a headless plumbing proof, not a production scenario. It activates authoritative blood loss at start, accepts a learner volume bolus through the real patient volume ledger, resolves from the resulting structured event, and exposes a sanitized learner event view without leaking the hidden fault ID.

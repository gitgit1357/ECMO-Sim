# Phase 5b — Functional UX Architecture Review
**Date:** 2026-08-10
**Roadmap:** FIX_MAP v4 Phase 5
**Status:** CLOSED — functional UX guardrails implemented; device-alarm system remains explicitly incomplete

## Scope
Phase 5b reviews **functional** learner UX: alarms/advisories, control placement/action safety, feedback visibility, and latency. Cosmetic polish is intentionally out of scope.

## 1. Alarm/advisory disposition
The current runtime already produces simulator advisories such as:

- LOW EFFECTIVE VENOUS VOLUME
- DRAINAGE CHATTER
- LOW PATIENT-DIRECTED ECMO FLOW
- EXCESSIVE NEGATIVE DRAINAGE PRESSURE

These are derived from simulator behavior settings. They are **not** promoted to validated device alarms in Phase 5b.

The learner UI now labels them explicitly:

`SIMULATOR ADVISORIES • NOT DEVICE-VALIDATED`

Phase 5b does not invent:

- alarm priority classes;
- clinical/device-specific alarm thresholds;
- acknowledge/silence/reset behavior;
- audio alarm behavior;
- alarm escalation/latching beyond already-modeled chatter display behavior;
- bubble-detector alarms or pump interlock (the underlying mechanism remains absent).

Those require an explicit alarm contract plus device/workflow evidence before they can be represented as validated learner alarms.

## 2. Control placement and shortcut safety
The primary learner controls remain separated by domain:

- ECMO console: pump/RPM/sweep/FdO2/bridge/shunt;
- Ventilator: pressure-control settings;
- Interventions: generic volume and CKRT Qb/net UF;
- Labs: ordered diagnostics;
- Monitor and Scenario Log: read-only.

Global keyboard shortcuts had one functional risk: Space/Up/Down could previously mutate pump/RPM regardless of which tab the learner was using.

Phase 5b now gates those shortcuts so they are active **only on the ECMO page** and are suppressed while focus is inside an editing widget (entry/combobox/spinbox/text). This prevents a learner typing in another page from accidentally toggling the pump or changing RPM.

## 3. Latency visibility
The existing async native-physiology contract intentionally pauses learner simulation time while a native equilibrium recompute is pending, while allowing the GUI/circuit to remain responsive.

Phase 5b adds a global header status:

`PHYSIOLOGY UPDATING • SIM TIME PAUSED`

This is visible regardless of the currently selected tab. It complements the Patient Monitor `UPDATING` state and the existing rule that point-in-time patient diagnostics cannot be collected from a stale native state.

No new latency target is claimed. P0/P0b performance contracts remain authoritative.

## 4. Learner feedback/visibility
The existing architecture remains intentional:

- immediate local action status on Interventions/Labs/Ventilator;
- bottom event strip for recent human-readable console action feedback;
- canonical structured EventStream for audit/replay;
- Scenario Log as learner-safe event history;
- hidden scenario state and internal mechanism provenance remain excluded from the learner projection.

No second event or alarm log is created by Phase 5b.

## Verification
Focused Phase 5b + Phase 2 workspace regression: 39/39 passing before final bounded regression.
Live Tk/Xvfb smoke confirms:

- pump shortcut is inert on Labs;
- pump shortcut acts on the ECMO page;
- a real pressure-control change that triggers async native recompute displays the global `SIM TIME PAUSED` status.

## Remaining functional UX debt
- validated device alarm architecture (priority/threshold/ack/silence/audio/history semantics);
- bubble detector/interlock after the backend mechanism exists;
- expert review of control placement against the intended bedside training workflow;
- real-target hardware latency/usability validation;
- accessibility/keyboard navigation review;
- cosmetic polish remains separate and later.

## Next roadmap work
Continue Phase 5 with broader validation readiness: convert the current matrix/CBC evidence into an expert-review queue and validation plan without treating software regression as clinical validation.

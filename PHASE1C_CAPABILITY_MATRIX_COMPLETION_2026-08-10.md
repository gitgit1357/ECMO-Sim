# Phase 1c — Capability Matrix Completion Note

**Date:** 2026-08-10

## Scope
Build the living capability matrix against the actual Python runtime after the Phase 1b JS-runtime decision. No Phase 1d event stream, Phase 1e scenario engine, physiology extension, or GUI feature implementation was permitted.

## Deliverables
- `CAPABILITY_MATRIX.md` — human-readable authoritative status index.
- `CAPABILITY_MATRIX.csv` — complete evidence/notes ledger for filtering and future automation.
- `CAPABILITY_MATRIX.json` — machine-readable mirror for future tooling.

## Direct runtime findings
- Exact-tree test collection: **305 tests** when `PYTHONPATH` is pinned to this project.
- GUI page inspection: **ECMO Console functional; 5 reserved shells** (`Patient Monitor`, `Ventilator`, `Labs & Diagnostics`, `Interventions`, `Scenario Log`).
- No `src/neoscenarios/` package exists.
- No Python VV patient-support coupling path exists.
- No Python bubble-detector/interlock engine exists; the GUI explicitly labels it not yet modeled.
- Ventilator rate/mode/Ti remain fixture-only; `AirwayPort` exposes PEEP, airway opening pressure, and FiO2.
- Myocardial failure remains explicitly not validated per `README.md`.

## Integrity
This phase is documentation/audit only. `src/` and `tests/` are not modified.

## Exit criteria
- [x] Matrix exists and is grounded in runtime/test evidence.
- [x] Matrix includes Implemented, Integrated, GUI-exposed, Test coverage, Clinical/behavior validation, and Learner-operable distinctions.
- [x] Unsupported features are explicitly `N`/partial rather than inferred from legacy JS.
- [x] Machine-readable CSV/JSON mirrors created.
- [x] No Phase 1d/1e implementation started.

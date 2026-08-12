# Phase 5c — Validation Readiness Completion
**Date:** 2026-08-10
**Status:** CLOSED — review queue established; expert reviews themselves remain pending

## Completed
- Added `VALIDATION_REVIEW_QUEUE.json` and `VALIDATION_REVIEW_QUEUE.md`.
- Derived the queue from all 11 current CBC JSON contracts.
- Separated review priority by learner exposure:
  - **Priority A (7):** learner-operable mechanisms already exposed in the GUI/workspace.
  - **Priority B (4):** headless/indirect physiology or incomplete production fault surfaces.
- Each contract now has named review domains, explicit review questions, evidence boundaries, and an external-training gate.
- Added tests that require one-to-one coverage of the current CBC set and preserve `CAPABILITY_MATRIX.json` as the sole status authority.

## Priority A
1. hypovolemia / preload low-flow
2. sweep-gas failure
3. CKRT net ultrafiltration
4. positive-airway-pressure hemodynamics
5. FdO2 oxygen-fraction control
6. bridge recirculation / flow diversion
7. fixed-shunt configuration

## Priority B
1. oxygenator dysfunction
2. ongoing major bleeding
3. drainage-path resistance
4. myocardial dysfunction

## What Phase 5c does not claim
The queue does not mark any CBC expert-reviewed. It does not create clinical validation from test counts, and it does not establish device equivalence, institutional-policy equivalence, regulatory status, prescription targets, or legal/IP freedom to operate.

## Next Phase 5 decision
Begin Priority-A expert review/evidence packets, while separately deciding when to initiate formal commercial/IP/legal review. Any current-information legal/regulatory work must be handled as a distinct evidence-based review rather than inferred from simulator architecture.

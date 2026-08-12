# Phase 5e — External Training / Go-Live Gate

**Current state:** BLOCKED — independent facility-educator review pending.

## Gate opens only when

1. All 11 current CBCs have an independent disposition from the facility ECMO educator or another explicitly designated independent clinical reviewer.
2. No CBC remains in unresolved `REJECT_REWORK`.
3. Every `ACCEPT_WITH_LIMITATION` limitation is carried into the training scope, learner/instructor disclosure, or remediation backlog as appropriate.
4. Known blocked mechanisms remain excluded from learner claims and scenarios unless separately implemented and validated.
5. The build under review is identified by version/hash so a later source change cannot inherit approval automatically.

## Gate does not establish

- regulatory clearance or certification;
- legal/IP clearance;
- device equivalence;
- institutional policy approval;
- patient-specific predictive validity;
- treatment recommendation authority.

## Re-review triggers

Independent review must be reconsidered when a change materially alters learner-facing clinical behavior, activates a previously blocked mechanism, changes device-specific quantitative claims, changes scenario resolution logic, or changes a reviewed CBC acceptance relationship. Cosmetic-only changes and internal refactors that demonstrably preserve reviewed behavior do not automatically invalidate the review, but must remain traceable.

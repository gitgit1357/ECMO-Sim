# Product Positioning and Claims Boundary
**Phase:** 5a — broader validation and commercial readiness
**Date:** 2026-08-10
**Status:** LOCKED as project intent; not a legal/regulatory determination

## Intended product position
This project is an **education and simulation-training platform for neonatal ECMO learning and practice**.

The simulator is intended to present internally coherent, clinically plausible cause/effect relationships for training. It is not being developed as a patient-specific physiologic digital twin.

## Claims the project may make now
Claims must stay within evidence already represented in the living capability matrix and Behavior Contracts. Examples of acceptable project-level statements are:

- a named capability is implemented and tested in the current Python runtime;
- a named Clinical Behavior Contract is automated/passing;
- a learner control changes an authoritative modeled mechanism rather than directly patching a monitor value;
- a result is a reduced-order simulation output;
- a behavior or number is provisional, device-specific validation pending, or expert review pending when the matrix says so.

## Claims the project must not make without additional evidence/review
The project must not present itself as having established any of the following unless a later evidence/review gate explicitly supports it:

- patient-specific prediction;
- diagnosis or treatment recommendation authority;
- clinical decision support for a real patient;
- validated treatment thresholds or prescription targets derived only from regression stimuli;
- device-specific performance equivalence where manufacturer/device validation has not been completed;
- institutional-policy equivalence where local policy has not been reviewed;
- regulatory status, clearance, approval, certification, or exemption;
- legal/IP freedom to operate or commercial compliance.

## Evidence hierarchy for stronger claims
A stronger claim must be backed by the appropriate layer rather than by test count alone:

1. **Software implementation** — capability exists in authoritative runtime code.
2. **Software regression** — tests demonstrate repeatable computation/system behavior.
3. **Behavior Contract** — learner-facing directional/range behavior is explicitly protected.
4. **Expert clinical review** — contract assumptions, preconditions, allowed exceptions, and teaching interpretation are reviewed.
5. **Device/institution evidence where applicable** — device curves, operating ranges, local workflow/policy, or other traceable source support is attached.
6. **Commercial/legal/regulatory review where applicable** — performed separately before external claims rely on it.

Passing levels 1–3 does not imply levels 4–6.

## UI rule
Learner-facing application surfaces must visibly identify the workspace as **SIMULATION / TRAINING ONLY**. This label communicates intended product use; it is not represented as a regulatory safe harbor or legal conclusion.

## Ongoing rule
The living capability matrix remains the status authority. Historical completion documents and Behavior Contracts may preserve the state of the project when they were authored and must not override the matrix when later phases legitimately add capability.

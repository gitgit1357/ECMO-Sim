# Neonatal ECMO Simulator — Current Roadmap Status

**Authoritative roadmap:** `FIX_MAP_v4.md`  
**Status overlay date:** 2026-08-10  
**Rule:** this file reports progress against FIX_MAP v4; it does not silently rewrite the settled roadmap.

## Guiding rule

Clinical plausibility outranks mathematical fidelity. Scenario/intervention actions call mechanisms, never monitor-number patches. Behavior Contracts run continuously underneath the numbered phases and do not replace them.

## Phase status

### Phase 0 — Real-time performance
**CLOSED**

- native physiology cache implemented;
- invalidating native solves moved off the Tk/UI thread;
- process-worker/revision/coalescing semantics implemented;
- stale solve results rejected;
- simulation time pauses while native equilibrium is pending;
- long-term sub-second solve performance remains tracked debt rather than a phase gate.

### Phase 1 — Architecture consolidation
**CLOSED**

- legacy JS engine audited and preserved;
- behavioral intent retained; JS runtime retired as active runtime;
- capability matrix established as the single living status authority;
- structured event-record contract implemented;
- deterministic seeded `neoscenarios` primitives implemented;
- Tier-A trigger/orchestration/disclosure semantics ported;
- supported-mechanism registry and first hypovolemia scenario family implemented.

### Phase 2 — Learner loop / GUI tabs
**CLOSED**

Roadmap order completed:

1. Patient Monitor — complete
2. Interventions — complete for currently supported authoritative mechanisms
3. Labs & Diagnostics — complete for currently supported ordered diagnostics, frozen at collection time
4. Ventilator — pressure-control backend and learner controls complete within stated scope
5. Scenario Log — learner-safe rendering of canonical structured event stream complete

Unsupported therapies/analytes/device behaviors remain visibly unavailable rather than simulated by constants or direct patches.

### Ongoing discipline — Clinical + System Behavior Contracts
**CONTINUOUS / PARALLEL — not a numbered phase**

CBC01-CBC11 currently exist. They have been used both to formalize already-correct behavior and to expose narrow runtime defects. Passing a CBC does not equal expert clinical validation.

### Phase 4 — Physiology fidelity gaps
**CLOSED**

- **4a Myocardial dysfunction:** investigated; existing corrected phenotype was adequate; promoted into live runtime mechanism and protected by CBC11. Exact scale-to-severity mapping remains expert-review pending.
- **4b Oxygenator/cannula fidelity:** no deeper model complexity earned; CBC03/CBC05A adequate for currently claimed behavior; device-specific thresholds/curves and absent fault mechanisms remain blocked/deferred.
- **4c CKRT scope:** current Qb + net-UF pathway retained; deeper solute/device/prescription model deferred because no demonstrated Behavior Contract failure currently earns that complexity.

### Phase 5 — Broader validation and commercial readiness
**ACTIVE**

Completed:

- **5a Positioning/claims boundary:** product is explicitly simulation/training; no patient-specific prediction, treatment authority, device equivalence, regulatory-status, or legal/IP claims are inferred from passing software tests.
- **5b Functional UX architecture:** global physiology-latency visibility, context-gated ECMO keyboard controls, and simulator-advisory labeling implemented; device-validated alarm semantics remain deferred.
- **5c Validation readiness:** all 11 CBCs placed into an expert/evidence review queue (7 Priority A learner-operable, 4 Priority B indirect/headless).

Active next work:

- **5d Priority-A evidence/expert review packets** are active; CBC01, CBC02, CBC06, CBC07, and CBC08 external-evidence packets are complete, with expert sign-off pending.
- Evidence review may support directional relationships, but numeric/device/institution-specific claims stay gated until the required evidence and expert disposition exist.

Future Phase-5 work remains separate from the current software correctness track:

- human expert dispositions and documented allowed exceptions;
- institution/device-specific evidence where needed;
- external-training readiness decisions;
- formal commercial/legal/IP/regulatory review only when there is a product ready for that review;
- cosmetic polish after functional/safety UX priorities.

## Current primary-track next action

Complete Priority-A review packets in order of learner exposure and risk, updating the living capability matrix after each disposition. Do not resume opportunistic model expansion unless an evidence review or Behavior Contract exposes a demonstrated gap that materially affects the learner.


## Phase 5d update — CBC02
- CBC02 Sweep-Gas Failure external evidence packet complete; expert sign-off pending.
- Evidence review clarifies the zero-sweep oxygen assertion is a sustained/post-transient state; residual gas washout is not dynamically modeled.
- Next primary-track action: continue Priority-A evidence packets.

- CBC02 Sweep-Gas Failure evidence packet complete; expert sign-off pending.


## Phase 5d update — CBC06
- CBC06 CKRT Net Ultrafiltration external evidence packet complete; expert sign-off pending.
- Evidence supports CKRT/CRRT fluid removal during pediatric ECMO and explicit delivered-UF accounting.
- The simulator activation gate (`CKRT selected + Qb > 0`) remains an implementation/workflow rule requiring expert review, not a universal device claim.
- Phase 2b learner Qb/net-UF controls are now reflected correctly in CBC06 and the living matrix.
- Qb, net-UF, duration, recovery tolerances, and hemodynamic magnitudes remain regression-only.
- Next primary-track action: continue Priority-A evidence packets.


## Phase 5d update — CBC07
- CBC07 Positive-Airway-Pressure Hemodynamics external evidence packet complete; expert sign-off pending.
- External pediatric/neonatal evidence supports a possible reduction in forward output with higher PEEP but also shows heterogeneous and often modest systemic effects; CBC07's monotonic CO/MAP path is therefore explicitly a canonical regression teaching path, not a universal patient prediction.
- The measured-CVP guardrail remains: higher CVP under positive airway pressure does not prove increased blood volume or effective transmural preload.
- Phase 2d learner pressure-control ventilator controls are now reflected correctly in CBC07.
- The PEEP-to-ECMO drainage relationship remains BLOCKED pending a transmural preload interface.
- Queue bookkeeping corrected: CBC01 and CBC02 now carry the same external-evidence-packet-complete/expert-signoff-pending status as CBC06/CBC07.
- Next primary-track action: continue the remaining Priority-A evidence packets.


## Phase 5d update — CBC08
- CBC08 FdO2 Oxygen-Fraction Control external evidence packet complete; expert sign-off pending.
- External evidence supports the gas-control distinction: oxygen fraction delivered to the membrane lung is an oxygenation control, while sweep-flow rate is the dominant CO2-removal control.
- Adult VA-ECMO randomized evidence directly shows gas-blender oxygen-fraction titration changing post-oxygenator oxygenation while ECMO blood flow remained similar between groups.
- Exact FdO2 probe values, the reduced-order post-oxy pO2 curve, Hill constants, and device-specific transfer magnitudes remain regression-only / device-validation pending.
- Coupled-patient FdO2 behavior remains BLOCKED until an authoritative central-venous oxygen state exists.
- Next primary-track action: continue remaining Priority-A evidence packets.


## 2026-08-10 Phase 5d CBC09 update
- CBC09 Bridge Recirculation / Flow Diversion evidence packet complete; expert sign-off pending.
- Next: CBC10 Fixed-Shunt Configuration evidence packet.

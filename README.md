# Neonatal ECMO Simulation Training Platform

**Current internal build:** v0.21.0  
**Positioning:** simulation / training only  
**Status authority:** `CAPABILITY_MATRIX.json`  
**Roadmap authority:** `FIX_MAP_v4.md` with current progress in `ROADMAP_CURRENT_STATUS_2026-08-10.md`

## What this project is

A reduced-order neonatal ECMO training simulator designed to present clinically plausible, internally coherent cause/effect relationships to a learner. It is not intended to be a patient-specific digital twin, diagnostic tool, treatment-recommendation system, or controller for a real medical device.

The current integrated learner workspace includes:

- VA-ECMO console controls and coupled patient/circuit behavior;
- Patient Monitor;
- Interventions for currently supported authoritative mechanisms;
- ordered Labs & Diagnostics with frozen sample-time semantics;
- pressure-control Ventilator controls;
- learner-safe Scenario Log;
- deterministic scenario-engine primitives and structured event records;
- Clinical Behavior Contracts (CBC01–CBC11) protecting defined learner-facing behavior.

## Run the learner workspace

Python 3.11+ is required.

```bash
python -m pip install -e .[dev]
python examples/run_ecmo_workspace.py
```

Windows convenience launcher:

```text
run_ecmo_workspace.bat
```

Run the test suite:

```bash
pytest
```

Because some physiology equilibrium tests are intentionally slow, project verification records use bounded test groups when the execution harness has a timeout. A timeout is never counted as a pass or failure without a completed process exit.

## Current validation/review state

- All 11 CBCs have received a **single-reviewer clinical review** by the project author, a practicing ECMO specialist.
- Priority-A CBCs have 7/7 external evidence packets.
- Independent facility-educator clinical review remains pending and is required before external-training/go-live.
- Formal regulatory, legal/IP, trademark, institutional, and commercial-clearance determinations remain separate pending reviews.

See:

- `PHASE5D_SINGLE_REVIEWER_CLINICAL_REVIEW_2026-08-10.md`
- `external_review/INDEPENDENT_CLINICAL_REVIEW_PACKET.md`
- `external_review/EXTERNAL_TRAINING_GO_LIVE_GATE.md`
- `commercial_review/REGULATORY_AND_IP_REVIEW_READINESS.md`

## Important fidelity boundaries

The simulator intentionally does not represent every clinical or device mechanism. The capability matrix identifies supported, partial, and blocked behavior. Current notable blocked/deferred areas include:

- VA differential hypoxemia / upper-vs-lower-body oxygenation state;
- PEEP-to-ECMO drainage through a true transmural preload interface;
- coupled-patient FdO₂ response through an authoritative central-venous oxygen state;
- hemofilter net-fluid removal into the patient without a bounded prescription path;
- vasoactive/inotrope, sedation/analgesia, electrolyte/calcium, and blood-component-specific intervention mechanisms;
- complete CBC/chemistry/coagulation/lactate laboratory state;
- device-validated alarm priority/acknowledge/silence behavior.

Those gaps are disclosed rather than approximated with direct monitor-number patches.

## Core engineering rules

1. Clinical plausibility outranks mathematical fidelity.
2. Learner/scenario actions call mechanisms; they do not directly patch monitor values.
3. Labs are frozen point-in-time samples, not continuously updating monitor channels.
4. A passing software test is not automatically a clinical, device, regulatory, or legal validation claim.
5. Behavior Contracts run continuously underneath the numbered roadmap phases.
6. Model complexity earns its way in only when a demonstrated learner-facing contract or validation need requires it.

## Project navigation

- `CAPABILITY_MATRIX.md/.csv/.json` — living implementation and validation-status authority
- `FIX_MAP_v4.md` — settled roadmap
- `ROADMAP_CURRENT_STATUS_2026-08-10.md` — current progress overlay
- `VALIDATION_REVIEW_QUEUE.md/.json` — CBC review/evidence disposition
- `clinical_behavior_contracts/` — CBC definitions and non-claims
- `validation_packets/` — external evidence packets
- `external_review/` — independent clinical-review readiness package
- `commercial_review/` — regulatory/legal/IP review-readiness package
- `HANDOFF.md` — append-only project handoff
- `CHANGELOG.md` — historical implementation progression

Historical stage documents are intentionally retained as provenance. When a historical document conflicts with current status, `CAPABILITY_MATRIX.json` is authoritative.

# Neonatal ECMO Sim Platform — Fix Map v6 Authorization Record
Date: 2026-08-11
Status: AUTHORIZED governing roadmap

The project owner authorized Fix Map v6 as the governing roadmap after audited closure of Fix Map v5.

Concrete authorization created by that decision:
- Phase 9a.0 — Unified Venous-State Foundation feasibility/ownership audit: AUTHORIZED TO BEGIN.
- Phase 9b.0 — Typed Scenario→Mechanism Activation Contract feasibility audit: AUTHORIZED TO BEGIN.
- Phase 9a.1+ and 9b.1+: NOT PRE-AUTHORIZED; each requires its own audit to conclude PROCEED before implementation is separately authorized.
- Phase 10 and everything later: UNOPENED / UNAUTHORIZED / UNSHARPENED.

Governing conventions authorized with the map:
1. Teaching-fidelity standard: directionally correct, plausible/tunable magnitude, explicitly non-validated quantitative claims, CBC-style contracts for new mechanisms, no fabricated responses.
2. Three-gate lifecycle: Gate 1 engineering evidence; Gate 2 single-reviewer internal clinical completion; Gate 3 independent external-training clearance.
3. Audit-before-authority: any new authoritative state owner/mechanism/major architectural responsibility begins with a feasibility/ownership audit; STOP/RESCOPE is a successful outcome.
4. Per-item independence: 9a and 9b each receive their own audit conclusion.
5. No later phase is opened by roadmap authorization alone.

This record preserves the actionable authorization boundary. The full roadmap text remains the project-owner-authorized Fix Map v6 supplied on 2026-08-11; this audit does not modify or sharpen Phase 10+.


## Authorization update — Phase 9a.1+
The project owner subsequently explicitly authorized **Phase 9a.1+**, bound to the 9a.0 constraints:
- `VenousState` is an immutable patient-boundary container, not a new solver.
- CVP remains sourced from native `mean_ra_mmhg`.
- effective venous volume remains volume-ledger-owned.
- native mixed-venous oxygen remains `neocoupling`-owned.
- the preload proxy is explicitly derived and disclosed as illustrative/not quantitatively validated.
- the structural no-projection-feedback guard from 9a.5 is mandatory.

`9b.1` remains unauthorized because 9b.0 concluded no generalized new surface is needed.

Sequential intent is recorded as 9a.1, then 10a → 10b → 11 only as each later phase is individually authorized. This update does **not** authorize Phase 10 or later work.

## Authorization update — Phase 10a
On 2026-08-11 the project owner explicitly directed implementation of **Phase 10a** from the verified Phase 9a complete baseline.

Authorized scope is limited to the PEEP→ECMO drainage coupling that Phase 9a made possible: consume the canonical intrathoracic-relative preload proxy at the patient→ECMO drainage boundary, protect the direction as bounded/reversible educational behavior, extend CBC07/documentation accordingly, and correct stale capability-matrix statements. This authorization does not open Phase 10b or Phase 11.


## Authorization update — Phase 10b
After verified completion of Phase 10a, the project owner directed the project to continue. In the established sequential context (10a → 10b → 11), that direction opens **Phase 10b only**.

Authorized scope is the FdO2→coupled-patient oxygenation path through the Phase 9a authoritative native mixed-venous inlet state, extending CBC08. Implementation must prefer existing authoritative pathways over a new oxygen solver, protect directional/bounded/reversible educational behavior, preserve fixed-sweep CO2 and hydraulic separation, and leave differential hypoxemia/Harlequin physiology for separately authorized Phase 11.

## Authorization update — Phase 11 audit
After verified completion of Phase 10b, the project owner again directed the project to continue. In the established sequential context (10a → 10b → 11), that direction opens **Phase 11 for feasibility/ownership audit**.

Because Phase 11 would introduce a new regional arterial-oxygenation/mixing-point mechanism, the governing audit-before-authority rule applies before physiology implementation. The audit must determine whether the current neonatal VA topology can support the intended differential-hypoxemia teaching contract without importing femoral-VA assumptions that are not represented by the simulator.


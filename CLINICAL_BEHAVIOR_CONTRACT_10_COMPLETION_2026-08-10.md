# Clinical Behavior Contract 10 Completion — Fixed-Shunt Configuration / Hemofilter Hydraulics

**Date:** 2026-08-10  
**Build target:** v0.17.13  
**Contract:** `cbc.ecmo.fixed-shunt-configuration.v1`

## Decision

CBC10 was intentionally constrained to the fixed-shunt **configuration/hydraulic** behavior the Python runtime already owns. It does not promote the lower-level hemofilter filtrate-removal helper into coupled-patient physiology.

## Probe result

At fixed patient boundary and pump settings:

- OPEN and CKRT produce the same fixed-shunt hydraulics in the current 3-way side-port model.
- Installing HEMOFILTER adds inline resistance, decreases shunt flow/fraction, and redistributes a small amount of flow toward the patient branch.
- `scuffing_active` on/off with HEMOFILTER already installed does not change hydraulics.
- The lower-level hemofilter removal helper is not connected to `CoupledVaEcmoPatient`; the console also exposes no clinically bounded hemofilter-UF prescription.

The provisional `FixedShuntParameters.ultrafiltration_rate_ml_min = 10.0` therefore remains an implementation placeholder and is **not** promoted into patient fluid removal by this contract.

## Contracted behavior

CBC10 protects:

1. inline HEMOFILTER resistance lowers shunt diversion relative to OPEN;
2. some flow redistributes toward the patient branch at fixed RPM;
3. closed-loop MAP support does not fall solely because shunt diversion is reduced;
4. `scuffing_active` is hydraulically neutral;
5. CKRT is hydraulically equivalent to OPEN in the current side-port model;
6. branch conservation remains intact.

## Blocked prerequisite

`Hemofilter net-fluid removal to coupled patient` is now a dedicated BLOCKED capability-matrix row. Before that behavior can be contracted, the model needs a clinically bounded prescription/control and an explicit coupled-patient handoff rather than reuse of the provisional helper default.

## Restoration scope

Returning HEMOFILTER configuration to OPEN reproduces the original operating point. This is immutable/configuration determinism, not proof of stateful filter insertion/removal, priming, de-airing, clot clearing, or recovery.

## Source changes

None. All 93 non-generated files under `src/` are byte-for-byte unchanged from v0.17.12.

## Fresh verification

Zero-exit batches:

- CBC01/CBC04/CBC06/CBC07/CBC10: 20/20
- CBC02/CBC03/CBC08: 13/13
- CBC05A/CBC09: 9/9
- fixed-shunt/main-circuit/console: 62/62
- coupled VA/preload/time-step: 27/27
- workspace/ready-scenario integration: 20/20

**Total: 151 passed, 0 failed.**

Exact-tree collection: **392 tests**.

## Capability matrix

- 76 unique rows.
- CSV and JSON mirrors identical.
- Phase 1b backing inventory unchanged: 79 actions / 36 complications / 28 scenario ID migrations.

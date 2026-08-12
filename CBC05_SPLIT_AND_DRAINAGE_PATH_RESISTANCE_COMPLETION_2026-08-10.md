# CBC05 Split Decision + CBC05A Completion — 2026-08-10

CBC05 was not forced into a single generic drainage-obstruction contract.

Empirical probing of the current Python runtime showed:

- the existing drain-cannula hydraulic coefficient is a legitimate patient-path resistance primitive: increasing it reduces patient-directed and total flow and shifts a larger fraction of solved flow through the always-open shunt;
- the existing common pre-pump resistance changes displayed P1 but does not alter the branched operating-point root solve, so it is not sufficient evidence for a common mechanical-obstruction fault;
- no position/cannula-position state exists, so position-sensitive maldrainage cannot be represented honestly.

Decision:

- CBC05A `cbc.ecmo.drainage-path-resistance.v1`: implemented and automated.
- CBC05B common pre-pump obstruction: blocked pending a solved flow-limiting fault mechanism.
- CBC05C position-sensitive drainage compromise: blocked pending explicit positional state.

CBC05A intentionally makes no mandatory P1-direction assertion. In the project's always-open shunt topology, recirculated shunt flow joins the drainage side before the pump and can preserve pump-inlet supply while patient drainage falls. Patient-directed flow and shunt fraction are therefore more reliable contract signals than assuming gross flow or P1 behaves as in a conventional no-shunt ECMO circuit.

The resistance multiplier is a regression stimulus only. It is not a percent occlusion or clinically validated kink severity.

CBC05A restoration is currently deterministic re-evaluation of immutable hydraulic parameters, not stateful kink recovery. A future mutable kink fault must replace that restoration branch with activation/clear testing.

## Fresh verification

- CBC01-CBC05A contract tests: 17/17 passed.
- Coupled patient/cache/preload/MAP: 21/21 passed.
- Main-circuit/oxygenator/gas: 64/64 passed.
- ECMO workspace integration/events/model: 11/11 passed.
- Ready scenario + Tier-A vertical slice: 10/10 passed.
- Scenario primitives: 16/16 passed.
- Tier-A orchestration: 10/10 passed.

Total fresh bounded verification for this block: **149 passed, 0 failed**.

Exact tree collection: **366 tests**.

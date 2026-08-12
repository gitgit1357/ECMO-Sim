# NorthStar Regression Bench v1

This directory preserves a fixed, repeatable cardiovascular regression test that is rerun after each new modular patient system is attached.

## Boundary rule
The patient circulation engine owns anatomy and physiology only. Pump and cannula models are **external test fixtures**. The core engine never imports this folder or `bench_fixtures`.

## Frozen v1 test matrix
- Normal 3.5 kg / 72-hour term-neonate baseline
- Closed-loop VA fixed-flow steps: 0, 50, 100, 150, 200 mL/kg/min
- External cannula fixture sizes: 9, 11, 13, 15 Fr
- External deterministic centrifugal pump fixture: 2000, 3000, 4000, 5000 RPM

The synthetic centrifugal pump fixture is **not** a manufacturer device model. It exists only to make RPM/head/flow regression testing deterministic. Manufacturer pump curves can later be added as separate external fixtures without changing the patient.

## Commands
Run and save current results:

`py .\regression_bench\run_northstar.py`

Compare current engine against the accepted v1 reference:

`py .\regression_bench\compare_northstar.py`

## Change control
Never overwrite the accepted snapshot merely because a new system changes results. First determine whether the change is:
1. an unintended regression,
2. an expected interaction that should remain inside the old tolerance envelope, or
3. a deliberate model improvement requiring a new accepted reference version.

A new accepted reference must use a new filename/version and document why the expected physiology changed.

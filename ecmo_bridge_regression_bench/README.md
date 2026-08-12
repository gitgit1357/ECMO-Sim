# ECMO Bridge NorthStar Regression Bench v1

Independent of the pump, oxygenator, fixed shunt, cardiovascular, lung,
kidney, and coupling NorthStar benches. Covers only the Stage 4 standalone
bridge branch (`neoecmo.bridge`) — clamp-position hydraulics only. No
stagnation-clock, clot-risk-from-dwell-time, flush-validity, sensor, or
patient-coupling logic is included yet (those are a later cross-branch
risk-tracking stage, deliberately not blended in here).

Frozen cases sweep clamp position at a fixed pressure boundary, and
separately confirm the fully-closed state stays a hard zero across several
different pressure gradients (including a reversed one).

The resistance model is explicitly provisional (see `bridge.py`
`BridgeParameters` docstring — no bridge tubing/clamp hardware is locked
yet). This bench freezes the *behavior* of the current provisional model
so future solver/harness changes cannot silently alter it; it does not
assert the absolute numbers are clinically validated.

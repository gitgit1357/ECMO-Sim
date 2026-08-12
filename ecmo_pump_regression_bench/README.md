# ECMO Pump-Head NorthStar Regression Bench v1

This bench is independent of the cardiovascular, lung, kidney, and coupling
NorthStar benches. It covers only the Stage 1 standalone pump-head hydraulic
bench (`neoecmo`) — no oxygenator, shunt, bridge, cannula, sensor, or patient
coupling behavior is included yet.

Frozen cases sweep RPM at a fixed set of boundary pressures/resistances.

The `neoecmo` module must pass its standalone bench before any oxygenator,
shunt, bridge, or cannula hydraulics are added, and before any coupling to
the native patient physiology engines is enabled.

The pump curve itself is explicitly provisional (see `pump.py`
`PumpHeadCurveParameters` docstring). This bench freezes the *behavior* of
the current provisional curve so future changes to the solver, bench
harness, or unrelated modules cannot silently alter it — it does not assert
that the curve's absolute numbers are clinically validated. When the curve
is replaced with real manufacturer/bench data, this snapshot must be
deliberately re-accepted, not silently overwritten.

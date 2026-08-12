# ECMO Oxygenator Hydraulics NorthStar Regression Bench v1

Independent of the pump, cardiovascular, lung, kidney, and coupling
NorthStar benches. Covers only the Stage 2 standalone oxygenator
hydraulics-only bench (`neoecmo.oxygenator`) — mechanical resistance and
flow-dependent pressure drop across obstruction/clot states. No gas
exchange, membrane oxygen/CO2 transfer, or heat exchanger behavior is
included yet (handoff section 21 gas-exchange and heat-exchanger
requirements remain a later stage).

Frozen cases sweep flow at three obstruction states (clean, mild clot,
severe clot).

The oxygenator hydraulics module must pass its standalone bench before gas
exchange is added, and before this stage is wired into the fixed-shunt/
branch-distribution or patient-coupling stages.

The resistance model is explicitly provisional (see `oxygenator.py`
`OxygenatorHydraulicParameters` docstring — no oxygenator make/model is
locked yet). This bench freezes the *behavior* of the current provisional
model so future solver/harness changes cannot silently alter it; it does
not assert the absolute numbers are clinically validated. Replacing the
model with real manufacturer/bench data requires a deliberate re-accept of
this snapshot, not a silent overwrite.

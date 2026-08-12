# ECMO Fixed Shunt NorthStar Regression Bench v1

Independent of the pump, oxygenator, cardiovascular, lung, kidney, and
coupling NorthStar benches. Covers only the Stage 3 standalone fixed-shunt
branch (`neoecmo.fixed_shunt`) — hydraulics of the always-open,
non-adjustable shunt path, with or without a scuffing filter installed.
No bridge, cannula, sensor, or patient-coupling logic is included yet, and
no circuit-level flow-distribution coordinator combines this branch with
the main circuit yet (handoff section 13 Stage 4 covers that once bridge
and cannula branches also exist standalone).

Frozen cases sweep downstream (pre-pump) pressure at a fixed upstream
(post-oxygenator) pressure, across four configurations: OPEN (no filter,
no CKRT), HEMOFILTER inactive, HEMOFILTER active, and CKRT. HEMOFILTER
and CKRT occupy the same two stopcock positions as alternatives to each
other, but CKRT's stopcocks are 3-way — the main shunt flow passes
straight through unaffected (matching OPEN's hydraulics exactly) while a
side port on each stopcock feeds the CKRT machine's own independent pump.
CKRT's own blood flow is tracked but never affects the shunt's own
calculation (confirmed directly, chat 2026-07-26 — CKRT does not use the
total blood volume flowing through the shunt line).

The resistance model is explicitly provisional (see `fixed_shunt.py`
`FixedShuntParameters` docstring — no scuffing-filter make/model is locked
yet). This bench freezes the *behavior* of the current provisional model
so future solver/harness changes cannot silently alter it; it does not
assert the absolute numbers are clinically validated.

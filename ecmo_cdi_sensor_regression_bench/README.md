# ECMO CDI Sensor NorthStar Regression Bench v1

Independent of all prior standalone, wiring-stage, and gas-exchange
NorthStar benches. Covers the CDI mixing sensor (`neoecmo.cdi_sensor`) —
flow-weighted mixing of native venous blood and bridge recirculation at
the CDI's real confirmed position on the drain limb.

Confirmed circuit anatomy (chat 2026-07-26): patient -> 8" -> bridge tee
-> 8" -> CDI -> 4" -> venous access pigtail -> 6" -> manifold -> 6" ->
shunt/transducer T -> 4" -> pump. The CDI sits downstream of the bridge
tee (bridge recirculation reaches it under normal forward flow) but
upstream of the shunt/transducer T (shunt recirculation does NOT reach it
under normal forward flow — only via retrograde flow, which this
reduced-order sensor does not model).

Frozen cases sweep bridge clamp position at a fixed RPM, computing the
CDI reading against a fixed assumed native venous saturation/pCO2 and the
gas-exchange module's post-oxygenator saturation/pCO2 at that operating
point.

**Key structural guarantee, tested and frozen**: at clamp_position=0.0
(bridge closed), the CDI reading equals the native venous value exactly
— zero recirculation contamination. This must never regress; any change
here would mean the CDI is picking up shunt or some other unintended
flow path.

This bench freezes the *behavior* of the current provisional models
composed together (pump, oxygenator, shunt, bridge, cannulas, gas
exchange, plus the vasculature placeholder) — it does not assert the
absolute numbers are clinically validated beyond the topology guarantee
above.

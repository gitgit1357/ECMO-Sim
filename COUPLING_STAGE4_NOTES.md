# Coupling Stage 4 — volume, preload, drainage limitation, and chatter

Added `neoecmocoupling.preload` as a separate reduced-order coupling layer.

Behavior protected:
- Falling blood-volume fraction lowers effective venous preload/CVP.
- Lower preload reduces sustainable ECMO drainage and patient-directed flow.
- P1 becomes more negative as the circuit attempts to drain a volume-limited patient.
- Excess pump demand relative to sustainable drainage activates a chatter state.
- Patient-directed flow is capped at sustainable venous drainage; impossible excess demand is not left as delivered patient flow.
- Chatter reports a severity and an expected low/high patient-flow range for later dynamic animation.
- Lowering RPM reduces the drainage-demand ratio and can reduce or clear chatter.
- Bridge and shunt flow do not increase patient drainage capacity or patient perfusion.

All gains and thresholds are isolated in `PreloadDrainageConfig` and remain provisional behavioral parameters pending clinical tuning.

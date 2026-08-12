# CBC11 — Myocardial Dysfunction v1

Contract ID: `cbc.patient.myocardial-dysfunction.v1`

## Purpose
Protect the learner-facing direction and reversibility of native LV/RV contractility loss without asserting a clinically validated mapping between the dimensionless contractility scale and a named severity grade.

## Preconditions
- Native cardiopulmonary patient solve is active.
- No concurrent blood-volume, vascular-tone, or ECMO-support change is introduced during the isolated comparison.
- Contractility is changed only through `MyocardialFunctionPort` / `patient.set_myocardial_function`.

## Required behavior
### LV dysfunction
Reducing LV contractility from baseline must reduce native cardiac output and MAP. A larger reduction must produce a larger hemodynamic effect than a mild reduction. The existing isolated failure bench must continue to show increased left-sided filling/chamber-volume proxies during severe LV dysfunction.

### RV dysfunction
Reducing RV contractility must reduce native cardiac output, pulmonary forward flow, and MAP while increasing measured CVP/RA filling pressure. The isolated failure bench must continue to show increased RV filling/chamber-volume proxies during severe RV dysfunction.

### Reversal
Returning both contractility scales to 1.0 on the same unified patient must return the isolated equilibrium toward baseline without resetting volume state.

## Explicit non-claims
- `0.70`, `0.30`, or `0.15` are regression stimuli, not validated clinical severity categories.
- No universal relationship between percent contractility loss and percent cardiac-output loss is claimed.
- No inotrope/vasoactive treatment response is modeled by this contract.
- No arrhythmia, ischemia, myocarditis, stunned myocardium, LV distension, valve disease, or regional dysfunction is implied.
- No learner GUI control for myocardial function is added here.

## Known sensitivity / future retest condition
The current model is strongly nonlinear: a mild scale reduction can be substantially buffered, while severe reductions produce a large failure phenotype. If expert review requires a different scale-to-severity relationship, revise the myocardial model only against a new Behavior Contract; do not add monitor-number patches.

If a persistent named myocardial-failure fault state or inotrope mechanism is later introduced, repeat the recovery and treatment branches through those stateful mechanisms.

## Status
Automated behavior contract: passing.
Expert clinical validation of scale/severity mapping: pending.

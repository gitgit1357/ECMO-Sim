# v0.15.0 — Coupling Stage 5 (2026-07-28)

- Added time-stepped modular patient/VA-ECMO coordinator.
- Added bounded native cardiac-output suppression from VA drainage/preload diversion.
- Applied coupled MAP, pulse pressure, effective systemic flow, mixed arterial gases, renal perfusion, urine, CKRT removal, and volume feedback.
- Added integrated Stage 5 behavioral tests.

# v0.35.0-dev (ECMO circuit, consolidated control surface)

- Added `ecmo_console.py`: the single consolidated control surface for every real learner-adjustable input across the whole circuit — RPM, bridge (titrated by target flow, the confirmed realistic clinical action, with direct clamp_position still available for testing), shunt line configuration (OPEN/HEMOFILTER/CKRT) and its sub-controls, sweep gas FdO2 (rounded to the real Spectrum blender's 1% steps) and sweep gas flow. One call now returns everything the monitor would show (solved flows/pressures, post-oxygenator saturation/pCO2, CDI reading) instead of the half-dozen separate calls this previously required.
- Device specs and pathology/complication state (clot fractions, pump curve, cannula sizing) are deliberately kept as separate pass-through parameters with clean defaults, not learner controls — a scenario/complication engine would inject those, not the console itself.
- Found and fixed a real gap while building this: `solve_bridge_clamp_position_for_target_flow()` had no way to account for bridge clot state, silently dropping it whenever target-flow titration was used instead of direct clamp control. Added a `bridge_clot_fraction` parameter (backward compatible, existing calls unaffected) and verified clotted bridges now correctly require more opening to reach the same target flow.
- Added 13 new tests for the console (basic operation, bridge titration achieving its exact target, shunt configuration switching, FdO2 rounding and its effect on saturation, sweep flow's effect on CO2 clearance, pathology pass-through) plus 1 new test for the bridge_clot_fraction fix.
- Added `ecmo_console_regression_bench/` (ECMO Console NorthStar v1): 5 representative control combinations (bridge closed, bridge titrated, hemofilter active, CKRT running, low FdO2/low sweep), each exercising the entire stack through the console's single interface, frozen and passing.
- Full suite re-verified end to end in batches: 244/244 passing (81 pre-existing + 163 neoecmo), zero regression.
- This is the circuit's full control surface, complete for everything built so far. Native venous saturation/pCO2 remain required external inputs — real patient physiology coupling is still a separate, larger effort.



- Refined the CKRT model with a further clarification: the CKRT machine is blood-primed on initiation (no volume-bolus effect on connection), and while running it does pull some — not all — of the blood flowing through the shunt line via its own pump, returning that same volume minus only the amount intentionally removed (net ultrafiltration). This is typically small relative to blood flow, so shunt hydraulics remain correctly modeled as unaffected (unchanged from the previous fix), but CKRT's own continuous small net fluid removal was missing and needed adding.
- Generalized `ScuffingFiltrationState`/`step_filtrate_removal` (previously HEMOFILTER-only) to also handle CKRT's own net ultrafiltration, via a new `ckrt_net_ultrafiltration_rate_ml_min` field. Removal now happens whenever the CKRT machine is actually running (`ckrt_blood_flow_ml_min > 0`), separate from the HEMOFILTER path's `scuffing_active` flag — the two mechanisms share the same tracked cumulative-volume state but use different trigger conditions and rates.
- Added 3 new tests: CKRT net UF accumulates while the machine is running, does not accumulate if the machine isn't actually connected/running (blood flow = 0) even with a rate configured, and a sanity check that the net UF rate is meaningfully smaller than the CKRT blood flow rate (matching the "returns nearly all of what it draws" clinical description).
- Shunt hydraulics NorthStar snapshot reconfirmed unaffected (this change only touches the separate filtrate-tracking state, not `fixed_shunt_flow_ml_min`).
- Full suite re-verified end to end in batches: 230/230 passing (81 pre-existing + 149 neoecmo), zero regression.



- Restructured `fixed_shunt.py`'s binary `scuffing_filter_installed` flag into a proper `ShuntLineConfiguration` enum (OPEN / HEMOFILTER / CKRT), matching the confirmed real anatomy: two stopcocks on the shunt line, connected to each other in normal operation, with the hemofilter placeable inline between them as an alternative.
- **Initial CKRT implementation was wrong and got corrected in the same session**: first built CKRT as fully disconnecting the shunt line (forcing zero ECMO-driven shunt flow), based on an incorrect assumption that the stopcocks were simple 2-way on/off valves. Corrected after clarification: the stopcocks are 3-WAY — the main shunt flow continues to pass straight through unaffected regardless of CKRT being attached (identical hydraulics to OPEN), while a side port on each stopcock feeds the CKRT machine's own independent pump. CKRT's own blood flow does not use, share, or reduce the shunt's own flow (confirmed directly).
- `ckrt_blood_flow_ml_min` added as a tracked-only field (the CKRT machine's own prescription/settings) with zero effect on shunt hydraulics — verified explicitly by test.
- HEMOFILTER and CKRT are mutually exclusive alternate uses of the same two stopcock positions (only one can occupy the inline path at a time); filtrate-removal tracking remains HEMOFILTER-specific and is a no-op during CKRT even if the (irrelevant) scuffing_active flag were set.
- Updated all dependent tests, the NorthStar bench (added a 4th "ckrt" case, corrected mid-session to match OPEN's values instead of the initially-wrong zero), and this changelog to reflect the corrected model. Wiring-stage modules (main_circuit_with_shunt*, main_circuit_full) were unaffected since they only ever used FixedShuntParameters() defaults (configuration=OPEN).
- Added/updated tests: CKRT-behaves-identically-to-OPEN hydraulically, CKRT still responds to shunt clot fraction, CKRT's own blood-flow field has zero hydraulic effect, CKRT gives more shunt flow than HEMOFILTER (since it doesn't add filter resistance), plus the existing OPEN/HEMOFILTER coverage carried over.
- Full suite re-verified end to end in batches: 227/227 passing (81 pre-existing + 146 neoecmo), zero regression.



- Added `cdi_sensor.py`: flow-weighted mixing at the CDI's real confirmed position on the drain limb (patient -> 8" -> bridge tee -> 8" -> CDI -> 4" -> venous access pigtail -> 6" -> manifold -> 6" -> shunt/transducer T -> 4" -> pump, confirmed anatomy from chat 2026-07-26). Blends native venous blood with bridge recirculation only. Shunt flow is structurally never a parameter anywhere in this module — enforced by test (signature inspection, not just behavior) — since the shunt tee sits downstream of the CDI and cannot contaminate it under normal forward flow.
- **Critical topology guarantee verified**: with the bridge closed, the CDI reads the native venous value exactly — zero recirculation contamination. Frozen into the NorthStar snapshot with an explicit hard check (not just tolerance-based comparison) so this can never silently regress.
- **Notable finding from the swept snapshot**: even a 2% bridge crack (clamp_position=0.02) already shows 25.5% recirculation fraction and shifts the CDI-read saturation from a true 65% to an apparent 73.7% — a clinically real and significant false elevation from a very small opening. Good demonstration of why bridge management requires care, and a strong candidate for a future training scenario ("why did the venous sat suddenly look better with nothing else changing?").
- Added `cdi_reading_from_circuit_point()`: convenience wrapper that takes an already-solved `MainCircuitFullPoint` directly, returning a `CDIReading` (mixed saturation, recirculation fraction, optional mixed pCO2).
- Added 14 new tests: the bridge-closed-reads-pure-native guarantee (both directions — saturation and pCO2), recirculation-fraction monotonicity, structural shunt-exclusion (via signature inspection), degenerate zero-flow fallback, and the circuit-point wrapper's consistency with manual calculation.
- Added `ecmo_cdi_sensor_regression_bench/` (ECMO CDI Sensor NorthStar v1): clamp-position sweep at fixed RPM, frozen and passing, with an extra hard check beyond normal tolerance comparison confirming the bridge-closed case shows exactly zero recirculation.
- Full suite re-verified end to end in batches: 222/222 passing (81 pre-existing + 141 neoecmo), zero regression.



- Confirmed real sweep-gas hardware and practice: a Spectrum O2 blender fed by both medical air and O2, normally run at 100% FdO2, adjustable in 1% increments from 21% (room air floor) to 100%. Updated `oxygenator_gas_exchange.py` docstrings from "not confirmed, defaults to 1.0 pending confirmation" to reflect this as confirmed practice.
- Added `MIN_FDO2`/`MAX_FDO2`/`FDO2_BLENDER_STEP` constants and `round_fdo2_to_blender_step()`, which clamps to the blender's real physical range and rounds to the nearest 1% — for whenever a future interface exposes this as a dial rather than an arbitrary float, the same way ventilator FiO2 is titrated.
- `outlet_o2_saturation()` now floors fdo2 at the blender's real 21% minimum (previously floored at an arbitrary 0.0) — a value below what the hardware can physically produce now behaves identically to the floor itself rather than implying an unachievable lower FdO2.
- Added 4 new tests: blender clamping at both ends of its real range, 1% rounding behavior, and the floor-behaves-like-21%-not-lower guarantee.
- NorthStar snapshot reconfirmed unaffected (existing cases use fdo2=1.0, unaffected by the floor change).
- Full suite re-verified end to end in batches: 208/208 passing (81 pre-existing + 127 neoecmo), zero regression.



- Added `oxygenator_gas_exchange.py`: O2 saturation transfer and CO2 clearance for the Eurosets AMG PMP Infant oxygenator (confirmed as the correct device family — the ECMO-cleared Eurosets pediatric/infant line, indicated for infants up to 20 kg), separate from the hydraulics-only oxygenator module.
- **Real, confirmed value used**: min_flow_ml_min = 250 mL/min (the Eurosets AMG PMP Infant's stated minimum flow to prevent clot formation), replacing the earlier 200 mL/min guess in both the gas exchange module and the pre-existing hydraulics module's min_recommended_flow_ml_min default.
- **Provisional values used** (flagged, pending real AMG PMP Infant specs): rated_flow_ml_min = 1500 and the transfer-efficiency shape, grounded in a comparable device (Maquet Quadrox-i Neonatal: rated 1.5 L/min, ~90 mL O2/min and ~73 mL CO2/min transfer at that flow, tapering to ~15/~10 mL/min at 0.2 L/min).
- O2 transfer modeled as a reduced-order efficiency curve (full transfer at/below rated flow, tapering as blood flow outpaces the membrane — the real "outpacing the oxygenator" phenomenon), capped by an FdO2-dependent achievable-saturation ceiling (fdo2 defaults to 1.0/pure-O2 sweep pending confirmation of actual sweep-gas practice). CO2 clearance modeled separately, governed by sweep:blood flow ratio rather than blood flow alone, matching the real clinical lever for CO2 removal. Both degrade with membrane obstruction/clot state.
- The oxygenator never actively desaturates blood already above what the current FdO2/flow could achieve — verified explicitly by test.
- Documented (not yet built) the CDI recirculation topology confirmed this session: CDI sits on the drain limb downstream of the bridge tee but upstream of the shunt/transducer T, so bridge recirculation reaches the CDI under normal forward flow while shunt recirculation does not (only via retrograde flow) — noted directly in the package docstring as a requirement for the future CDI mixing model, which should weight Q_patient (native SvO2) against Q_bridge (post-oxygenator saturation) using outputs already available from the wiring stages, with shunt flow excluded under normal operation.
- Added 14 new tests: transfer-efficiency behavior at/below/beyond rated flow, obstruction effects on both O2 and CO2, FdO2-ceiling behavior including the never-actively-desaturates guarantee, CO2 clearance vs. sweep:blood ratio, and bench sanity.
- Added `ecmo_gas_exchange_regression_bench/` (ECMO Oxygenator Gas Exchange NorthStar v1): 2 membrane states x 8 flow steps, frozen and passing.
- Full suite re-verified end to end in batches: 204/204 passing (81 pre-existing + 123 neoecmo), zero regression.
- Next: the CDI mixing sensor itself (using Q_patient/Q_bridge from the wiring stages plus this stage's saturation outputs), and confirming actual sweep-gas practice (pure O2 vs. FdO2-titrated blend) to firm up the fdo2 default.



- Added `solve_bridge_clamp_position_for_target_flow()`: given a target bridge flow, solves for the clamp_position that produces it (root-find over the whole composed circuit, since opening the bridge changes total flow and shifts the shunt/patient split too — not a simple single-branch inversion).
- Motivation: clamp_position is not a value known or relied upon in real practice — clinicians titrate the bridge by watching the resulting flow and adjusting until they hit a target, the same way RPM (not flow) is the pump control while flow is what's watched. This function lets a future interface be built around "titrate to a target flow" rather than around clamp percentage, matching how bridge management actually works clinically.
- Caught and fixed a real bug introduced while adding this function: the edit that inserted the new function accidentally deleted `solve_main_circuit_full_operating_point`'s closing `return` statement, causing it to silently return `None`. Caught immediately by rerunning the Wiring Stage 4 test suite (which failed loudly with an AttributeError) before this ever reached a released state; restored the return statement and reconfirmed the existing NorthStar snapshot matches exactly (proving the fix didn't change any prior behavior).
- Added 6 new tests: zero/negative target handling, round-trip verification that the solved clamp position actually reproduces the target flow, monotonicity (higher target needs more opening), patient-flow reduction as bridge opens for a target, and a clear error for physically unachievable targets.
- Full suite re-verified end to end in batches: 190/190 passing (81 pre-existing + 109 neoecmo), zero regression.



- Added `patient_path.py`: composes real return tubing (grounded Poiseuille) + real return/drain cannulas (empirical, quadratic) + a much narrower "vasculature-only" placeholder (0.3574 mmHg/(mL/min), back-solved from the same real cross-check numbers, standing in only for patient vascular resistance since patient physiology is out of scope for this package by design). Includes an inverse solver since the cannula quadratic terms make this path nonlinear in flow, unlike the flat linear placeholder used in Wiring Stages 2-3.
- Added `main_circuit_full.py`: the complete standalone circuit — pump -> oxygenator -> [fixed shunt || bridge || real patient path] -> back to pump inlet. This is the final circuit-only wiring stage; real patient physiology (neocirculation/neopatient) is a separate future integration, not part of this package.
- **Validated against real clinical numbers with real cannula physics** (not a value tuned to force the match): at RPM=3000, bridge closed, solves to 630.4 mL/min total / 254.0 shunt / 376.4 patient — within 10% of the reported ~600/240/360 example.
- **New emergent behavior discovered, not calibrated in**: shunt fraction is no longer flat across RPM the way it was in Wiring Stages 2-3 (which used a flat linear placeholder) — it now rises from 37.2% at 2000 RPM to 43.1% at 4000 RPM, because the cannula terms are quadratic (resistance rises with flow) while the shunt stays purely linear (laminar tubing), so the patient path becomes proportionally more restrictive at higher flows.
- Confirmed the bridge-crack finding from Wiring Stage 3 carries over with the real patient path in place (a 10% crack still diverts the majority of flow through the bridge).
- Added 12 new tests: patient-path forward/inverse consistency, full-circuit flow conservation and pressure consistency, the real-numbers cross-validation (now within 10% using real cannula physics), the new shunt-fraction-rises-with-RPM behavior, bridge carryover checks, and the degenerate RPM=0 case.
- Added `ecmo_main_circuit_full_regression_bench/` (ECMO Main Circuit Full NorthStar v1): RPM sweep at bridge closed (primary cross-check case) plus a clamp-position sweep at fixed RPM, frozen and passing.
- Full suite re-verified end to end in batches: 184/184 passing (81 pre-existing + 103 neoecmo), zero regression.
- **This completes the ECMO circuit hydraulics build.** All five hydraulic components (pump, oxygenator, fixed shunt, bridge, cannulas) exist standalone, tested, and frozen; all four wiring stages compose them into one working, cross-validated circuit. Not yet built: sensors (flow probes, pressure channels, CDI), gas exchange, heat exchanger, cross-branch stagnation/risk tracking, and — as a separate future effort outside this package — coupling to real patient physiology (neocirculation/neopatient) to replace the narrow vasculature placeholder.



- Added `main_circuit_with_shunt_and_bridge.py`: the bridge wired in as a second parallel branch alongside the fixed shunt, at the same post-oxygenator junction. Bridge defaults closed (clamp_position=0.0) per its clinical default. Real cannulas/patient physiology still not wired in — patient-path term remains the Stage 2 placeholder.
- **Critical regression check passed**: with the bridge closed, results are numerically identical to Wiring Stage 2 (verified across RPM 2000-4000, rel tolerance 1e-6) — adding a branch that defaults closed changed nothing until deliberately opened, confirming the wiring is correct.
- Finding worth the clinical author's own confirmation: even a modest partial bridge opening (clamp_position=0.1) diverts ~84% of total flow through the bridge at RPM=3000 with the current placeholder patient-path resistance, because the bridge is a short, wide, low-resistance direct connection versus routing through the full patient vascular bed. Directionally consistent with real clinical caution around bridge management (why it's normally kept fully clamped), but the specific magnitude hasn't been validated against real weaning-trial experience the way the shunt fraction was — flagged as provisional in the regression bench README, not asserted as correct.
- Added 8 new tests: the bridge-closed-equals-Stage-2 regression check (the most important test in this stage), zero bridge flow when closed, three-way flow conservation, monotonic bridge-fraction increase with clamp opening, patient-fraction reduction as bridge opens, fully-open-bridge dominance, and the degenerate RPM=0 case.
- Added `ecmo_main_circuit_with_shunt_and_bridge_regression_bench/` (ECMO Main Circuit + Shunt + Bridge NorthStar v1): RPM sweep at bridge closed (regression case) plus a clamp-position sweep at fixed RPM (weaning-trial behavior case), frozen and passing.
- Full suite re-verified end to end in batches: 172/172 passing (81 pre-existing + 91 neoecmo), zero regression.
- Next wiring stage: close the loop with both real cannulas (return 8Fr, drain 10Fr) replacing the placeholder patient-path resistance — the point this stops being partly self-validating and starts being a genuinely independent check.



- Added `main_circuit_with_shunt.py`: the fixed shunt wired in as a parallel branch off the Stage 1 backbone (pump -> oxygenator -> [shunt parallel with a placeholder patient-path resistance] -> back to pump inlet). No bridge branch or real cannulas/patient physiology yet.
- The placeholder patient-path resistance (0.4889 mmHg/(mL/min)) is not a guess — it's the value implied by the clinical author's own real cross-check numbers from this session (bridge closed, ~600 mL/min total flow split ~240 shunt/~360 patient), explicitly flagged for replacement once cannulas are wired into this stage.
- **Validated against real clinical numbers end-to-end for the first time**: at RPM=3000, the solved circuit produces 633 mL/min total flow split into 253/380 shunt/patient, a 40.0% shunt fraction — matching the clinical author's reported 35-40% range almost exactly, now produced by the composed pump+oxygenator+shunt system rather than a hand back-solve.
- Confirmed shunt fraction stays constant (~40.0%) across RPM 2000-4000, as expected since both parallel branches are linear resistances at this stage (shunt quadratic term is 0, patient-path placeholder is linear) — flow ratio between two linear resistances in parallel doesn't depend on total flow.
- Confirmed shunt clot fraction correctly shifts the split toward the patient side (more shunt resistance -> proportionally less shunt flow).
- Added 7 new tests: flow conservation (shunt + patient = total), pressure-node consistency, the real-number cross-validation, RPM-independence of the split ratio, clot-fraction effect on the split, and RPM/flow monotonicity.
- Added `ecmo_main_circuit_with_shunt_regression_bench/` (ECMO Main Circuit + Shunt NorthStar v1): 2 shunt clot states x 7 RPM steps (including the RPM=0 degenerate case), frozen and passing.
- Full suite re-verified end to end in batches: 164/164 passing (81 pre-existing + 83 neoecmo), zero regression.
- Next wiring stage: add the bridge as a second parallel branch (bridge closed by default, so this should reproduce the same shunt-fraction behavior until deliberately opened for a weaning-trial test).



- Added `main_circuit_series.py`: the first wiring stage, composing the standalone pump and oxygenator modules into one solvable circuit (pump -> oxygenator -> return, using the grounded pre-pump/return tubing resistances). No fixed shunt or bridge branch yet — those are separate later wiring stages, added and tested one at a time per the agreed review-then-wire plan.
- Flow is bounded non-negative in this stage (unlike the standalone branch benches, which allowed signed/reversed flow) since the oxygenator is a one-way device in real use; reversed-flow validity is deliberately left for a later check rather than solved for here.
- Added 8 new tests: internal pressure-node consistency (P2-P1 = pump head, P2-P3 = oxygenator delta_p), oxygenator-in-series reduces flow vs. pump-alone, oxygenator obstruction reduces series flow at fixed RPM, RPM/flow monotonicity, degenerate zero-RPM case, and default-resistance grounding.
- Added `ecmo_main_circuit_series_regression_bench/` (ECMO Main Circuit Series NorthStar v1): 2 oxygenator states x 7 RPM steps, frozen and passing.
- Sanity-checked output: at these RPMs, flow is 800-1500 mL/min and pre-pump pressure (P1) is only mildly negative (-1 to -3 mmHg) — both expected artifacts of cannula resistance not being wired in yet, not bugs. Real clinical drainage pressures (-20 to -80 mmHg) and neonatal target flows (~600 mL/min) should emerge once cannulas are added in a later wiring stage.
- Full suite re-verified end to end in batches: 157/157 passing (81 pre-existing + 76 neoecmo), zero regression.
- Next wiring stage: add the fixed shunt as a parallel branch off this backbone — the first point a real shunt/patient flow split becomes computable end-to-end.



- Added cannula hydraulics to `neoecmo`: return (8Fr) and drain (10Fr), matching the clinical author's actual cannula sizing. Deliberately modeled as an EMPIRICAL quadratic (orifice-type) pressure-flow relationship, not Hagen-Poiseuille like the tubing — cannula side holes and tip geometry make straight-pipe laminar flow physically inapplicable, consistent with how the field actually calibrates cannula hydraulics (manufacturer nomograms, not pipe-flow calculation).
- Return (8Fr) default grounded in a published Medtronic DLP pediatric arterial cannula bench measurement (~600 mL/min at 100 mmHg). Drain (10Fr) default reuses the same-size-class arterial bench figure (~1100 mL/min at 100 mmHg) as an explicitly-flagged placeholder — likely an overestimate, since multi-side-hole venous cannulae generally have lower resistance than a single-end-hole arterial cannula of the same French size. Flagged for replacement once real drain-cannula data is available.
- Added `resistance_coefficient_from_datapoint()` utility so any future real manufacturer/bench data point can recalibrate either default directly.
- Cross-validated against the clinical author's real numbers (600 mL/min total flow, bridge closed, 240 mL/min shunt / 360 mL/min patient): the two cannulas together account for ~26.5% of the previously-implied total patient-path resistance (~0.489 mmHg/(mL/min)), with the remainder attributable to patient vasculature — a clinically sensible split (systemic vascular resistance typically dominates over cannula resistance in the patient path).
- Added `ecmo_cannula_regression_bench/` (ECMO Cannula NorthStar v1): both cannula sizes swept across 10 flow steps, frozen and passing.
- Added 10 new tests, including round-trip validation that both defaults reproduce their literature source data points.
- Full suite re-verified end to end in batches: 149/149 passing (81 pre-existing + 68 neoecmo), zero regression.
- Not yet built: sensors, gas exchange, heat exchanger, cross-branch stagnation/risk tracking, or the circuit-level flow-distribution coordinator. Next stage: the coordinator itself — solving main circuit + fixed shunt + bridge + both cannulas as one connected system, which is the first point real total/shunt/patient flow splits (like the 600/240/360 example) can be produced end to end rather than checked by hand.



- Added `neoecmo.tubing_geometry`: Hagen-Poiseuille linear resistance calculation from measured tube diameter and length, plus a Reynolds-number check confirming the laminar-flow assumption across realistic neonatal ECMO flow ranges.
- Grounded in real measured geometry supplied directly by the clinical author (2026-07-25): 3/8" ID for the main circuit and bridge tubing, 1/16" ID for the fixed-shunt tubing (without the scuffing filter installed); main circuit 8 ft cannula-to-cannula (3 ft pre-pump, 2 ft pump-to-oxygenator, 3 ft return); shunt and bridge each ~1 ft.
- Recalibrated `fixed_shunt.py` and `bridge.py` tubing resistance defaults from guessed placeholders to Poiseuille-derived values, and set their quadratic (turbulent) terms to 0.0 since Reynolds analysis confirms laminar flow throughout — the linear term is now the physically correct model, not an approximation.
- Result: the fixed shunt's resistance is ~1296x the main tubing's per foot (6x smaller bore -> 6^4), confirming its narrow bore is an intentional restrictive design choice, not an arbitrary small number. Old placeholder shunt-bench flows (thousands of mL/min) dropped to a clinically plausible tens-to-hundreds range. The bridge, being wide-bore, now shows even less resistance than previously modeled — expected, since an open bridge is meant to offer minimal restriction.
- Grounded `pump_bench.py`'s default inlet resistance in the measured pre-pump segment; outlet resistance remains a documented placeholder since the real downstream path (oxygenator + return tubing/cannula) isn't composed into that standalone bench yet.
- Regenerated and re-accepted the fixed-shunt and bridge NorthStar snapshots to reflect the new grounded defaults (pump NorthStar unaffected — its cases pass resistance values explicitly rather than relying on defaults).
- Added 11 new tests for tubing_geometry.py: physical scaling laws (resistance ∝ length, ∝ 1/diameter^4, ∝ viscosity) rather than just fixed-number checks, plus laminar-flow confirmation for all three measured segments.
- Full suite re-verified end to end in batches: 139/139 passing (81 pre-existing + 58 neoecmo), zero regression.
- Note for the next stage (cannulas): cannula ID/length will need the same treatment once measured — expect cannula resistance to dominate over tubing resistance by a wide margin given typical cannula lumens are much narrower than 3/8" circuit tubing.



- Added bridge branch hydraulics to `neoecmo`: clamp-position model with a hard zero-flow cutoff when fully closed (not an asymptote of rising resistance — a real clamp is a physical cutoff), and the same signed-quadratic resistance solver as the shunt for any nonzero opening, so weaning-trial partial openings and reversed-gradient flow both behave correctly.
- Deliberately scoped hydraulics-only: stagnation-clock, clot-risk-from-dwell-time, and flush-validity logic from the handoff are deferred to a later cross-branch risk-tracking stage rather than blended into this one, keeping this stage's testable surface small.
- Added `ecmo_bridge_regression_bench/` (ECMO Bridge NorthStar v1): clamp-position sweep plus four closed-clamp pressure-gradient cases (including a reversed gradient) confirming the closed state stays a hard zero, frozen and passing.
- Added 10 new tests: closed-clamp hard-zero behavior at multiple gradients, fully-open forward/reversed flow, monotonic partial-opening behavior, clot-fraction resistance, and bench sanity.
- Full suite re-verified end to end in batches: 128/128 passing (81 pre-existing + 12 pump + 11 oxygenator + 14 fixed shunt + 10 bridge), zero regression.
- Not yet built: cannula resistances, sensors, gas exchange, heat exchanger, cross-branch stagnation/risk tracking, or the circuit-level flow-distribution coordinator. Next stage: drain and return cannula resistances (standalone against synthetic venous/arterial reservoirs), the last branch before the coordinator can be built.



- Added fixed-shunt branch hydraulics to `neoecmo`: always-open, non-learner-adjustable parallel path with a signed quadratic resistance solver (flow can reverse direction if the pressure gradient reverses — no valve, no error). Optional scuffing filter adds substantial resistance whenever installed, independent of whether it is actively removing fluid (installed/active are separate axes, exactly per handoff section 19).
- Added filtrate-removal tracking (`ScuffingFiltrationState`) as a simple rate-based cumulative volume — requires both installed AND active; does not model solute clearance (deliberately out of scope for this stage).
- Added `ecmo_fixed_shunt_regression_bench/` (ECMO Fixed Shunt NorthStar v1): 3 filter-state cases x 6 downstream-pressure steps, frozen and passing, confirming filter activity never changes frozen hydraulic behavior.
- Added 14 new tests: basic hydraulics, reversed-flow handling, filter-installed-vs-active independence, clot-fraction resistance, and filtrate-accumulation guard conditions.
- Full suite re-verified end to end in batches: 118/118 passing (81 pre-existing + 12 pump + 11 oxygenator + 14 fixed shunt), zero regression.
- Not yet built: bridge, cannula resistances, sensors, gas exchange, heat exchanger, or the circuit-level flow-distribution coordinator that combines main/shunt/bridge into one solved system — that coordinator is deliberately deferred until the bridge and cannula branches also exist standalone, per the mirrored heart/lung/kidney build order.



- Added oxygenator hydraulics-only model to `neoecmo`: mechanical resistance and flow-dependent pressure drop (P2-P3), with obstruction/clot state raising resistance via a lumped 1/(1-obstruction)^2 model. No gas exchange, membrane O2/CO2 transfer, or heat exchanger yet — hydraulics only, mirroring the neolung mechanics-before-gas-exchange build order.
- Added low-flow exposure tracking (time below minimum recommended blood flow) as a non-resetting cumulative clock — exposure only, not a risk/complication engine (that remains a later stage).
- Added `ecmo_oxygenator_regression_bench/` (ECMO Oxygenator NorthStar v1): 3 obstruction-state cases x 8 flow steps, frozen and passing.
- Added 11 new tests covering baseline/flow-dependent/obstruction-dependent ΔP and low-flow exposure behavior.
- Full suite re-verified end to end in batches: 104/104 passing (81 pre-existing + 12 pump + 11 oxygenator), zero regression.
- Not yet built: fixed shunt, bridge, cannula resistances, flow/pressure sensors, gas exchange, heat exchanger, or coupling to native patient physiology. Next stage: fixed-shunt branch (parallel resistance path with its own boundary-condition bench), then bridge, then cannulas, then the circuit-level flow-distribution coordinator.



- Added new standalone `neoecmo` package: ECMO circuit hydraulics engine, deliberately independent of `neocirculation`/`neolung`/`neokidney`/`neocoupling`/`neopatient` (enforced by boundary tests in both directions).
- Stage 1 only: pump-head hydraulic bench for the uncoated LivaNova/Sorin revOlution centrifugal pump (catalog 050300000). RPM never maps directly to flow — `solve_pump_operating_point` intersects a provisional, explicitly-labeled-replaceable H-Q curve with simple inlet/outlet pressure reservoirs and tubing resistances to solve actual flow.
- Added `ecmo_pump_regression_bench/` (ECMO Pump NorthStar v1): 4 boundary-condition cases x 7 RPM steps, frozen and passing.
- Added 12 tests covering all 10 stage-1 acceptance criteria from the ECMO circuit handoff (2026-07-24) plus explicit no-cross-import boundary tests.
- Full suite re-verified end to end: 93/93 passing (81 pre-existing + 12 new), zero regression.
- Not yet built: oxygenator hydraulics, fixed shunt, bridge, cannula resistances, flow/pressure sensors, stagnation clocks, gas exchange, or any coupling to the native patient physiology modules. These follow in later stages per the mirrored heart/lung/kidney build order, one component at a time.



- Added removable `neocoupling` coordinator; heart and lung remain independent modules.
- Added minimal cardiopulmonary signal exchange only: pulmonary flow, mixed-venous oxygen boundary, arterial oxygenation/oxygen delivery, pleural pressure, lung-volume PVR effect, and hypoxic PVR response.
- Added modest airway-pressure-to-thorax transmission for positive-pressure/PEEP teaching behavior without a full chest-wall model.
- Added Cardiopulmonary Coupling NorthStar v1 with neutral, hypoxia, low-compliance, and PEEP challenges.
- Preserved all pre-existing standalone NorthStar baselines; no heart or lung core imports the coupling layer.
- Fidelity boundary remains educational and reduced-order rather than physiologic-digital-twin accuracy.

# v0.8.0

- Added standalone reduced-order neonatal gas exchange with no cardiovascular dependency.
- Added alveolar ventilation, O2 uptake/CO2 elimination relationships, FiO2 response, shunt, diffusion impairment, dead-space, and simplified high-/low-VQ mismatch behavior.
- Added incoming mixed-venous gas values as standalone boundary placeholders for later coupling.
- Added standalone gas-exchange bench and external ventilator + gas-exchange bench.
- Added frozen Gas Exchange NorthStar v1 regression suite.
- Preserved cardiovascular, standalone lung-mechanics, and ventilator NorthStar snapshots with zero drift.

# Changelog

## 0.3.0

- Added documented baseline parameter registry.
- Added fresh-model engineering modifiers for volume, SVR, PVR, arterial compliance, HR, LV/RV contractility, and external pressure.
- Added controlled perturbation suite and JSON-style report runner.
- Added pressure/chamber/volume drift analysis and a ten-minute accelerated runner.
- Added tests proving the engineering layer does not mutate the normal baseline.
- Disclosed that reduced contractility currently produces an underpowered failure response and is not yet clinically validated.

## 0.4.0
- Added explicit ventricular source resistance separate from valve resistance.
- Added nonlinear passive ventricular stiffness to prevent unrealistic preload compensation during severe pump failure.
- Added isolated LV/RV failure validation profiles.
- Added recovery-sequence validation without hidden state resets.
- Added removable pressure-volume loop engineering diagnostics.

## v0.4.1
- Added an isolated right-atrial pump-drainage bench harness.
- Bench range: 0–200 mL/kg/min in configurable steps.
- No arterial return, oxygenator, or ECMO afterload effects are included in this bench; it isolates acute preload extraction only.
- Added measurements for native RV output, native LV output, RA/LA/PA/aortic pressures, and removed patient volume.
- Confirmed immediate RV output reduction with delayed LV reduction due to pulmonary vascular volume buffering.

## v0.4.2
- Added an isolated closed-loop VA-ECMO hydraulic bench (right-atrial drainage to aortic-root return).
- Matched drainage and return conserve patient blood volume exactly.
- Tracks native RV output, native LV output, pump contribution, total aortic inflow, aortic-valve opening fraction, arterial pressure/pulse pressure, RA/LA/PA pressures, and chamber volumes.
- Keeps intrinsic contractility, vascular compliance, SVR, and PVR unchanged during the bench so changes arise only from preload diversion and arterial return loading.
- Added automated checks for blood-volume conservation and progressive native-heart unloading.

## v0.4.3

- Added a completely external `bench_fixtures` package; the `neocirculation` patient engine does not import it.
- Added manufacturer-sourced Medtronic Bio-Medicus Life Support Mini 9, 11, 13, and 15 Fr drainage/return catheter records.
- Stored exact manufacturer anchor values at -40 mmHg drainage and +100 mmHg return pressure loss.
- Added a two-point power-law interpolation model solely for bench testing between/around those published anchors.
- Added an external cannula hydraulic overlay that consumes circulation bench outputs without modifying patient physiology.
- Added provenance, model numbers, dimensions, source URL, test-medium caveat, and extrapolation flags.

## v0.5.0
- Added frozen NorthStar regression bench (`neonatal-circulation-northstar-v1`).
- Added accepted versioned reference snapshot and explicit comparison tolerances.
- Added external synthetic centrifugal pump fixture for deterministic RPM/head/flow regression testing.
- Added fixed VA flow, cannula-size, and RPM test matrices.
- Added boundary test preventing patient physiology from importing pump/cannula/regression fixtures.
- Added change-control rule: reference snapshots are versioned, never silently replaced.

## v0.6.0 — standalone neonatal lung mechanics foundation
- Added independent `neolung` package with no import of `neocirculation`.
- Added spontaneous-breathing single-compartment mechanics: compliance, airway resistance, pleural pressure, alveolar pressure, flow, FRC, and lung volume.
- Added explicit read-only future cardiopulmonary boundary dataclasses.
- Added standalone perturbation bench for compliance, airway resistance, respiratory rate, effort, and PEEP.
- Gas exchange and cardiovascular coupling remain intentionally disabled.

## v0.7.0
- Added removable external pressure-control ventilator fixture.
- Added generic airway-opening pressure input to the standalone lung API; no ventilator ownership in `neolung`.
- Added Ventilator NorthStar v1 frozen regression matrix.
- Added pressure-control challenge cases for PIP/PEEP/rate/Ti, low compliance, and high airway resistance.
- Added regression tests enforcing module boundary and mechanical response direction.

## v0.10.0
- Added simultaneous heart-lung equipment bench with external pressure-control ventilation and VA support.
- Added frozen Combined Equipment NorthStar v1, intended to be rerun unchanged after every future system integration.
- Preserved external device ownership boundaries.
- Added a bench-only oxygenation mixing proxy for native lung output plus idealized oxygenator return.

## v0.12.0
- Restored full v0.10 heart/lung/equipment codebase after v0.11 packaging omission.
- Added standalone neokidney module.
- Added live CV->kidney and CV+lung->kidney coupling.
- Added staged kidney integration regression bench.
- Renal vasoactive feedback remains deliberately weighted/reduced-order because systemic beds are still lumped.

## v0.13.0
- Added generic renal therapy controls: fluids, fluid removal, diuretic multiplier, renal vaso-tone, renal function fraction.
- Added simple fluid-balance accumulator and deliberately limited intravascular-fraction estimate.
- Added Renal Therapy NorthStar v1 and focused therapy tests.
- No drug-specific PK/PD or nephron-level chemistry added.

## v0.14.0
- Added live fluid-balance feedback into cardiovascular blood-volume state through venous reservoirs.
- Added separate CV-only and CV+lung fluid-feedback benches and NorthStar manifest.

## v0.15.0
- Added explicit renal volume-depletion/perfusion guardrails.
- Progressive hypovolemia now suppresses urine toward oliguria/anuria.
- Diuretic multipliers cannot override severe volume depletion or critical renal hypoperfusion.
- Added depletion/recovery benches and Renal Volume Guardrail NorthStar v1.
\n## v0.16.0\n- Added separate unified three-system patient shell (`neopatient`).\n- Cardiovascular, lung/gas exchange, and kidney/fluid systems remain independently runnable.\n- Added airway, vascular support, and renal therapy equipment attachment ports.\n- Vascular/ECMO port is contract-only pending validated equipment adapter.\n
## v0.17.0
- Corrected PEEP/PaCO2 coupling artifact.
- Static PEEP no longer counts as large dynamic tidal ventilation.
- CO2 clearance now depends on alveolar ventilation plus pulmonary perfusion efficiency.
- PEEP has only a modest capped recruitment effect on effective ventilation.

## v0.18.0
- Corrected development order for PEEP/CO2 behavior.
- Moved PEEP/CO2 clearance semantics into standalone `neolung` gas-exchange ownership.
- Added standalone PEEP/perfusion gas bench and Lung PEEP-CO2 NorthStar v1.
- Reintegrated the validated standalone lung behavior into cardiopulmonary coupling.
- Coupling no longer owns the lung correction logic.

## GUI learner workspace — 2026-07-28

- Added `neogui.EcmoWorkspace`, a functional Tkinter ECMO pump/circuit console.
- Added a tab-ready learner shell with reserved pages for patient monitoring, ventilator controls, diagnostics, interventions, and scenario history.
- Connected RPM, pump start/stop, bridge clamp opening, shunt configuration, scuffing state, FdO2, and sweep controls directly to the verified `neoecmo.run_ecmo_console()` solver.
- Added live solved displays for total, patient, shunt, and bridge flows; P1/P2/P3; pump head; oxygenator delta pressure; gas exchange; and CDI values.
- Added a headless GUI adapter test suite so solver/control behavior can be regression-tested without opening a window.
- Added `run_ecmo_workspace.bat` and `examples/run_ecmo_workspace.py` launchers.

## GUI v0.2 — Console-style ECMO workstation (2026-07-28)

- Reworked the ECMO tab from a generic control dashboard into a console-inspired device layout.
- Added explicit sweep controls in L/min with ±0.05 and ±0.10 steps plus direct numeric entry (0.00–10.00 L/min).
- Added explicit FdO2 controls with ±5% and ±10% steps plus direct numeric entry (21–100%).
- Added dominant total-flow and actual-RPM readouts, P1/P2/P3 and oxygenator delta-pressure tiles.
- Added patient, shunt, and bridge branch-flow readouts.
- Added a simplified circuit map, gas/CDI panel, and circuit-distribution panel.
- Added persistent action/result feedback describing each learner control change and its immediate modeled consequence.
- Added clearly marked nonfunctional placeholders for alarms, clamps, probe position, and bubble reset; these do not silently pretend to work.
- Retained the tab-ready learner workspace and the July 27 canonical model base.

## GUI v0.3 — compact console layout (2026-07-28)

- Replaced the oversized three-pane ECMO page with a compact device-style layout.
- Added a narrow left navigation rail for the tabbed learner workspace.
- Added a compact top telemetry ribbon.
- Added a large circular total-flow/RPM display with commanded-RPM marker and P1/P2 readouts.
- Added an original neonatal patient/circuit visualization with drainage, return, bridge, shunt, pump, and oxygenator paths.
- Moved RPM, sweep, FdO2, bridge, and shunt controls into a compact bottom control strip.
- Preserved direct solver coupling and existing learner-action feedback.

## 2026-07-28 — ECMO–Patient Coupling Stage 1
- Added `neoecmocoupling`, a separate coupling-boundary package.
- Added explicit patient-to-ECMO and ECMO-to-patient contracts.
- Added branch-flow conservation and input-range validation.
- Added adapters from existing unified-patient snapshots and ECMO console states.
- No patient or circuit physiology was changed in this stage.

## 2026-07-28 — ECMO coupling Stage 2B
- Added content-based mixing of native arterial and ECMO-return blood.
- Unified patient now consumes ECMO return flow, PO2, and PCO2 through `VascularSupportPort`.
- Added patient arterial oxygen content, PO2, saturation, PCO2, oxygen delivery, and ECMO flow-fraction calculations in the coupling layer.
- Added regression tests protecting the clinical relationship between ECMO blood flow, oxygenation, sweep, and CO2 removal.

## v0.11 coupling Stage 3 — 2026-07-28
- Added live MAP/CVP hydraulic feedback from patient to ECMO circuit.
- Added `solve_ecmo_against_patient()` coupling entry point.
- Preserved legacy standalone circuit solve when patient boundaries are absent.
- Added hydraulic behavior and conservation tests.
- Moved arterial blood mixing to neutral `neoblood` package to preserve patient/ECMO dependency boundaries.

## Coupling Stage 3B — 2026-07-28
- Added `solve_closed_loop_va_ecmo()` in `neoecmocoupling.closed_loop`.
- Added reduced-order two-way relationship: patient-directed VA flow raises MAP, and MAP feeds back as return afterload.
- Excluded shunt and bridge recirculation from MAP support.
- Added estimated pulse-pressure behavior that may fall as VA support increases.
- Added six regression tests for VA flow/MAP directionality, bridge exclusion, feedback, pump-off baseline, pulse pressure, and conservation.

## v0.14.0 — Coupling Stage 4B
- Added weight-based estimated pre-cannulation blood volume.
- Added compact patient volume ledger for inputs, urine, CKRT removal, blood loss, sampling loss, and third spacing.
- Added effective venous volume as the drainage/chatter-facing volume state.
- Preserved reduced-order, scenario-sensitive modeling rather than introducing a full fluid-compartment engine.

## v0.16 coupling stage 6 — 2026-07-28

- Added dynamic patient–ECMO display response around the Stage-5 coordinator.
- Preserved separate true and displayed states.
- Added configurable flow, pressure, oxygen, and CO2 response timing.
- Added delayed chatter indication and true-state clinical advisories.
- Kept dynamic behavior outside the patient and ECMO core packages.

## v0.17 — GUI coupled-patient integration (2026-07-28)
- Wired the learner workspace to the Stage-6 dynamic patient–ECMO coordinator.
- Added timed GUI refresh and displayed-versus-true state separation.
- Added patient MAP and arterial blood gas telemetry.
- Added live preload/chatter/low-flow advisory presentation.

## 2026-08-10 — v0.17.6 CBC03 oxygenator dysfunction
- Added CBC03 with separate hydraulic-obstruction and membrane-transfer branches.
- Added non-circular regression tests for pressure/flow and gas-transfer directional behavior.
- No physiology source changes required.
- Added append-only clarification that CBC02 conversational prose said ~760 mmHg while the packaged model's pure-O2 post-oxy target is 450 mmHg; CBC02 acceptance behavior was unchanged.
- Capability matrix remains the single living status authority.

## 2026-08-10 — v0.17.6 CBC03 oxygenator dysfunction
- Added CBC03 with separate hydraulic-obstruction and membrane-transfer branches.
- Added non-circular regression tests for pressure/flow and gas-transfer directional behavior.
- No physiology source changes required.
- Added append-only clarification that CBC02 conversational prose said ~760 mmHg while the packaged model's pure-O2 post-oxy target is 450 mmHg; CBC02 acceptance behavior was unchanged.
- Capability matrix remains the single living status authority.

## 2026-08-10 — CBC08 FdO2 oxygen-state coherence
- Added `cbc.ecmo.fdo2-oxygen-fraction-control.v1`.
- Fixed contradictory post-oxygenator O2 outputs by deriving saturation from the same reduced-order outlet pO2 state rather than maintaining a separate FdO2-to-saturation approximation.
- Added the inverse Hill helper `saturation_from_po2_mmhg()` and exported it from `neoecmo`.
- Fixed-sweep FdO2 changes now preserve CO2 clearance and hydraulics while changing the coherent modeled O2 state.
- Coupled-patient FdO2 response remains explicitly blocked pending a real central-venous oxygen state.

## 2026-08-10 — v0.17.13 CBC10 fixed-shunt configuration / hemofilter hydraulics
- Added `cbc.ecmo.fixed-shunt-configuration.v1`.
- Protected OPEN/HEMOFILTER/CKRT shunt hydraulic semantics and the independence of filter presence from `scuffing_active` hydraulic state.
- Added an explicit blocked capability for hemofilter net-fluid removal into the coupled patient; the provisional helper default was not promoted into patient physiology.
- No runtime source changes.

## v0.18.0 — Phase 2a Patient Monitor — 2026-08-10
- Resumed FIX_MAP v4 numbered-roadmap execution after Phase 1; Behavior Contracts remain a parallel discipline.
- Replaced the Patient Monitor reserved shell with a real read-only learner display.
- Added a pure `PatientMonitorReading` projection layer over `WorkspaceSnapshot`.
- Reused existing learner-display dynamics for MAP, SpO2, PaO2, PaCO2, and patient-directed ECMO flow.
- Exposed existing BP, CVP, native cardiac output, urine, fluid balance, and blood-volume state without adding physiology.
- HR, patient temperature, and waveforms remain explicitly unavailable rather than synthesized.

"""
neoecmo — standalone ECMO circuit hydraulics engine.

Deliberately independent of neocirculation, neolung, neokidney, and
neocoupling/neopatient. This package must never import those modules; the
eventual patient-facing coupling boundary lives in a separate coupling layer,
the same way neocoupling sits between neocirculation and neolung without
either owning the other's internals.

Stage 1 (complete): pump-head hydraulic bench. See pump.py and
pump_bench.py, and ecmo_pump_regression_bench/ for the frozen NorthStar
snapshot.

Stage 2 (complete): oxygenator hydraulics only. See oxygenator.py and
oxygenator_bench.py, and ecmo_oxygenator_regression_bench/ for the frozen
NorthStar snapshot.

Stage 3 (complete): fixed shunt branch. See fixed_shunt.py and
fixed_shunt_bench.py, and ecmo_fixed_shunt_regression_bench/ for the
frozen NorthStar snapshot.

Stage 4 (current): bridge branch — the second of the three parallel flow
paths (main/shunt/bridge), hydraulics-only. Closed clamp is a hard zero
flow, not an asymptote; any opening solves the same signed-quadratic
resistance model as the shunt. Stagnation-clock, clot-risk-from-dwell,
and flush-validity logic are deliberately deferred to a later cross-branch
risk-tracking stage. See bridge.py and bridge_bench.py, and
ecmo_bridge_regression_bench/ for the frozen NorthStar snapshot.

Stage 5 (current): cannula hydraulics — drain (10Fr) and return (8Fr),
per your measured French sizes. Deliberately modeled as an EMPIRICAL
quadratic (orifice-type) pressure-flow relationship, not Hagen-Poiseuille
like the tubing — cannula side holes and tip geometry make straight-pipe
laminar flow physically inapplicable, consistent with how the field
actually calibrates cannula hydraulics (manufacturer nomograms). See
cannula.py and cannula_bench.py for defaults, sourcing, and the explicit
caveat that the drain (multi-side-hole, 10Fr) default reuses a
single-end-hole arterial figure as a likely-overestimate placeholder.

Cross-cutting: tubing_geometry.py provides Hagen-Poiseuille resistance
calculations from measured tube diameter/length, used to ground the
fixed-shunt and bridge tubing resistance defaults in real geometry
(measured by the clinical author 2026-07-25) rather than guesses. See
tubing_geometry.py for the measured segment registry and the
Reynolds-number check confirming laminar flow across realistic neonatal
ECMO flow ranges.

Wiring Stage 1 (current): pump + oxygenator composed in series — the
first step of tying the standalone branch modules together into an
actual solvable circuit. No fixed shunt or bridge branch yet; those are
separate later wiring stages, added one at a time and tested before the
next. See main_circuit_series.py.

Wiring Stage 2 (current): fixed shunt added as a parallel branch off the
Stage 1 backbone (pump -> oxygenator -> [shunt parallel with a
placeholder patient-path resistance] -> back to pump inlet). No bridge
branch or real cannulas/patient physiology yet. The placeholder
patient-path resistance is grounded in the clinical author's own real
cross-check numbers (bridge closed, ~40% shunt fraction), not guessed —
see main_circuit_with_shunt.py for sourcing and the explicit note that it
must be replaced once cannulas are wired in. See main_circuit_with_shunt.py.

Wiring Stage 3 (current): bridge added as a second parallel branch
alongside the shunt (bridge clamp_position=0.0/closed by default, so this
must reduce to Stage 2's result until deliberately opened — that
equivalence is this stage's regression check). Real cannulas/patient
physiology still not wired in. See main_circuit_with_shunt_and_bridge.py.

Wiring Stage 4 (current, FINAL circuit-only wiring stage): real cannulas
replace the flat patient-path placeholder used in Stages 2-3. patient_path.py
composes real return tubing + real return/drain cannulas + a much
narrower vasculature-only placeholder (patient vasculature is still out
of scope for this package by design). main_circuit_full.py is the
complete standalone circuit: pump -> oxygenator -> [shunt || bridge ||
real patient path] -> back to pump inlet. This is the last stage before
real patient physiology (neocirculation/neopatient) would be coupled in
separately — this package still never models the patient itself.

Gas exchange (current): oxygenator O2/CO2 transfer, separate from the
hydraulics-only module. min_flow_ml_min is REAL (250 mL/min Eurosets AMG
PMP Infant minimum flow to prevent clot formation, confirmed 2026-07-26,
replacing the earlier hydraulics placeholder too). rated_flow_ml_min and
the transfer-efficiency shape remain PROVISIONAL, grounded in a
comparable device (Quadrox-i Neonatal) pending the AMG PMP Infant's own
specs. See oxygenator_gas_exchange.py and gas_exchange_bench.py.

CDI sensor (current): flow-weighted mixing at the CDI's real confirmed
position on the drain limb — downstream of the bridge tee, upstream of
the shunt/transducer T (confirmed circuit anatomy, chat 2026-07-26:
patient -> 8" -> bridge tee -> 8" -> CDI -> 4" -> venous access pigtail
-> 6" -> manifold -> 6" -> shunt/transducer T -> 4" -> pump). Blends
native venous blood with bridge recirculation only; shunt flow is
deliberately never a parameter anywhere in this module, since shunt
recirculation cannot reach this sensor under normal forward flow. See
cdi_sensor.py.

ECMO console (current): the single consolidated control surface for
every learner-adjustable input across the whole circuit (RPM, bridge —
titrated by target flow, the confirmed realistic control action — shunt
line configuration including hemofilter/CKRT, sweep gas FdO2 and flow),
returning the complete solved monitor/CDI state in one call instead of
several separate ones. Device specs and pathology/complication state
remain separate pass-through parameters, not learner controls. See
ecmo_console.py.
"""

from .pump import DEFAULT_REVOLUTION_CURVE, PumpHeadCurveParameters, pump_head_mmhg
from .pump_bench import (
    PumpBenchPoint,
    format_pump_head_bench_report,
    run_pump_head_bench,
    solve_pump_operating_point,
)
from .oxygenator import (
    OxygenatorHydraulicParameters,
    OxygenatorLowFlowExposureState,
    oxygenator_delta_p_mmhg,
    step_low_flow_exposure,
)
from .oxygenator_bench import (
    OxygenatorBenchPoint,
    format_oxygenator_hydraulic_bench_report,
    run_oxygenator_hydraulic_bench,
)
from .oxygenator_gas_exchange import (
    MAX_FDO2,
    MIN_FDO2,
    FDO2_BLENDER_STEP,
    OxygenatorGasExchangeParameters,
    co2_clearance_efficiency,
    outlet_o2_saturation,
    outlet_po2_mmhg,
    po2_from_saturation_mmhg,
    saturation_from_po2_mmhg,
    outlet_paco2_mmhg,
    oxygenator_transfer_efficiency,
    round_fdo2_to_blender_step,
)
from .gas_exchange_bench import (
    GasExchangeBenchPoint,
    format_gas_exchange_bench_report,
    run_gas_exchange_bench,
)
from .post_oxygenator_cdi import (
    PostOxygenatorBloodState,
    PostOxyCdiReading,
    PostOxyCdiSensorState,
    measure_post_oxygenator_blood,
)
from .cdi_sensor import (
    CDIReading,
    cdi_mixed_paco2_mmhg,
    cdi_mixed_saturation,
    cdi_reading_from_circuit_point,
    recirculation_fraction,
)
from .fixed_shunt import (
    FixedShuntParameters,
    ScuffingFiltrationState,
    ShuntLineConfiguration,
    fixed_shunt_flow_ml_min,
    step_filtrate_removal,
)
from .fixed_shunt_bench import (
    FixedShuntBenchPoint,
    format_fixed_shunt_bench_report,
    run_fixed_shunt_bench,
)
from .bridge import BridgeParameters, bridge_flow_ml_min
from .bridge_bench import (
    BridgeBenchPoint,
    format_bridge_bench_report,
    run_bridge_clamp_sweep_bench,
)
from .tubing_geometry import (
    MEASURED_SEGMENTS,
    MeasuredTubingSegment,
    poiseuille_linear_resistance_mmhg_per_ml_min,
    resistance_for_segment,
    reynolds_number,
)
from .cannula import (
    DRAIN_10FR,
    RETURN_8FR,
    CannulaHydraulicParameters,
    cannula_delta_p_mmhg,
    resistance_coefficient_from_datapoint,
)
from .cannula_bench import (
    CannulaBenchPoint,
    format_cannula_bench_report,
    run_cannula_hydraulic_bench,
)
from .main_circuit_series import (
    MainCircuitSeriesPoint,
    solve_main_circuit_series_operating_point,
)
from .main_circuit_with_shunt import (
    PATIENT_PATH_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    MainCircuitWithShuntPoint,
    solve_main_circuit_with_shunt_operating_point,
)
from .main_circuit_with_shunt_and_bridge import (
    MainCircuitWithShuntAndBridgePoint,
    solve_main_circuit_with_shunt_and_bridge_operating_point,
)
from .patient_path import (
    PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    patient_path_delta_p_mmhg,
    solve_patient_path_flow_ml_min,
)
from .main_circuit_full import (
    MainCircuitFullPoint,
    solve_bridge_clamp_position_for_target_flow,
    solve_main_circuit_full_operating_point,
)
from .ecmo_console import (
    EcmoConsoleControls,
    EcmoConsoleState,
    run_ecmo_console,
)

__all__ = [
    "DEFAULT_REVOLUTION_CURVE",
    "PumpHeadCurveParameters",
    "pump_head_mmhg",
    "PumpBenchPoint",
    "format_pump_head_bench_report",
    "run_pump_head_bench",
    "solve_pump_operating_point",
    "OxygenatorHydraulicParameters",
    "OxygenatorLowFlowExposureState",
    "oxygenator_delta_p_mmhg",
    "step_low_flow_exposure",
    "OxygenatorBenchPoint",
    "format_oxygenator_hydraulic_bench_report",
    "run_oxygenator_hydraulic_bench",
    "OxygenatorGasExchangeParameters",
    "co2_clearance_efficiency",
    "outlet_o2_saturation",
    "outlet_po2_mmhg",
    "po2_from_saturation_mmhg",
    "saturation_from_po2_mmhg",
    "outlet_paco2_mmhg",
    "oxygenator_transfer_efficiency",
    "MIN_FDO2",
    "MAX_FDO2",
    "FDO2_BLENDER_STEP",
    "round_fdo2_to_blender_step",
    "GasExchangeBenchPoint",
    "format_gas_exchange_bench_report",
    "run_gas_exchange_bench",
    "PostOxygenatorBloodState",
    "PostOxyCdiReading",
    "PostOxyCdiSensorState",
    "measure_post_oxygenator_blood",
    "CDIReading",
    "cdi_mixed_saturation",
    "cdi_mixed_paco2_mmhg",
    "recirculation_fraction",
    "cdi_reading_from_circuit_point",
    "FixedShuntParameters",
    "ScuffingFiltrationState",
    "ShuntLineConfiguration",
    "fixed_shunt_flow_ml_min",
    "step_filtrate_removal",
    "FixedShuntBenchPoint",
    "format_fixed_shunt_bench_report",
    "run_fixed_shunt_bench",
    "BridgeParameters",
    "bridge_flow_ml_min",
    "BridgeBenchPoint",
    "format_bridge_bench_report",
    "run_bridge_clamp_sweep_bench",
    "MEASURED_SEGMENTS",
    "MeasuredTubingSegment",
    "poiseuille_linear_resistance_mmhg_per_ml_min",
    "resistance_for_segment",
    "reynolds_number",
    "DRAIN_10FR",
    "RETURN_8FR",
    "CannulaHydraulicParameters",
    "cannula_delta_p_mmhg",
    "resistance_coefficient_from_datapoint",
    "CannulaBenchPoint",
    "format_cannula_bench_report",
    "run_cannula_hydraulic_bench",
    "MainCircuitSeriesPoint",
    "solve_main_circuit_series_operating_point",
    "PATIENT_PATH_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN",
    "MainCircuitWithShuntPoint",
    "solve_main_circuit_with_shunt_operating_point",
    "MainCircuitWithShuntAndBridgePoint",
    "solve_main_circuit_with_shunt_and_bridge_operating_point",
    "PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN",
    "patient_path_delta_p_mmhg",
    "solve_patient_path_flow_ml_min",
    "MainCircuitFullPoint",
    "solve_main_circuit_full_operating_point",
    "solve_bridge_clamp_position_for_target_flow",
    "EcmoConsoleControls",
    "EcmoConsoleState",
    "run_ecmo_console",
]

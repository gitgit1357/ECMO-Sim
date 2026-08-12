from __future__ import annotations

from dataclasses import dataclass

from scipy.optimize import brentq

from .bridge import BridgeParameters, bridge_flow_ml_min
from .cannula import DRAIN_10FR, RETURN_8FR, CannulaHydraulicParameters
from .fixed_shunt import FixedShuntParameters, fixed_shunt_flow_ml_min
from .oxygenator import OxygenatorHydraulicParameters, oxygenator_delta_p_mmhg
from .patient_path import (
    PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    patient_path_delta_p_mmhg,
    solve_patient_path_flow_ml_min,
    solve_live_patient_path_flow_ml_min,
)
from .pump import DEFAULT_REVOLUTION_CURVE, PumpHeadCurveParameters, pump_head_mmhg
from .tubing_geometry import resistance_for_segment


@dataclass(frozen=True)
class MainCircuitFullPoint:
    """
    One solved operating point for the full standalone circuit: pump ->
    oxygenator -> [fixed shunt parallel with the bridge parallel with the
    real patient path (return tubing + real return/drain cannulas + a
    narrow vasculature-only placeholder)] -> back to the pump inlet.

    This is the last wiring stage before real patient physiology
    (neocirculation/neopatient) would be coupled in separately — this
    package still does not model the patient, only the circuit around
    where the patient would connect.
    """

    rpm: float
    inlet_reservoir_mmhg: float
    resistance_pre_pump_mmhg_per_ml_min: float
    solved_total_flow_ml_min: float
    solved_shunt_flow_ml_min: float
    solved_bridge_flow_ml_min: float
    solved_patient_flow_ml_min: float
    shunt_fraction: float
    bridge_fraction: float
    patient_fraction: float
    p1_mmhg: float
    p2_mmhg: float
    p3_mmhg: float
    junction_delta_p_mmhg: float
    pump_head_mmhg: float
    oxygenator_delta_p_mmhg: float


def solve_main_circuit_full_operating_point(
    rpm: float,
    inlet_reservoir_mmhg: float = 0.0,
    resistance_pre_pump_mmhg_per_ml_min: float = resistance_for_segment("main_pre_pump"),
    pump_curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
    oxygenator_params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
    shunt_params: FixedShuntParameters = FixedShuntParameters(),
    bridge_params: BridgeParameters = BridgeParameters(),  # closed by default
    return_cannula_params: CannulaHydraulicParameters = RETURN_8FR,
    drain_cannula_params: CannulaHydraulicParameters = DRAIN_10FR,
    vasculature_placeholder_resistance_mmhg_per_ml_min: float = PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    junction_delta_p_search_bounds_mmhg: tuple[float, float] = (0.0, 2000.0),
    patient_arterial_pressure_mmhg: float | None = None,
    patient_venous_pressure_mmhg: float | None = None,
    live_patient_residual_vasculature_resistance_mmhg_per_ml_min: float = 0.0,
) -> MainCircuitFullPoint:
    """
    Solve the full three-branch junction (shunt / bridge / real patient
    path) against the pump + oxygenator backbone.

    The patient branch is no longer a flat linear placeholder (Wiring
    Stages 2-3) — it's now the real composed return tubing + real
    return/drain cannula quadratic resistances + a narrow vasculature-only
    placeholder (see patient_path.py). Because the cannula terms are
    quadratic, the patient branch's effective resistance rises with flow
    while the shunt/bridge remain purely linear, so the shunt/bridge
    fraction is no longer expected to stay flat across RPM the way it did
    in Wiring Stages 2-3 — that's a genuinely new emergent behavior to
    check, not something tuned in.
    """

    def flows_at_junction_delta_p(delta_p: float) -> tuple[float, float, float, float]:
        q_shunt = fixed_shunt_flow_ml_min(delta_p, 0.0, shunt_params)
        q_bridge = bridge_flow_ml_min(delta_p, 0.0, bridge_params)
        if patient_arterial_pressure_mmhg is not None and patient_venous_pressure_mmhg is not None:
            q_patient = solve_live_patient_path_flow_ml_min(
                delta_p,
                patient_arterial_pressure_mmhg,
                patient_venous_pressure_mmhg,
                resistance_for_segment("main_return"),
                return_cannula_params,
                drain_cannula_params,
                live_patient_residual_vasculature_resistance_mmhg_per_ml_min,
            )
        else:
            q_patient = solve_patient_path_flow_ml_min(
                delta_p,
                resistance_for_segment("main_return"),
                return_cannula_params,
                drain_cannula_params,
                vasculature_placeholder_resistance_mmhg_per_ml_min,
            )
        return q_shunt, q_bridge, q_patient, q_shunt + q_bridge + q_patient

    def f(delta_p: float) -> float:
        _, _, _, q_total = flows_at_junction_delta_p(delta_p)
        return (
            pump_head_mmhg(rpm, q_total, pump_curve)
            - delta_p
            - oxygenator_delta_p_mmhg(q_total, oxygenator_params)
        )

    lo, hi = junction_delta_p_search_bounds_mmhg
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0.0:
        raise RuntimeError(
            "No sign change across the search bracket — widen "
            "junction_delta_p_search_bounds_mmhg for this RPM/parameter "
            "combination."
        )
    junction_delta_p = brentq(f, lo, hi, xtol=1e-6, rtol=1e-10)

    q_shunt, q_bridge, q_patient, q_total = flows_at_junction_delta_p(junction_delta_p)
    effective_inlet_pressure = patient_venous_pressure_mmhg if patient_venous_pressure_mmhg is not None else inlet_reservoir_mmhg
    p1 = effective_inlet_pressure - q_total * resistance_pre_pump_mmhg_per_ml_min
    p3 = p1 + junction_delta_p
    oxy_dp = oxygenator_delta_p_mmhg(q_total, oxygenator_params)
    p2 = p3 + oxy_dp
    head = pump_head_mmhg(rpm, q_total, pump_curve)

    return MainCircuitFullPoint(
        rpm=rpm,
        inlet_reservoir_mmhg=inlet_reservoir_mmhg,
        resistance_pre_pump_mmhg_per_ml_min=resistance_pre_pump_mmhg_per_ml_min,
        solved_total_flow_ml_min=q_total,
        solved_shunt_flow_ml_min=q_shunt,
        solved_bridge_flow_ml_min=q_bridge,
        solved_patient_flow_ml_min=q_patient,
        shunt_fraction=(q_shunt / q_total) if q_total > 0.0 else 0.0,
        bridge_fraction=(q_bridge / q_total) if q_total > 0.0 else 0.0,
        patient_fraction=(q_patient / q_total) if q_total > 0.0 else 0.0,
        p1_mmhg=p1,
        p2_mmhg=p2,
        p3_mmhg=p3,
        junction_delta_p_mmhg=junction_delta_p,
        pump_head_mmhg=head,
        oxygenator_delta_p_mmhg=oxy_dp,
    )


def solve_bridge_clamp_position_for_target_flow(
    target_bridge_flow_ml_min: float,
    rpm: float,
    inlet_reservoir_mmhg: float = 0.0,
    resistance_pre_pump_mmhg_per_ml_min: float = resistance_for_segment("main_pre_pump"),
    pump_curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
    oxygenator_params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
    shunt_params: FixedShuntParameters = FixedShuntParameters(),
    return_cannula_params: CannulaHydraulicParameters = RETURN_8FR,
    drain_cannula_params: CannulaHydraulicParameters = DRAIN_10FR,
    vasculature_placeholder_resistance_mmhg_per_ml_min: float = PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    bridge_clot_fraction: float = 0.0,
    clamp_position_search_bounds: tuple[float, float] = (0.0, 1.0),
    patient_arterial_pressure_mmhg: float | None = None,
    patient_venous_pressure_mmhg: float | None = None,
    live_patient_residual_vasculature_resistance_mmhg_per_ml_min: float = 0.0,
) -> tuple[float, MainCircuitFullPoint]:
    """
    Solve for the clamp position that produces a target bridge flow, given
    the rest of the circuit's current operating conditions.

    This mirrors how bridge management actually works clinically: nobody
    reads a clamp position off a dial and dials it in — you crack the
    clamp, watch the resulting flow, and adjust until you hit the flow
    you want. clamp_position stays an internal hydraulic parameter; this
    function exists so a future interface can be built around "titrate to
    a target flow" rather than around clamp percentage, the same way RPM
    (not flow) is the learner-facing pump control while flow is what gets
    watched. Bridge flow rises monotonically with clamp_position (holding
    everything else fixed), so a root-find over clamp_position is
    well-behaved.

    bridge_clot_fraction is pathology state (not a learner control),
    included so a scenario/complication layer can inject bridge clot risk
    even while flow is being titrated by target rather than by clamp
    position directly.

    Returns (clamp_position, the full solved circuit point at that
    clamp_position) so callers get both the answer and everything else
    that changed as a result (total flow, shunt/patient flows, pressures).
    """
    if target_bridge_flow_ml_min <= 0.0:
        clamp_position = 0.0
        point = solve_main_circuit_full_operating_point(
            rpm,
            inlet_reservoir_mmhg,
            resistance_pre_pump_mmhg_per_ml_min,
            pump_curve,
            oxygenator_params,
            shunt_params,
            BridgeParameters(clamp_position=clamp_position, clot_fraction=bridge_clot_fraction),
            return_cannula_params,
            drain_cannula_params,
            vasculature_placeholder_resistance_mmhg_per_ml_min,
            patient_arterial_pressure_mmhg=patient_arterial_pressure_mmhg,
            patient_venous_pressure_mmhg=patient_venous_pressure_mmhg,
            live_patient_residual_vasculature_resistance_mmhg_per_ml_min=live_patient_residual_vasculature_resistance_mmhg_per_ml_min,
        )
        return clamp_position, point

    def bridge_flow_at_clamp(clamp: float) -> float:
        return solve_main_circuit_full_operating_point(
            rpm,
            inlet_reservoir_mmhg,
            resistance_pre_pump_mmhg_per_ml_min,
            pump_curve,
            oxygenator_params,
            shunt_params,
            BridgeParameters(clamp_position=clamp, clot_fraction=bridge_clot_fraction),
            return_cannula_params,
            drain_cannula_params,
            vasculature_placeholder_resistance_mmhg_per_ml_min,
            patient_arterial_pressure_mmhg=patient_arterial_pressure_mmhg,
            patient_venous_pressure_mmhg=patient_venous_pressure_mmhg,
            live_patient_residual_vasculature_resistance_mmhg_per_ml_min=live_patient_residual_vasculature_resistance_mmhg_per_ml_min,
        ).solved_bridge_flow_ml_min

    def f(clamp: float) -> float:
        return bridge_flow_at_clamp(clamp) - target_bridge_flow_ml_min

    lo, hi = clamp_position_search_bounds
    f_lo, f_hi = f(lo), f(hi)
    if f_lo * f_hi > 0.0:
        raise RuntimeError(
            f"Target bridge flow {target_bridge_flow_ml_min} mL/min is not "
            f"achievable within clamp_position bounds {clamp_position_search_bounds} "
            "at this RPM/circuit configuration — even fully open, the bridge "
            "cannot reach that flow (or the target is negative)."
        )
    clamp_position = brentq(f, lo, hi, xtol=1e-6, rtol=1e-10)

    point = solve_main_circuit_full_operating_point(
        rpm,
        inlet_reservoir_mmhg,
        resistance_pre_pump_mmhg_per_ml_min,
        pump_curve,
        oxygenator_params,
        shunt_params,
        BridgeParameters(clamp_position=clamp_position, clot_fraction=bridge_clot_fraction),
        return_cannula_params,
        drain_cannula_params,
        vasculature_placeholder_resistance_mmhg_per_ml_min,
        patient_arterial_pressure_mmhg=patient_arterial_pressure_mmhg,
        patient_venous_pressure_mmhg=patient_venous_pressure_mmhg,
        live_patient_residual_vasculature_resistance_mmhg_per_ml_min=live_patient_residual_vasculature_resistance_mmhg_per_ml_min,
    )
    return clamp_position, point

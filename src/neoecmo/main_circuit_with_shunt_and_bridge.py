from __future__ import annotations

from dataclasses import dataclass

from scipy.optimize import brentq

from .bridge import BridgeParameters, bridge_flow_ml_min
from .fixed_shunt import FixedShuntParameters, fixed_shunt_flow_ml_min
from .main_circuit_with_shunt import PATIENT_PATH_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN
from .oxygenator import OxygenatorHydraulicParameters, oxygenator_delta_p_mmhg
from .pump import DEFAULT_REVOLUTION_CURVE, PumpHeadCurveParameters, pump_head_mmhg
from .tubing_geometry import resistance_for_segment


@dataclass(frozen=True)
class MainCircuitWithShuntAndBridgePoint:
    """
    One solved operating point for pump -> oxygenator -> [fixed shunt
    parallel with the bridge parallel with a placeholder patient-path
    resistance] -> back to the pump inlet.

    Real cannulas/patient physiology are still not wired in — the
    patient-path term remains the same placeholder used in Wiring Stage 2
    (see main_circuit_with_shunt.py for sourcing).
    """

    rpm: float
    inlet_reservoir_mmhg: float
    resistance_pre_pump_mmhg_per_ml_min: float
    patient_path_placeholder_resistance_mmhg_per_ml_min: float
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


def solve_main_circuit_with_shunt_and_bridge_operating_point(
    rpm: float,
    inlet_reservoir_mmhg: float = 0.0,
    resistance_pre_pump_mmhg_per_ml_min: float = resistance_for_segment("main_pre_pump"),
    patient_path_placeholder_resistance_mmhg_per_ml_min: float = PATIENT_PATH_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    pump_curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
    oxygenator_params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
    shunt_params: FixedShuntParameters = FixedShuntParameters(),
    bridge_params: BridgeParameters = BridgeParameters(),  # clamp_position=0.0 (closed) by default
    junction_delta_p_search_bounds_mmhg: tuple[float, float] = (0.0, 2000.0),
) -> MainCircuitWithShuntAndBridgePoint:
    """
    Solve for the flow split at the post-oxygenator junction, now with
    three parallel branches back to the pump inlet: the fixed shunt, the
    bridge, and the (still placeholder) patient path.

    With the bridge left at its clinical default (fully clamped shut,
    clamp_position=0.0), it contributes exactly zero flow and this should
    reduce to the same result as Wiring Stage 2 (main_circuit_with_shunt)
    — that equivalence is the regression check for this stage: adding a
    branch that is closed by default must not change anything until it is
    deliberately opened.
    """

    def flows_at_junction_delta_p(delta_p: float) -> tuple[float, float, float, float]:
        q_shunt = fixed_shunt_flow_ml_min(delta_p, 0.0, shunt_params)
        q_bridge = bridge_flow_ml_min(delta_p, 0.0, bridge_params)
        q_patient = delta_p / patient_path_placeholder_resistance_mmhg_per_ml_min
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
    p1 = inlet_reservoir_mmhg - q_total * resistance_pre_pump_mmhg_per_ml_min
    p3 = p1 + junction_delta_p
    oxy_dp = oxygenator_delta_p_mmhg(q_total, oxygenator_params)
    p2 = p3 + oxy_dp
    head = pump_head_mmhg(rpm, q_total, pump_curve)

    return MainCircuitWithShuntAndBridgePoint(
        rpm=rpm,
        inlet_reservoir_mmhg=inlet_reservoir_mmhg,
        resistance_pre_pump_mmhg_per_ml_min=resistance_pre_pump_mmhg_per_ml_min,
        patient_path_placeholder_resistance_mmhg_per_ml_min=patient_path_placeholder_resistance_mmhg_per_ml_min,
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

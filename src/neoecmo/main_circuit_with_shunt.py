from __future__ import annotations

from dataclasses import dataclass

from scipy.optimize import brentq

from .fixed_shunt import FixedShuntParameters, fixed_shunt_flow_ml_min
from .oxygenator import OxygenatorHydraulicParameters, oxygenator_delta_p_mmhg
from .pump import DEFAULT_REVOLUTION_CURVE, PumpHeadCurveParameters, pump_head_mmhg
from .tubing_geometry import resistance_for_segment

# Placeholder resistance standing in for "everything downstream of the
# oxygenator that isn't the shunt": return tubing + return cannula +
# patient vasculature + drain cannula + pre-pump-adjacent tubing, none of
# which are wired into this circuit yet (cannulas are a later wiring
# stage; patient vasculature doesn't exist in this package at all).
#
# Value is NOT a guess: it's the patient-path resistance implied by the
# clinical author's own real cross-check numbers (bridge closed, 600
# mL/min total flow split ~240 shunt / ~360 patient -> back-solved
# implied patient-path resistance of ~0.489 mmHg/(mL/min), see chat
# 2026-07-25). This must be replaced once cannulas are wired into this
# stage and real patient-path composition becomes possible.
PATIENT_PATH_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN = 0.4889


@dataclass(frozen=True)
class MainCircuitWithShuntPoint:
    """
    One solved operating point for pump -> oxygenator -> [fixed shunt
    parallel with a placeholder patient-path resistance] -> back to the
    pump inlet. Still no bridge branch or real cannulas/patient
    physiology — those are separate later wiring stages.

    This is now effectively a closed loop except for inlet_reservoir_mmhg,
    which only sets the absolute pressure baseline for reporting P1/P2/P3
    — it does not affect the solved flow split, since nothing external
    drives flow around a closed loop.
    """

    rpm: float
    inlet_reservoir_mmhg: float
    resistance_pre_pump_mmhg_per_ml_min: float
    patient_path_placeholder_resistance_mmhg_per_ml_min: float
    solved_total_flow_ml_min: float
    solved_shunt_flow_ml_min: float
    solved_patient_flow_ml_min: float
    shunt_fraction: float
    p1_mmhg: float
    p2_mmhg: float
    p3_mmhg: float
    junction_delta_p_mmhg: float
    pump_head_mmhg: float
    oxygenator_delta_p_mmhg: float


def solve_main_circuit_with_shunt_operating_point(
    rpm: float,
    inlet_reservoir_mmhg: float = 0.0,
    resistance_pre_pump_mmhg_per_ml_min: float = resistance_for_segment("main_pre_pump"),
    patient_path_placeholder_resistance_mmhg_per_ml_min: float = PATIENT_PATH_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    pump_curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
    oxygenator_params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
    shunt_params: FixedShuntParameters = FixedShuntParameters(),
    junction_delta_p_search_bounds_mmhg: tuple[float, float] = (0.0, 2000.0),
) -> MainCircuitWithShuntPoint:
    """
    Solve for the flow split at the post-oxygenator junction, where the
    fixed shunt and the (placeholder) patient path run in parallel back to
    the pump inlet.

    Solved by finding the junction delta_p (P3 - P1) at which:

        pump_head(rpm, Q_total) = junction_delta_p + oxygenator_delta_p(Q_total)

    where Q_total = Q_shunt(junction_delta_p) + Q_patient(junction_delta_p),
    Q_shunt comes from the real fixed_shunt module, and Q_patient uses the
    placeholder linear resistance above (see its docstring for why).
    """

    def flows_at_junction_delta_p(delta_p: float) -> tuple[float, float, float]:
        q_shunt = fixed_shunt_flow_ml_min(delta_p, 0.0, shunt_params)
        q_patient = delta_p / patient_path_placeholder_resistance_mmhg_per_ml_min
        return q_shunt, q_patient, q_shunt + q_patient

    def f(delta_p: float) -> float:
        _, _, q_total = flows_at_junction_delta_p(delta_p)
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

    q_shunt, q_patient, q_total = flows_at_junction_delta_p(junction_delta_p)
    p1 = inlet_reservoir_mmhg - q_total * resistance_pre_pump_mmhg_per_ml_min
    p3 = p1 + junction_delta_p
    oxy_dp = oxygenator_delta_p_mmhg(q_total, oxygenator_params)
    p2 = p3 + oxy_dp
    head = pump_head_mmhg(rpm, q_total, pump_curve)

    return MainCircuitWithShuntPoint(
        rpm=rpm,
        inlet_reservoir_mmhg=inlet_reservoir_mmhg,
        resistance_pre_pump_mmhg_per_ml_min=resistance_pre_pump_mmhg_per_ml_min,
        patient_path_placeholder_resistance_mmhg_per_ml_min=patient_path_placeholder_resistance_mmhg_per_ml_min,
        solved_total_flow_ml_min=q_total,
        solved_shunt_flow_ml_min=q_shunt,
        solved_patient_flow_ml_min=q_patient,
        shunt_fraction=(q_shunt / q_total) if q_total > 0.0 else 0.0,
        p1_mmhg=p1,
        p2_mmhg=p2,
        p3_mmhg=p3,
        junction_delta_p_mmhg=junction_delta_p,
        pump_head_mmhg=head,
        oxygenator_delta_p_mmhg=oxy_dp,
    )

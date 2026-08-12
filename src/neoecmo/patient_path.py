from __future__ import annotations

from scipy.optimize import brentq

from .cannula import DRAIN_10FR, RETURN_8FR, CannulaHydraulicParameters, cannula_delta_p_mmhg
from .tubing_geometry import resistance_for_segment

# This is now a NARROWER placeholder than the one used in Wiring Stages 2-3:
# it stands in only for patient vasculature itself (systemic vascular
# resistance), since real return tubing and real cannulas are now composed
# directly below rather than lumped into one flat number. Patient
# vasculature is not part of this package by design (neoecmo never models
# patient physiology — that lives in neocirculation/neopatient, coupled
# later) so this remains a placeholder, but it is now a much smaller,
# better-isolated one.
#
# Derived (not guessed) by back-solving against the same real cross-check
# used before: at the clinical author's reported ~360 mL/min patient flow
# with the bridge closed, the junction delta_p (~176 mmHg, matching what
# the shunt alone implies at that operating point) minus the real return
# tubing + real return/drain cannula pressure drops at that flow leaves
# ~128.7 mmHg unaccounted for -> ~0.3574 mmHg/(mL/min) of vasculature
# resistance (chat 2026-07-26).
PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN = 0.3574


def patient_path_delta_p_mmhg(
    flow_ml_min: float,
    return_tubing_resistance_mmhg_per_ml_min: float = resistance_for_segment("main_return"),
    return_cannula_params: CannulaHydraulicParameters = RETURN_8FR,
    drain_cannula_params: CannulaHydraulicParameters = DRAIN_10FR,
    vasculature_placeholder_resistance_mmhg_per_ml_min: float = PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
) -> float:
    """
    Total pressure drop along the patient path: return tubing (real,
    grounded) -> return cannula (real, empirical) -> [patient vasculature
    — still a placeholder, out of scope for this package] -> drain
    cannula (real, empirical). Series resistances add directly.

    Unlike Wiring Stages 2-3's flat linear placeholder, this composition
    is no longer purely linear in flow: the cannula terms are quadratic,
    so this path's resistance effectively rises with flow, while the
    shunt/bridge remain purely linear (laminar tubing). That is a
    genuinely new, testable emergent behavior versus the earlier stages,
    not something tuned in — see main_circuit_full.py tests.
    """
    sign = 1.0 if flow_ml_min >= 0.0 else -1.0
    magnitude = abs(flow_ml_min)
    dp = (
        magnitude * return_tubing_resistance_mmhg_per_ml_min
        + cannula_delta_p_mmhg(magnitude, return_cannula_params)
        + cannula_delta_p_mmhg(magnitude, drain_cannula_params)
        + magnitude * vasculature_placeholder_resistance_mmhg_per_ml_min
    )
    return sign * dp


def solve_patient_path_flow_ml_min(
    delta_p_mmhg: float,
    return_tubing_resistance_mmhg_per_ml_min: float = resistance_for_segment("main_return"),
    return_cannula_params: CannulaHydraulicParameters = RETURN_8FR,
    drain_cannula_params: CannulaHydraulicParameters = DRAIN_10FR,
    vasculature_placeholder_resistance_mmhg_per_ml_min: float = PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    flow_search_bound_ml_min: float = 20000.0,
) -> float:
    """Invert patient_path_delta_p_mmhg to find the flow that produces a
    given pressure drop (root-find, since the cannula terms make this
    nonlinear in flow, unlike the earlier flat linear placeholder)."""
    if delta_p_mmhg == 0.0:
        return 0.0
    sign = 1.0 if delta_p_mmhg > 0.0 else -1.0
    magnitude = abs(delta_p_mmhg)

    def f(q: float) -> float:
        return (
            patient_path_delta_p_mmhg(
                q,
                return_tubing_resistance_mmhg_per_ml_min,
                return_cannula_params,
                drain_cannula_params,
                vasculature_placeholder_resistance_mmhg_per_ml_min,
            )
            - magnitude
        )

    solved = brentq(f, 0.0, flow_search_bound_ml_min, xtol=1e-6, rtol=1e-10)
    return sign * solved


def live_patient_path_delta_p_mmhg(
    flow_ml_min: float,
    arterial_pressure_mmhg: float,
    venous_pressure_mmhg: float,
    return_tubing_resistance_mmhg_per_ml_min: float = resistance_for_segment("main_return"),
    return_cannula_params: CannulaHydraulicParameters = RETURN_8FR,
    drain_cannula_params: CannulaHydraulicParameters = DRAIN_10FR,
    vasculature_resistance_mmhg_per_ml_min: float = 0.0,
) -> float:
    """Pressure required across the external patient branch.

    The live patient owns the arterial-to-venous pressure gradient. The
    circuit owns tubing and cannula losses. A residual vasculature term is
    optional and defaults to zero so the patient's measured MAP/CVP are not
    counted twice.
    """
    patient_gradient = arterial_pressure_mmhg - venous_pressure_mmhg
    return (
        patient_gradient
        + flow_ml_min * return_tubing_resistance_mmhg_per_ml_min
        + cannula_delta_p_mmhg(flow_ml_min, return_cannula_params)
        + flow_ml_min * vasculature_resistance_mmhg_per_ml_min
        + cannula_delta_p_mmhg(flow_ml_min, drain_cannula_params)
    )


def solve_live_patient_path_flow_ml_min(
    available_delta_p_mmhg: float,
    arterial_pressure_mmhg: float,
    venous_pressure_mmhg: float,
    return_tubing_resistance_mmhg_per_ml_min: float = resistance_for_segment("main_return"),
    return_cannula_params: CannulaHydraulicParameters = RETURN_8FR,
    drain_cannula_params: CannulaHydraulicParameters = DRAIN_10FR,
    vasculature_resistance_mmhg_per_ml_min: float = 0.0,
    flow_search_bound_ml_min: float = 20000.0,
) -> float:
    """Solve patient-directed ECMO flow against live MAP and CVP.

    No forward patient flow is possible until circuit pressure exceeds the
    patient's arterial-to-venous pressure gradient.
    """
    zero_flow_requirement = arterial_pressure_mmhg - venous_pressure_mmhg
    if available_delta_p_mmhg <= zero_flow_requirement:
        return 0.0

    def f(q: float) -> float:
        return live_patient_path_delta_p_mmhg(
            q,
            arterial_pressure_mmhg,
            venous_pressure_mmhg,
            return_tubing_resistance_mmhg_per_ml_min,
            return_cannula_params,
            drain_cannula_params,
            vasculature_resistance_mmhg_per_ml_min,
        ) - available_delta_p_mmhg

    return brentq(f, 0.0, flow_search_bound_ml_min, xtol=1e-6, rtol=1e-10)

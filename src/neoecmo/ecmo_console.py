from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .bridge import BridgeParameters
from .cannula import DRAIN_10FR, RETURN_8FR, CannulaHydraulicParameters
from .cdi_sensor import CDIReading, cdi_reading_from_circuit_point
from .post_oxygenator_cdi import (
    PostOxygenatorBloodState,
    PostOxyCdiReading,
    PostOxyCdiSensorState,
    measure_post_oxygenator_blood,
)
from .fixed_shunt import FixedShuntParameters, ShuntLineConfiguration
from .main_circuit_full import (
    MainCircuitFullPoint,
    solve_bridge_clamp_position_for_target_flow,
    solve_main_circuit_full_operating_point,
)
from .oxygenator import OxygenatorHydraulicParameters
from .oxygenator_gas_exchange import (
    OxygenatorGasExchangeParameters,
    outlet_o2_saturation,
    outlet_po2_mmhg,
    outlet_paco2_mmhg,
    po2_from_saturation_mmhg,
    round_fdo2_to_blender_step,
)
from .patient_path import PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN
from .pump import DEFAULT_REVOLUTION_CURVE, PumpHeadCurveParameters
from .tubing_geometry import resistance_for_segment


@dataclass(frozen=True)
class EcmoConsoleControls:
    """
    Every control an ECMO specialist can actually adjust on this circuit,
    at any time, per everything built and confirmed in this package. This
    is deliberately the FULL set and no more — device specs (pump curve,
    cannula sizing, tubing geometry) and pathology/complication states
    (clot fractions, membrane obstruction) are NOT controls; they're
    passed to run_ecmo_console separately with clean defaults, since a
    learner doesn't set those, a scenario/complication engine does.

    rpm: the pump control. Flow is never set directly — it's the
    resultant, exactly per the pump-curve solve throughout this package.

    Bridge: real bridge management is titrate-by-watching-flow, not by a
    known clamp percentage (confirmed directly). Set
    bridge_target_flow_ml_min to titrate to a specific bridge flow (the
    realistic control action); leave it None and set
    bridge_clamp_position directly only for testing/debugging at a known
    clamp position. bridge_clamp_position is ignored whenever
    bridge_target_flow_ml_min is provided.

    Shunt line: shunt_configuration selects OPEN / HEMOFILTER / CKRT (the
    confirmed 3-stopcock-configuration anatomy). shunt_scuffing_active
    only matters in HEMOFILTER. shunt_ckrt_blood_flow_ml_min and
    shunt_ckrt_net_ultrafiltration_rate_ml_min only matter in CKRT (and
    have zero effect on shunt hydraulics either way — confirmed directly
    that CKRT does not use the shunt's own blood volume).

    Sweep gas: fdo2 (rounded to the real Spectrum blender's 1% steps,
    21-100%) and sweep_gas_flow_ml_min are both real, continuously
    adjustable controls.
    """

    rpm: float = 0.0

    bridge_clamp_position: float = 0.0
    bridge_target_flow_ml_min: Optional[float] = None

    shunt_configuration: ShuntLineConfiguration = ShuntLineConfiguration.OPEN
    shunt_scuffing_active: bool = False
    shunt_ckrt_blood_flow_ml_min: float = 0.0
    shunt_ckrt_net_ultrafiltration_rate_ml_min: float = 0.0

    fdo2: float = 1.0
    sweep_gas_flow_ml_min: float = 0.0


@dataclass(frozen=True)
class EcmoConsoleState:
    """Everything the learner-facing monitor would show, plus the
    resolved controls actually applied (e.g. the clamp_position the
    bridge titration solved to, and fdo2 snapped to the real blender
    step) — for display/logging, not for feeding back into the next
    call."""

    circuit: MainCircuitFullPoint
    resolved_bridge_clamp_position: float
    resolved_fdo2: float
    post_oxygenator_saturation: float
    post_oxygenator_po2_mmhg: float
    post_oxygenator_paco2_mmhg: float
    post_oxygenator_blood: PostOxygenatorBloodState
    post_oxygenator_cdi: PostOxyCdiReading
    cdi: CDIReading


def run_ecmo_console(
    controls: EcmoConsoleControls,
    native_venous_saturation: float,
    native_venous_paco2_mmhg: float,
    pump_curve: PumpHeadCurveParameters = DEFAULT_REVOLUTION_CURVE,
    oxygenator_hydraulic_params: OxygenatorHydraulicParameters = OxygenatorHydraulicParameters(),
    oxygenator_gas_params: OxygenatorGasExchangeParameters = OxygenatorGasExchangeParameters(),
    return_cannula_params: CannulaHydraulicParameters = RETURN_8FR,
    drain_cannula_params: CannulaHydraulicParameters = DRAIN_10FR,
    shunt_clot_fraction: float = 0.0,
    bridge_clot_fraction: float = 0.0,
    vasculature_placeholder_resistance_mmhg_per_ml_min: float = PATIENT_VASCULATURE_PLACEHOLDER_RESISTANCE_MMHG_PER_ML_MIN,
    resistance_pre_pump_mmhg_per_ml_min: float = resistance_for_segment("main_pre_pump"),
    hematocrit_pct: float = 38.0,
    hemoglobin_g_dl: float = 12.7,
    blood_temperature_c: float = 37.0,
    post_oxy_cdi_sensor: PostOxyCdiSensorState = PostOxyCdiSensorState(),
    patient_arterial_pressure_mmhg: float | None = None,
    patient_venous_pressure_mmhg: float | None = None,
    live_patient_residual_vasculature_resistance_mmhg_per_ml_min: float = 0.0,
) -> EcmoConsoleState:
    """
    Apply one full set of learner controls to the whole verified circuit
    and return everything the monitor would show in a single bundle:
    solved flows/pressures, post-oxygenator gas values, and the CDI
    reading — instead of the several separate calls each of those
    previously required.

    native_venous_saturation / native_venous_paco2_mmhg remain required
    inputs, not computed values: real patient physiology
    (neocirculation/neopatient) is not coupled into this package yet (a
    separate, larger integration effort) — this console is the ECMO
    circuit's control surface only.

    shunt_clot_fraction / bridge_clot_fraction are pathology state, not
    learner controls, included here only as pass-throughs with clean
    (0.0) defaults so a scenario/complication layer can inject them
    later without this console needing to change shape.
    """
    fdo2 = round_fdo2_to_blender_step(controls.fdo2)

    shunt_params = FixedShuntParameters(
        clot_fraction=shunt_clot_fraction,
        configuration=controls.shunt_configuration,
        scuffing_active=controls.shunt_scuffing_active,
        ckrt_blood_flow_ml_min=controls.shunt_ckrt_blood_flow_ml_min,
        ckrt_net_ultrafiltration_rate_ml_min=controls.shunt_ckrt_net_ultrafiltration_rate_ml_min,
    )

    common_kwargs = dict(
        resistance_pre_pump_mmhg_per_ml_min=resistance_pre_pump_mmhg_per_ml_min,
        pump_curve=pump_curve,
        oxygenator_params=oxygenator_hydraulic_params,
        shunt_params=shunt_params,
        return_cannula_params=return_cannula_params,
        drain_cannula_params=drain_cannula_params,
        vasculature_placeholder_resistance_mmhg_per_ml_min=vasculature_placeholder_resistance_mmhg_per_ml_min,
        patient_arterial_pressure_mmhg=patient_arterial_pressure_mmhg,
        patient_venous_pressure_mmhg=patient_venous_pressure_mmhg,
        live_patient_residual_vasculature_resistance_mmhg_per_ml_min=live_patient_residual_vasculature_resistance_mmhg_per_ml_min,
    )

    if controls.bridge_target_flow_ml_min is not None:
        resolved_clamp, circuit = solve_bridge_clamp_position_for_target_flow(
            controls.bridge_target_flow_ml_min,
            controls.rpm,
            bridge_clot_fraction=bridge_clot_fraction,
            **common_kwargs,
        )
    else:
        resolved_clamp = controls.bridge_clamp_position
        bridge_params = BridgeParameters(
            clamp_position=resolved_clamp, clot_fraction=bridge_clot_fraction
        )
        circuit = solve_main_circuit_full_operating_point(
            controls.rpm,
            bridge_params=bridge_params,
            **common_kwargs,
        )

    # A complete sweep-gas loss means there is no gas-side flow across the
    # membrane lung.  Preserve the established nonzero-sweep behavior
    # (FdO2 primarily governs O2 transfer; sweep primarily governs CO2),
    # but do not allow zero sweep to keep producing oxygenated return blood.
    # At zero sweep the post-oxygenator gas state therefore equals the inlet
    # venous state for O2 while the existing CO2 model naturally returns the
    # inlet pCO2.
    if controls.sweep_gas_flow_ml_min <= 0.0:
        post_oxy_sat = native_venous_saturation
        post_oxy_po2 = po2_from_saturation_mmhg(native_venous_saturation)
    else:
        post_oxy_sat = outlet_o2_saturation(
            native_venous_saturation,
            circuit.solved_total_flow_ml_min,
            fdo2,
            oxygenator_gas_params,
        )
        post_oxy_po2 = outlet_po2_mmhg(
            native_venous_saturation,
            circuit.solved_total_flow_ml_min,
            fdo2,
            oxygenator_gas_params,
        )
    post_oxy_paco2 = outlet_paco2_mmhg(
        native_venous_paco2_mmhg,
        circuit.solved_total_flow_ml_min,
        controls.sweep_gas_flow_ml_min,
        oxygenator_gas_params.obstruction_fraction,
    )
    post_oxy_blood = PostOxygenatorBloodState(
        po2_mmhg=post_oxy_po2,
        pco2_mmhg=post_oxy_paco2,
        oxygen_saturation=post_oxy_sat,
        hematocrit_pct=hematocrit_pct,
        hemoglobin_g_dl=hemoglobin_g_dl,
        temperature_c=blood_temperature_c,
    )
    post_oxy_blood.validate()
    post_oxy_cdi = measure_post_oxygenator_blood(post_oxy_blood, post_oxy_cdi_sensor)
    cdi = cdi_reading_from_circuit_point(
        circuit,
        native_venous_saturation,
        post_oxy_sat,
        native_venous_paco2_mmhg,
        post_oxy_paco2,
    )

    return EcmoConsoleState(
        circuit=circuit,
        resolved_bridge_clamp_position=resolved_clamp,
        resolved_fdo2=fdo2,
        post_oxygenator_saturation=post_oxy_sat,
        post_oxygenator_po2_mmhg=post_oxy_po2,
        post_oxygenator_paco2_mmhg=post_oxy_paco2,
        post_oxygenator_blood=post_oxy_blood,
        post_oxygenator_cdi=post_oxy_cdi,
        cdi=cdi,
    )

from dataclasses import dataclass
from datetime import datetime, timezone
from neocirculation import TARGETS
from neocoupling import run_coupled_neonate
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters
from neokidney import KidneyParameters, KidneyState, calculate_kidney_state, update_fluid_balance
from .ports import AirwayPort, VascularSupportPort, RenalTherapyPort, MyocardialFunctionPort
from neoblood import mix_native_and_ecmo_arterial_blood
from neoventilator import PressureControlSettings
from .volume_ledger import VolumeLedgerConfig, VolumeLedgerState, snapshot_volume_ledger
from .async_native import NativePhysiologyAsyncRunner, NativeSolveRequest

@dataclass(frozen=True)
class UnifiedPatientConfig:
    weight_kg: float = 3.5
    intravascular_fraction_of_net_fluid: float = 0.25
    blood_volume_ml_per_kg: float = 86.0
    lung_run_s: float = 12.0
    circulation_run_s: float = 12.0
    native_physiology_volume_recalc_threshold_ml: float = 0.10
    native_physiology_async: bool = False
    native_physiology_executor: str = "thread"

@dataclass
class UnifiedPatientState:
    elapsed_min: float = 0.0
    cumulative_net_body_fluid_ml: float = 0.0
    blood_volume_delta_ml: float = 0.0
    cumulative_urine_ml: float = 0.0
    volume_ledger: VolumeLedgerState = None

    def __post_init__(self):
        if self.volume_ledger is None:
            self.volume_ledger = VolumeLedgerState()

@dataclass(frozen=True)
class VenousPreloadState:
    """Simplified patient-boundary venous preload state.

    ``intrathoracic_relative_preload_proxy_mmhg`` illustrates a known
    pressure relationship for teaching. It is not a validated transmural
    preload measurement or a patient/device-specific quantitative model.
    """

    cvp_mmhg: float
    pleural_delta_mmhg: float
    intrathoracic_relative_preload_proxy_mmhg: float
    effective_venous_volume_ml: float
    effective_venous_volume_fraction: float


@dataclass(frozen=True)
class VenousOxygenState:
    """Native mixed-venous oxygen state owned by the native coupling solve."""

    native_mixed_venous_po2_mmhg: float
    native_mixed_venous_saturation_pct: float
    native_mixed_venous_oxygen_content_ml_dl: float


@dataclass(frozen=True)
class VenousState:
    """Immutable unified-patient boundary container; not an independent solver."""

    preload: VenousPreloadState
    oxygen: VenousOxygenState


@dataclass(frozen=True)
class UnifiedPatientSnapshot:
    elapsed_min: float
    total_blood_volume_ml: float
    blood_volume_fraction: float
    effective_venous_volume_ml: float
    effective_venous_volume_fraction: float
    third_space_volume_ml: float
    map_mmhg: float
    systolic_mmhg: float
    diastolic_mmhg: float
    cvp_mmhg: float
    native_cardiac_output_ml_min: float
    pulmonary_flow_ml_min: float
    mean_pa_pressure_mmhg: float
    pao2_mmhg: float
    paco2_mmhg: float
    sao2_pct: float
    respiratory_rate_bpm: float
    tidal_volume_ml: float
    minute_ventilation_ml_min: float
    ventilator_mode: str
    pvr_multiplier: float
    renal_flow_ml_min: float
    renal_perfusion_pressure_mmhg: float
    urine_ml_kg_hr: float
    cumulative_urine_ml: float
    cumulative_net_body_fluid_ml: float
    vascular_support_enabled: bool
    vascular_support_flow_ml_min: float
    venous: VenousState

class UnifiedNeonatalPatient:
    """Unified orchestration shell for the three independently testable systems."""
    def __init__(self, config=None):
        self.config=config or UnifiedPatientConfig()
        self.state=UnifiedPatientState()
        self.volume_config=VolumeLedgerConfig(
            blood_volume_ml_per_kg=self.config.blood_volume_ml_per_kg,
            default_input_intravascular_fraction=self.config.intravascular_fraction_of_net_fluid,
        )
        self.airway=AirwayPort()
        self.vascular_support=VascularSupportPort()
        self.renal_therapy=RenalTherapyPort()
        self.myocardial_function=MyocardialFunctionPort()
        self._physiology_cache_key = None
        self._physiology_cache = None
        self._physiology_cache_blood_volume_delta_ml = None
        self._native_async_runner = NativePhysiologyAsyncRunner(self.config.native_physiology_executor) if self.config.native_physiology_async else None
        self._native_async_revision = 0
        self._native_async_latest_requested_revision = 0
        self._native_async_latest_signature = None
        self._native_async_debug_events = []

    def set_airway(self, port):
        self.airway=port
        self._physiology_cache_key = None
    def set_vascular_support(self, port): self.vascular_support=port
    def set_renal_therapy(self, port): self.renal_therapy=port
    def set_myocardial_function(self, port):
        self.myocardial_function=port
        self._physiology_cache_key = None

    def _native_cache_key(self):
        return (
            self.config.weight_kg,
            self.config.lung_run_s,
            self.config.circulation_run_s,
            self.airway.peep_cmh2o,
            self.airway.airway_opening_pressure_cmh2o,
            self.airway.fio2,
            None if self.airway.pressure_control is None else self.airway.pressure_control.pip_cmh2o,
            None if self.airway.pressure_control is None else self.airway.pressure_control.peep_cmh2o,
            None if self.airway.pressure_control is None else self.airway.pressure_control.rate_bpm,
            None if self.airway.pressure_control is None else self.airway.pressure_control.inspiratory_time_s,
            None if self.airway.pressure_control is None else self.airway.pressure_control.fio2,
            None if self.airway.pressure_control is None else self.airway.pressure_control.rise_time_s,
            None if self.airway.pressure_control is None else self.airway.pressure_control.fall_time_s,
            self.myocardial_function.lv_contractility_scale,
            self.myocardial_function.rv_contractility_scale,
        )

    def _native_cache_hit(self, cache_key, blood_volume_delta_ml):
        volume_recalc_threshold_ml = max(0.0, self.config.native_physiology_volume_recalc_threshold_ml)
        cached_volume = self._physiology_cache_blood_volume_delta_ml
        return (
            cache_key == self._physiology_cache_key
            and self._physiology_cache is not None
            and cached_volume is not None
            and abs(blood_volume_delta_ml - cached_volume) < volume_recalc_threshold_ml
        )

    def _solve_native_sync(self, cache_key, blood_volume_delta_ml):
        lp=LungParameters(weight_kg=self.config.weight_kg,
            peep_cmh2o=self.airway.peep_cmh2o,
            airway_opening_pressure_cmh2o=self.airway.airway_opening_pressure_cmh2o)
        gp=GasExchangeParameters(weight_kg=self.config.weight_kg,fio2=self.airway.fio2)
        result = run_coupled_neonate(lung_params=lp,gas_params=gp,
            duration_lung_s=self.config.lung_run_s,
            duration_circulation_s=self.config.circulation_run_s,
            blood_volume_delta_ml=blood_volume_delta_ml,
            pressure_control=self.airway.pressure_control,
            lv_contractility_scale=self.myocardial_function.lv_contractility_scale,
            rv_contractility_scale=self.myocardial_function.rv_contractility_scale)
        self._physiology_cache_key = cache_key
        self._physiology_cache_blood_volume_delta_ml = blood_volume_delta_ml
        self._physiology_cache = result
        return result

    def _poll_native_async_result(self):
        runner = self._native_async_runner
        if runner is None:
            return
        completed = runner.poll_completed()
        if completed is None:
            return
        committed = completed.revision == self._native_async_latest_requested_revision
        # Cache mutation is deliberately main-thread-only. A completed result
        # becomes authoritative only if no newer native-physiology request has
        # superseded its revision.
        if committed:
            self._physiology_cache_key = completed.cache_key
            self._physiology_cache_blood_volume_delta_ml = completed.blood_volume_delta_ml
            self._physiology_cache = completed.physiology
            self._native_async_latest_signature = None
        self._native_async_debug_events.append({
            "revision": completed.revision,
            "event_type": "native_physiology_result",
            "event_time": None,
            "solver_completion_time": datetime.now(timezone.utc).isoformat(),
            "status": "committed" if committed else "discarded_stale",
        })

    def _request_native_async(self, cache_key, blood_volume_delta_ml):
        signature = (cache_key, float(blood_volume_delta_ml))
        if signature == self._native_async_latest_signature:
            return
        self._native_async_revision += 1
        self._native_async_latest_requested_revision = self._native_async_revision
        self._native_async_latest_signature = signature
        self._native_async_debug_events.append({
            "revision": self._native_async_revision,
            "event_type": "native_physiology_request",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "solver_completion_time": None,
            "status": "requested",
        })
        self._native_async_runner.submit_latest(
            NativeSolveRequest(
                revision=self._native_async_revision,
                cache_key=cache_key,
                blood_volume_delta_ml=float(blood_volume_delta_ml),
            )
        )

    def _solve(self):
        # The expensive native cardiopulmonary solve depends only on airway
        # settings and intravascular volume. ECMO support and renal therapy are
        # applied later in snapshot(), so repeated display/circuit snapshots
        # can safely reuse this result until one of those native inputs changes.
        cache_key = self._native_cache_key()
        blood_volume_delta_ml = self.state.blood_volume_delta_ml

        if self._native_async_runner is not None:
            self._poll_native_async_result()

        if self._native_cache_hit(cache_key, blood_volume_delta_ml):
            return self._physiology_cache

        if self._native_async_runner is not None and self._physiology_cache is not None:
            self._request_native_async(cache_key, blood_volume_delta_ml)
            # Non-blocking GUI semantics: while the new equilibrium is being
            # calculated, continue from the last-known-good native state.
            return self._physiology_cache

        # Initial solve, and all default/headless usage, remain synchronous.
        return self._solve_native_sync(cache_key, blood_volume_delta_ml)

    @property
    def native_physiology_update_pending(self):
        if self._native_async_runner is None:
            return False
        cache_key = self._native_cache_key()
        if not self._native_cache_hit(cache_key, self.state.blood_volume_delta_ml):
            return True
        return (
            self._native_async_runner.active_revision is not None
            or self._native_async_runner.pending_revision is not None
        )

    @property
    def native_physiology_debug_events(self):
        return tuple(self._native_async_debug_events)

    def shutdown(self):
        if self._native_async_runner is not None:
            self._native_async_runner.shutdown()

    def snapshot(self, *, include_vascular_support=True):
        cp=self._solve(); c=cp.circulation_metrics
        ledger=snapshot_volume_ledger(weight_kg=self.config.weight_kg, config=self.volume_config, state=self.state.volume_ledger)
        tbv=ledger.current_intravascular_volume_ml
        vf=ledger.blood_volume_fraction
        support_enabled = include_vascular_support and self.vascular_support.enabled
        native_multiplier = self.vascular_support.native_output_multiplier if support_enabled else 1.0
        native_multiplier = max(0.0, min(1.0, native_multiplier))
        native_output = c.native_output_ml_min * native_multiplier
        patient_map = (self.vascular_support.supported_map_mmhg
            if support_enabled and self.vascular_support.supported_map_mmhg is not None
            else c.mean_aortic_mmhg)
        native_pulse = max(0.0, c.systolic_aortic_mmhg - c.diastolic_aortic_mmhg)
        pulse_pressure = (self.vascular_support.estimated_pulse_pressure_mmhg
            if support_enabled and self.vascular_support.estimated_pulse_pressure_mmhg is not None
            else native_pulse)
        patient_diastolic = patient_map - pulse_pressure / 3.0
        patient_systolic = patient_map + 2.0 * pulse_pressure / 3.0
        effective_systemic_flow = native_output + (self.vascular_support.support_flow_ml_min if support_enabled else 0.0)
        k=calculate_kidney_state(KidneyParameters(weight_kg=self.config.weight_kg),KidneyState(),
            map_mmhg=patient_map,cvp_mmhg=c.mean_ra_mmhg,
            systemic_flow_ml_min=effective_systemic_flow,
            renal_vaso_tone=self.renal_therapy.renal_vaso_tone,
            function_fraction=self.renal_therapy.renal_function_fraction,
            diuretic_multiplier=self.renal_therapy.diuretic_multiplier,
            circulating_volume_fraction=vf,dt_s=0)
        patient_pao2 = cp.gas.arterial_po2_mmhg
        patient_paco2 = cp.gas.arterial_pco2_mmhg
        patient_sao2 = cp.gas.arterial_saturation_pct
        if support_enabled and self.vascular_support.support_flow_ml_min > 0.0:
            mixed = mix_native_and_ecmo_arterial_blood(
                native_flow_ml_min=native_output,
                native_pao2_mmhg=cp.gas.arterial_po2_mmhg,
                native_paco2_mmhg=cp.gas.arterial_pco2_mmhg,
                ecmo_flow_ml_min=self.vascular_support.support_flow_ml_min,
                ecmo_return_po2_mmhg=self.vascular_support.return_po2_mmhg,
                ecmo_return_paco2_mmhg=self.vascular_support.return_paco2_mmhg,
                hemoglobin_g_dl=16.5,
            )
            patient_pao2 = mixed.pao2_mmhg
            patient_paco2 = mixed.paco2_mmhg
            patient_sao2 = mixed.sao2_pct

        venous = VenousState(
            preload=VenousPreloadState(
                cvp_mmhg=c.mean_ra_mmhg,
                pleural_delta_mmhg=cp.pleural_delta_mmhg,
                intrathoracic_relative_preload_proxy_mmhg=c.mean_ra_mmhg - cp.pleural_delta_mmhg,
                effective_venous_volume_ml=ledger.effective_venous_volume_ml,
                effective_venous_volume_fraction=ledger.effective_venous_volume_fraction,
            ),
            oxygen=VenousOxygenState(
                native_mixed_venous_po2_mmhg=cp.mixed_venous_po2_mmhg,
                native_mixed_venous_saturation_pct=cp.mixed_venous_saturation_pct,
                native_mixed_venous_oxygen_content_ml_dl=cp.mixed_venous_oxygen_content_ml_dl,
            ),
        )
        return UnifiedPatientSnapshot(
            elapsed_min=self.state.elapsed_min,
            total_blood_volume_ml=tbv,
            blood_volume_fraction=vf,
            effective_venous_volume_ml=ledger.effective_venous_volume_ml,
            effective_venous_volume_fraction=ledger.effective_venous_volume_fraction,
            third_space_volume_ml=ledger.third_space_volume_ml,
            map_mmhg=patient_map,
            systolic_mmhg=patient_systolic,
            diastolic_mmhg=patient_diastolic,
            cvp_mmhg=c.mean_ra_mmhg,
            native_cardiac_output_ml_min=native_output,
            pulmonary_flow_ml_min=c.pulmonary_output_ml_min,
            mean_pa_pressure_mmhg=c.mean_pa_mmhg,
            pao2_mmhg=patient_pao2,
            paco2_mmhg=patient_paco2,
            sao2_pct=patient_sao2,
            respiratory_rate_bpm=cp.lung_metrics.respiratory_rate_bpm,
            tidal_volume_ml=cp.lung_metrics.tidal_volume_ml,
            minute_ventilation_ml_min=cp.lung_metrics.minute_ventilation_ml_min,
            ventilator_mode="pressure_control" if self.airway.pressure_control is not None else "native",
            pvr_multiplier=cp.pvr_multiplier,
            renal_flow_ml_min=k.renal_flow_ml_min,
            renal_perfusion_pressure_mmhg=k.renal_perfusion_pressure_mmhg,
            urine_ml_kg_hr=k.urine_ml_kg_hr,
            cumulative_urine_ml=self.state.cumulative_urine_ml,
            cumulative_net_body_fluid_ml=self.state.cumulative_net_body_fluid_ml,
            vascular_support_enabled=support_enabled,
            vascular_support_flow_ml_min=self.vascular_support.support_flow_ml_min if support_enabled else 0.0,
            venous=venous,
        )

    def _invalidate_native_physiology_cache(self):
        self._physiology_cache_key = None

    def add_intravascular_input(self, volume_ml, *, intravascular_fraction=1.0):
        volume=max(0.0, float(volume_ml)); fraction=max(0.0, min(1.0, float(intravascular_fraction)))
        self.state.volume_ledger.cumulative_input_ml += volume
        delta=volume*fraction
        self.state.volume_ledger.intravascular_delta_ml += delta
        self.state.blood_volume_delta_ml += delta
        if delta > 0.0:
            self._invalidate_native_physiology_cache()

    def record_blood_loss(self, volume_ml):
        volume=max(0.0, float(volume_ml))
        self.state.volume_ledger.cumulative_blood_loss_ml += volume
        self.state.volume_ledger.intravascular_delta_ml -= volume
        self.state.blood_volume_delta_ml -= volume
        if volume > 0.0:
            self._invalidate_native_physiology_cache()

    def record_sampling_loss(self, volume_ml):
        volume=max(0.0, float(volume_ml))
        self.state.volume_ledger.cumulative_sampling_loss_ml += volume
        self.state.volume_ledger.intravascular_delta_ml -= volume
        self.state.blood_volume_delta_ml -= volume
        if volume > 0.0:
            self._invalidate_native_physiology_cache()

    def move_to_third_space(self, volume_ml):
        self.state.volume_ledger.third_space_volume_ml += max(0.0, float(volume_ml))

    def return_from_third_space(self, volume_ml):
        self.state.volume_ledger.third_space_volume_ml=max(0.0, self.state.volume_ledger.third_space_volume_ml-max(0.0, float(volume_ml)))

    def advance(self, dt_min, *, additional_external_fluid_out_ml_min=0.0):
        if dt_min<=0: return self.snapshot()
        before=self.snapshot()
        urine_ml_min=before.urine_ml_kg_hr*self.config.weight_kg/60.0
        fb=update_fluid_balance(self.state.cumulative_net_body_fluid_ml,
            fluid_in_ml_min=self.renal_therapy.fluid_in_ml_min,
            external_fluid_out_ml_min=self.renal_therapy.external_fluid_out_ml_min + max(0.0, additional_external_fluid_out_ml_min),
            urine_ml_min=urine_ml_min,dt_min=dt_min)
        delta=fb.cumulative_net_ml-self.state.cumulative_net_body_fluid_ml
        self.state.cumulative_net_body_fluid_ml=fb.cumulative_net_ml
        iv_delta=delta*max(0,min(1,self.config.intravascular_fraction_of_net_fluid))
        self.state.blood_volume_delta_ml += iv_delta
        self.state.volume_ledger.intravascular_delta_ml += iv_delta
        input_ml=max(0.0, self.renal_therapy.fluid_in_ml_min*dt_min)
        ckrt_ml=max(0.0, (self.renal_therapy.external_fluid_out_ml_min + max(0.0, additional_external_fluid_out_ml_min))*dt_min)
        urine_ml=urine_ml_min*dt_min
        self.state.volume_ledger.cumulative_input_ml += input_ml
        self.state.volume_ledger.cumulative_ckrt_removal_ml += ckrt_ml
        self.state.volume_ledger.cumulative_urine_ml += urine_ml
        self.state.cumulative_urine_ml += urine_ml
        self.state.elapsed_min += dt_min
        baseline=self.volume_config.baseline_blood_volume_ml(self.config.weight_kg)
        minimum=baseline*self.volume_config.minimum_intravascular_fraction
        if baseline+self.state.volume_ledger.intravascular_delta_ml<minimum:
            corrected=minimum-baseline
            self.state.volume_ledger.intravascular_delta_ml=corrected
            self.state.blood_volume_delta_ml=corrected
        return self.snapshot()

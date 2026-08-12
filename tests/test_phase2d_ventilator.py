from __future__ import annotations

import pytest

from neocoupling import run_coupled_neonate
from neogui.ecmo_workspace import EcmoWorkspaceModel
from neolung import LungParameters
from neolung.gas_exchange import GasExchangeParameters
from neopatient import AirwayPort, UnifiedNeonatalPatient, UnifiedPatientConfig
from neopatient.async_native import NativeSolveRequest, solve_native_request
from neoventilator import PressureControlSettings


def _coupled(settings: PressureControlSettings):
    return run_coupled_neonate(
        LungParameters(weight_kg=3.0),
        GasExchangeParameters(weight_kg=3.0, fio2=settings.fio2),
        duration_lung_s=1.0,
        duration_circulation_s=0.2,
        pressure_control=settings,
    )


def test_pressure_control_settings_validate_and_generate_pressure_waveform():
    settings = PressureControlSettings(pip_cmh2o=12, peep_cmh2o=5, rate_bpm=40, inspiratory_time_s=0.35, fio2=0.4)
    assert settings.airway_pressure(0.0) == pytest.approx(5.0)
    assert settings.airway_pressure(0.10) == pytest.approx(12.0)
    assert settings.airway_pressure(0.50) == pytest.approx(5.0)
    assert settings.ie_ratio_text.startswith("1:")

    with pytest.raises(ValueError):
        PressureControlSettings(pip_cmh2o=4, peep_cmh2o=5)
    with pytest.raises(ValueError):
        PressureControlSettings(rate_bpm=100, inspiratory_time_s=0.7)
    with pytest.raises(ValueError):
        PressureControlSettings(fio2=0.10)


def test_pressure_control_drive_changes_real_lung_delivery():
    low = _coupled(PressureControlSettings(pip_cmh2o=8, peep_cmh2o=5, rate_bpm=40, inspiratory_time_s=0.35, fio2=0.4))
    high = _coupled(PressureControlSettings(pip_cmh2o=14, peep_cmh2o=5, rate_bpm=40, inspiratory_time_s=0.35, fio2=0.4))
    assert high.lung_metrics.tidal_volume_ml > low.lung_metrics.tidal_volume_ml
    assert high.lung_metrics.minute_ventilation_ml_min > low.lung_metrics.minute_ventilation_ml_min
    assert high.gas.arterial_pco2_mmhg < low.gas.arterial_pco2_mmhg


def test_pressure_control_rate_is_integrated_not_gui_only():
    slow = _coupled(PressureControlSettings(pip_cmh2o=10, peep_cmh2o=5, rate_bpm=25, inspiratory_time_s=0.35, fio2=0.4))
    fast = _coupled(PressureControlSettings(pip_cmh2o=10, peep_cmh2o=5, rate_bpm=60, inspiratory_time_s=0.30, fio2=0.4))
    assert fast.lung_metrics.respiratory_rate_bpm == pytest.approx(60.0)
    assert slow.lung_metrics.respiratory_rate_bpm == pytest.approx(25.0)
    assert fast.lung_metrics.minute_ventilation_ml_min > slow.lung_metrics.minute_ventilation_ml_min
    assert fast.gas.arterial_pco2_mmhg < slow.gas.arterial_pco2_mmhg


def test_unified_patient_airway_port_owns_pressure_control_and_readback():
    patient = UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=3.0, lung_run_s=1.0, circulation_run_s=0.2))
    settings = PressureControlSettings(pip_cmh2o=10, peep_cmh2o=5, rate_bpm=40, inspiratory_time_s=0.35, fio2=0.4)
    patient.set_airway(AirwayPort(pressure_control=settings, fio2=settings.fio2))
    snapshot = patient.snapshot(include_vascular_support=False)
    assert snapshot.ventilator_mode == "pressure_control"
    assert snapshot.respiratory_rate_bpm == pytest.approx(40.0)
    assert snapshot.tidal_volume_ml > 0.0
    assert snapshot.minute_ventilation_ml_min > 0.0


def test_workspace_ventilator_action_uses_authoritative_airway_and_events():
    model = EcmoWorkspaceModel()
    try:
        settings = PressureControlSettings(pip_cmh2o=10, peep_cmh2o=5, rate_bpm=40, inspiratory_time_s=0.35, fio2=0.4)
        snapshot = model.apply_pressure_control_ventilator(settings)
        assert model.ventilator_settings == settings
        assert model.dynamic.coupled.patient.airway.pressure_control == settings
        event = model.event_records[-1]
        assert event.event_type == "control.changed"
        assert event.target == "ventilator"
        assert event.action == "apply_pressure_control"
        assert event.new_value["rate_bpm"] == pytest.approx(40.0)

        model.remove_pressure_control_ventilator()
        assert model.ventilator_settings is None
        assert model.event_records[-1].action == "remove_pressure_control"
    finally:
        model.close()


def test_pressure_control_fio2_reaches_coupled_gas_exchange():
    low = _coupled(PressureControlSettings(pip_cmh2o=10, peep_cmh2o=5, rate_bpm=40, inspiratory_time_s=0.35, fio2=0.21))
    high = _coupled(PressureControlSettings(pip_cmh2o=10, peep_cmh2o=5, rate_bpm=40, inspiratory_time_s=0.35, fio2=0.60))
    assert high.gas.arterial_po2_mmhg > low.gas.arterial_po2_mmhg


def test_spawn_worker_request_reconstructs_pressure_control_from_primitive_cache_key():
    patient = UnifiedNeonatalPatient(UnifiedPatientConfig(weight_kg=3.0, lung_run_s=1.0, circulation_run_s=0.2))
    settings = PressureControlSettings(pip_cmh2o=10, peep_cmh2o=5, rate_bpm=45, inspiratory_time_s=0.32, fio2=0.35)
    patient.set_airway(AirwayPort(pressure_control=settings, fio2=settings.fio2))
    request = NativeSolveRequest(revision=7, cache_key=patient._native_cache_key(), blood_volume_delta_ml=0.0)
    result = solve_native_request(request)
    assert result.revision == 7
    assert result.physiology.lung_metrics.respiratory_rate_bpm == pytest.approx(45.0)
    assert result.physiology.gas.fio2 == pytest.approx(0.35)

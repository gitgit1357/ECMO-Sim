from __future__ import annotations

import numpy as np

from neocirculation import TARGETS, build_normal_term_neonate, calculate_baseline_metrics


def test_total_blood_volume_matches_reference_patient() -> None:
    model = build_normal_term_neonate()
    assert abs(model.total_blood_volume_ml - TARGETS.total_blood_volume_ml) < 1e-9


def test_closed_loop_conserves_volume() -> None:
    model = build_normal_term_neonate()
    result = model.simulate(duration_s=10.0, sample_hz=100.0)
    totals = np.sum(result.volumes_ml, axis=0)
    assert np.max(np.abs(totals - totals[0])) < 1e-6


def test_no_compartment_becomes_nonphysical() -> None:
    model = build_normal_term_neonate()
    result = model.simulate(duration_s=10.0, sample_hz=100.0)
    assert float(np.min(result.volumes_ml)) > 0.0


def test_baseline_produces_pulsatile_forward_flow() -> None:
    model = build_normal_term_neonate()
    result = model.simulate(duration_s=20.0, sample_hz=200.0)
    metrics = calculate_baseline_metrics(result, TARGETS.heart_rate_bpm)
    assert metrics.systolic_aortic_mmhg > metrics.diastolic_aortic_mmhg
    assert metrics.native_output_ml_min > 0
    assert metrics.pulmonary_output_ml_min > 0


def test_calibrated_baseline_is_within_reference_tolerances() -> None:
    model = build_normal_term_neonate()
    result = model.simulate(duration_s=30.0, sample_hz=150.0)
    metrics = calculate_baseline_metrics(result, TARGETS.heart_rate_bpm)
    assert 65.0 <= metrics.systolic_aortic_mmhg <= 75.0
    assert 37.0 <= metrics.diastolic_aortic_mmhg <= 45.0
    assert 48.0 <= metrics.mean_aortic_mmhg <= 55.0
    assert 740.0 <= metrics.native_output_ml_min <= 850.0
    assert 14.0 <= metrics.mean_pa_mmhg <= 21.0
    assert 2.0 <= metrics.mean_ra_mmhg <= 6.0


def test_monitor_adapter_is_read_only_and_display_neutral() -> None:
    from neocirculation import ResultTelemetryAdapter

    model = build_normal_term_neonate()
    result = model.simulate(duration_s=1.0, sample_hz=20.0)
    original_end = result.volumes_ml[:, -1].copy()
    frames = list(ResultTelemetryAdapter(result, TARGETS.heart_rate_bpm).frames())
    assert len(frames) == len(result.time_s)
    assert "aortic_pressure_mmhg" in frames[-1].values
    assert np.array_equal(original_end, result.volumes_ml[:, -1])


def test_rolling_telemetry_uses_completed_seconds_and_fixed_window() -> None:
    from neocirculation import MonitorFrame, RollingTelemetryAverager

    raw = []
    # Twenty seconds at two samples per second. Each second has a deliberately
    # distinct pressure/output level so the trailing-window calculation is exact.
    for second in range(20):
        for offset, ao in ((0.0, 40.0 + second), (0.5, 70.0 + second)):
            raw.append(
                MonitorFrame(
                    time_s=second + offset,
                    values={
                        "heart_rate_bpm": 130.0,
                        "aortic_pressure_mmhg": ao,
                        "pulmonary_pressure_mmhg": 10.0 + second,
                        "right_atrial_pressure_mmhg": 3.0 + second / 10.0,
                        "left_atrial_pressure_mmhg": 5.0,
                        "native_output_ml_min": 700.0 + second,
                        "pulmonary_output_ml_min": 700.0 + second,
                        "lv_volume_ml": 10.0,
                        "rv_volume_ml": 10.0,
                    },
                )
            )

    output = list(RollingTelemetryAverager(raw, window_seconds=15).frames())
    # At t=19.0, seconds 4 through 18 are the fifteen completed seconds.
    frame = next(item for item in output if item.time_s == 19.0)
    assert frame.values["rolling_window_seconds"] == 15.0
    assert abs(frame.values["arterial_systolic_mmhg"] - np.mean([70.0 + i for i in range(4, 19)])) < 1e-9
    assert abs(frame.values["arterial_diastolic_mmhg"] - np.mean([40.0 + i for i in range(4, 19)])) < 1e-9
    assert abs(frame.values["display_native_output_ml_min"] - np.mean([700.0 + i for i in range(4, 19)])) < 1e-9


def test_rolling_telemetry_preserves_raw_waveform_samples() -> None:
    from neocirculation import MonitorFrame, RollingTelemetryAverager

    raw = [
        MonitorFrame(
            time_s=t,
            values={
                "heart_rate_bpm": 130.0,
                "aortic_pressure_mmhg": value,
                "pulmonary_pressure_mmhg": 17.0,
                "right_atrial_pressure_mmhg": 4.0,
                "left_atrial_pressure_mmhg": 6.0,
                "native_output_ml_min": 800.0,
                "pulmonary_output_ml_min": 800.0,
                "lv_volume_ml": 10.0,
                "rv_volume_ml": 10.0,
            },
        )
        for t, value in ((0.0, 42.0), (0.5, 69.0), (1.0, 43.0))
    ]
    output = list(RollingTelemetryAverager(raw).frames())
    assert [frame.values["aortic_pressure_mmhg"] for frame in output] == [42.0, 69.0, 43.0]


def test_parameter_registry_distinguishes_targets_from_calibration() -> None:
    from neocirculation import BASELINE_PARAMETER_REGISTRY, ParameterClass

    records = BASELINE_PARAMETER_REGISTRY.records()
    assert records["heart_rate_bpm"].classification == ParameterClass.OBSERVED_TARGET
    assert records["systemic_resistance_scale"].classification == ParameterClass.CALIBRATED


def test_modified_patient_is_a_fresh_independent_model() -> None:
    from neocirculation import PatientModifiers, build_modified_neonate

    baseline = build_normal_term_neonate()
    modified = build_modified_neonate(PatientModifiers(blood_volume_scale=0.90))
    assert baseline is not modified
    assert baseline.total_blood_volume_ml == TARGETS.total_blood_volume_ml
    assert abs(modified.total_blood_volume_ml - TARGETS.total_blood_volume_ml * 0.90) < 1e-9


def test_volume_and_resistance_perturbations_move_in_expected_direction() -> None:
    from neocirculation import run_perturbation_suite

    reports = run_perturbation_suite(duration_s=20.0, sample_hz=80.0)
    baseline = reports["baseline"].metrics
    assert reports["hypovolemia_10pct"].metrics.mean_aortic_mmhg < baseline.mean_aortic_mmhg
    assert reports["hypervolemia_10pct"].metrics.mean_aortic_mmhg > baseline.mean_aortic_mmhg
    assert reports["svr_up_25pct"].metrics.mean_aortic_mmhg > baseline.mean_aortic_mmhg
    assert reports["svr_down_25pct"].metrics.mean_aortic_mmhg < baseline.mean_aortic_mmhg
    assert reports["pvr_up_50pct"].metrics.mean_pa_mmhg > baseline.mean_pa_mmhg


def test_two_minute_accelerated_run_has_no_material_drift() -> None:
    from neocirculation import calculate_drift

    model = build_normal_term_neonate()
    result = model.simulate(duration_s=120.0, sample_hz=10.0)
    drift = calculate_drift(result)
    assert drift["total_volume_range_ml"] < 1e-5
    assert abs(drift["aortic_mean_shift_mmhg"]) < 0.2
    assert abs(drift["ra_mean_shift_mmhg"]) < 0.1
    assert abs(drift["lv_volume_mean_shift_ml"]) < 0.05
    assert abs(drift["rv_volume_mean_shift_ml"]) < 0.05


def test_failure_profiles_are_directionally_distinct():
    from neocirculation.failure import run_failure_suite
    p = run_failure_suite(duration_s=20.0, sample_hz=60.0)
    base = p["baseline"].metrics
    lv = p["lv_severe"]
    rv = p["rv_severe"]
    assert lv.metrics.native_output_ml_min < base.native_output_ml_min * 0.75
    assert lv.metrics.mean_la_mmhg > base.mean_la_mmhg + 2.0
    assert lv.lv_peak_volume_ml > p["baseline"].lv_peak_volume_ml + 4.0
    assert rv.metrics.native_output_ml_min < base.native_output_ml_min * 0.75
    assert rv.metrics.mean_ra_mmhg > base.mean_ra_mmhg + 1.0
    assert rv.metrics.mean_pa_mmhg < base.mean_pa_mmhg
    assert rv.rv_peak_volume_ml > p["baseline"].rv_peak_volume_ml + 4.0


def test_recovery_returns_toward_baseline_without_reset():
    from neocirculation.failure import run_recovery_sequence
    for side in ("lv", "rv"):
        r = run_recovery_sequence(side, failure_scale=0.20, phase_s=12.0, sample_hz=60.0)
        baseline, failure, recovery = r["baseline"], r["failure"], r["recovery"]
        assert abs(recovery.mean_aortic_mmhg - baseline.mean_aortic_mmhg) < abs(failure.mean_aortic_mmhg - baseline.mean_aortic_mmhg)
        assert abs(recovery.native_output_ml_min - baseline.native_output_ml_min) < abs(failure.native_output_ml_min - baseline.native_output_ml_min)


def test_pressure_volume_extraction_is_read_only_and_nonempty():
    from neocirculation import build_normal_term_neonate, TARGETS
    from neocirculation.pv import extract_pressure_volume_loop
    model = build_normal_term_neonate()
    result = model.simulate(5.0, 60.0)
    before = result.node_series("LV").copy()
    loop = extract_pressure_volume_loop(result, "LV", TARGETS.heart_rate_bpm, beats=2)
    assert len(loop.volume_ml) > 10
    assert len(loop.volume_ml) == len(loop.pressure_mmhg)
    assert np.array_equal(before, result.node_series("LV"))


def test_preload_extraction_bench_reduces_native_rv_flow_monotonically():
    from neocirculation.pump_bench import run_preload_extraction_bench
    points = run_preload_extraction_bench((0, 50, 100, 150, 200), stabilization_s=10.0, extraction_s=2.0, sample_hz=80.0)
    rv = [p.native_rv_output_ml_min for p in points]
    assert all(a > b for a, b in zip(rv, rv[1:]))


def test_preload_extraction_preserves_initial_lv_buffering():
    from neocirculation.pump_bench import run_preload_extraction_bench
    points = run_preload_extraction_bench((0, 200), stabilization_s=10.0, extraction_s=2.0, sample_hz=80.0)
    baseline, high = points
    rv_drop = baseline.native_rv_output_ml_min - high.native_rv_output_ml_min
    lv_drop = baseline.native_lv_output_ml_min - high.native_lv_output_ml_min
    assert rv_drop > lv_drop


def test_closed_loop_va_ecmo_conserves_patient_blood_volume():
    from neocirculation.va_ecmo_bench import run_closed_loop_va_ecmo_bench
    points = run_closed_loop_va_ecmo_bench((0, 100, 200), stabilization_s=8.0, support_s=4.0, sample_hz=60.0)
    assert max(abs(p.volume_conservation_error_ml) for p in points) < 1e-5


def test_closed_loop_va_ecmo_progressively_reduces_native_rv_contribution():
    from neocirculation.va_ecmo_bench import run_closed_loop_va_ecmo_bench
    points = run_closed_loop_va_ecmo_bench((0, 50, 100, 150, 200), stabilization_s=8.0, support_s=5.0, sample_hz=60.0)
    rv = [p.native_rv_output_ml_min for p in points]
    assert all(a > b for a, b in zip(rv, rv[1:]))
    assert points[-1].circuit_fraction_of_aortic_inflow > points[1].circuit_fraction_of_aortic_inflow


def test_closed_loop_va_ecmo_preserves_intrinsic_contractility_but_changes_loading():
    from neocirculation.va_ecmo_bench import run_closed_loop_va_ecmo_bench
    baseline, high = run_closed_loop_va_ecmo_bench((0, 200), stabilization_s=8.0, support_s=5.0, sample_hz=60.0)
    assert high.mean_ra_pressure_mmhg < baseline.mean_ra_pressure_mmhg
    assert high.native_lv_output_ml_min < baseline.native_lv_output_ml_min
    assert high.mean_aortic_mmhg > baseline.mean_aortic_mmhg

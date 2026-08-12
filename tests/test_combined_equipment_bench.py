from neocoupling.equipment_bench import run_combined_equipment_bench


def _by_id(points):
    return {p.scenario_id:p for p in points}


def test_combined_equipment_expected_directional_behavior():
    p=_by_id(run_combined_equipment_bench())
    assert p['vent_ref_ecmo_200'].circuit_fraction > p['vent_ref_ecmo_100'].circuit_fraction > p['vent_ref_ecmo_0'].circuit_fraction
    assert p['vent_ref_ecmo_200'].native_lv_output_ml_min < p['vent_ref_ecmo_100'].native_lv_output_ml_min < p['vent_ref_ecmo_0'].native_lv_output_ml_min
    assert p['vent_ref_ecmo_200'].pulse_pressure_mmhg < p['vent_ref_ecmo_0'].pulse_pressure_mmhg
    assert p['high_peep_ecmo_0'].native_lv_output_ml_min < p['vent_ref_ecmo_0'].native_lv_output_ml_min
    assert p['low_vent_ecmo_0'].paco2_mmhg > p['vent_ref_ecmo_0'].paco2_mmhg
    assert p['low_vent_ecmo_200'].effective_systemic_sao2_pct > p['low_vent_ecmo_0'].effective_systemic_sao2_pct
    assert abs(p['vent_ref_ecmo_200'].volume_conservation_error_ml) < 1e-4

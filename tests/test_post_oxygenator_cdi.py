import pytest

from neoecmo import (
    PostOxygenatorBloodState,
    PostOxyCdiSensorState,
    measure_post_oxygenator_blood,
    outlet_po2_mmhg,
    po2_from_saturation_mmhg,
    run_ecmo_console,
    EcmoConsoleControls,
)


def test_po2_conversion_increases_with_saturation():
    assert po2_from_saturation_mmhg(0.99) > po2_from_saturation_mmhg(0.90)


def test_oxygenator_exposes_explicit_post_oxy_po2():
    po2 = outlet_po2_mmhg(0.65, 400.0, 1.0)
    assert po2 > 0.0


def test_post_oxy_cdi_reads_true_blood_when_valid():
    blood = PostOxygenatorBloodState(300.0, 32.0, 0.99, 39.0, 13.0, 36.8)
    reading = measure_post_oxygenator_blood(blood)
    assert reading.valid
    assert reading.po2_mmhg == pytest.approx(300.0)
    assert reading.pco2_mmhg == pytest.approx(32.0)
    assert reading.oxygen_saturation == pytest.approx(0.99)


def test_post_oxy_cdi_can_be_invalid_without_erasing_truth():
    blood = PostOxygenatorBloodState(300.0, 32.0, 0.99, 39.0, 13.0, 36.8)
    reading = measure_post_oxygenator_blood(blood, PostOxyCdiSensorState(valid=False))
    assert not reading.valid
    assert reading.po2_mmhg is None
    assert blood.po2_mmhg == 300.0


def test_console_keeps_post_oxy_truth_and_sensor_separate():
    state = run_ecmo_console(
        EcmoConsoleControls(rpm=3000.0, sweep_gas_flow_ml_min=600.0),
        native_venous_saturation=0.65,
        native_venous_paco2_mmhg=55.0,
    )
    assert state.post_oxygenator_po2_mmhg == pytest.approx(state.post_oxygenator_blood.po2_mmhg)
    assert state.post_oxygenator_cdi.po2_mmhg == pytest.approx(state.post_oxygenator_po2_mmhg)
    assert state.post_oxygenator_cdi.pco2_mmhg == pytest.approx(state.post_oxygenator_paco2_mmhg)


def test_post_oxy_po2_responds_to_fdo2():
    low = outlet_po2_mmhg(0.65, 400.0, 0.21)
    high = outlet_po2_mmhg(0.65, 400.0, 1.0)
    assert high > low

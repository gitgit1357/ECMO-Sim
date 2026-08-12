import json
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls, ShuntLineConfiguration
from neoecmocoupling import PatientToEcmoState, solve_closed_loop_va_ecmo

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "fixed_shunt_configuration_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _patient(c):
    p = c["preconditions"]
    return PatientToEcmoState(
        weight_kg=float(p["weight_kg"]),
        venous_pressure_mmhg=float(p["cvp_mmhg"]),
        arterial_pressure_mmhg=float(p["baseline_map_mmhg"]),
        blood_volume_fraction=1.0,
        native_cardiac_output_ml_min=float(p["native_cardiac_output_ml_min"]),
        native_venous_oxygen_saturation=float(p["native_venous_saturation"]),
        native_venous_paco2_mmhg=float(p["native_venous_paco2_mmhg"]),
    )


def _run(c, configuration, *, scuffing_active=False):
    p = c["preconditions"]
    return solve_closed_loop_va_ecmo(
        EcmoConsoleControls(
            rpm=float(p["rpm"]),
            shunt_configuration=configuration,
            shunt_scuffing_active=scuffing_active,
            sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
            fdo2=float(p["fdo2"]),
        ),
        _patient(c),
    )


def test_contract_definition_preserves_blocked_fluid_removal_boundary():
    c = _contract()
    assert c["contract_id"] == "cbc.ecmo.fixed-shunt-configuration.v1"
    assert c["clinical_review_status"] == "expert-review-pending"
    assert any("coupled patient" in item for item in c["blocked_behavior"])
    assert any("volume ledger" in item for item in c["future_retest_conditions"])


def test_inline_hemofilter_reduces_shunt_diversion_and_redistributes_to_patient():
    c = _contract()
    open_state = _run(c, ShuntLineConfiguration.OPEN)
    hemo_state = _run(c, ShuntLineConfiguration.HEMOFILTER)
    o = open_state.ecmo_state.circuit
    h = hemo_state.ecmo_state.circuit
    assert h.solved_shunt_flow_ml_min < o.solved_shunt_flow_ml_min
    assert h.shunt_fraction < o.shunt_fraction
    assert h.solved_patient_flow_ml_min > o.solved_patient_flow_ml_min
    assert hemo_state.settled_map_mmhg >= open_state.settled_map_mmhg


def test_scuffing_activity_does_not_change_hemofilter_hydraulics():
    c = _contract()
    inactive = _run(c, ShuntLineConfiguration.HEMOFILTER, scuffing_active=False)
    active = _run(c, ShuntLineConfiguration.HEMOFILTER, scuffing_active=True)
    for field in (
        "solved_total_flow_ml_min",
        "solved_shunt_flow_ml_min",
        "solved_patient_flow_ml_min",
        "shunt_fraction",
        "p1_mmhg",
        "p2_mmhg",
        "p3_mmhg",
    ):
        assert getattr(active.ecmo_state.circuit, field) == pytest.approx(getattr(inactive.ecmo_state.circuit, field))
    assert active.settled_map_mmhg == pytest.approx(inactive.settled_map_mmhg)


def test_ckrt_configuration_is_hydraulically_equivalent_to_open():
    c = _contract()
    tol = float(c["tolerances"]["hydraulic_equivalence_absolute_ml_min"])
    open_state = _run(c, ShuntLineConfiguration.OPEN)
    ckrt_state = _run(c, ShuntLineConfiguration.CKRT)
    for field in (
        "solved_total_flow_ml_min",
        "solved_shunt_flow_ml_min",
        "solved_patient_flow_ml_min",
        "shunt_fraction",
        "p1_mmhg",
        "p2_mmhg",
        "p3_mmhg",
    ):
        assert getattr(ckrt_state.ecmo_state.circuit, field) == pytest.approx(
            getattr(open_state.ecmo_state.circuit, field), abs=tol
        )
    assert ckrt_state.settled_map_mmhg == pytest.approx(open_state.settled_map_mmhg)


def test_branch_conservation_and_open_restoration():
    c = _contract()
    tol = float(c["tolerances"]["branch_conservation_absolute_ml_min"])
    baseline = _run(c, ShuntLineConfiguration.OPEN)
    _ = _run(c, ShuntLineConfiguration.HEMOFILTER, scuffing_active=True)
    restored = _run(c, ShuntLineConfiguration.OPEN)
    for state in (baseline, restored):
        p = state.ecmo_state.circuit
        assert p.solved_total_flow_ml_min == pytest.approx(
            p.solved_patient_flow_ml_min + p.solved_shunt_flow_ml_min + p.solved_bridge_flow_ml_min,
            abs=tol,
        )
    assert restored.ecmo_state.circuit.solved_patient_flow_ml_min == pytest.approx(
        baseline.ecmo_state.circuit.solved_patient_flow_ml_min
    )
    assert restored.settled_map_mmhg == pytest.approx(baseline.settled_map_mmhg)

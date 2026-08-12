import json
from pathlib import Path

import pytest

from neoecmo import EcmoConsoleControls
from neoecmocoupling import CoupledVaEcmoPatient, patient_boundary_from_snapshot
from neopatient import UnifiedNeonatalPatient


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "clinical_behavior_contracts" / "fdo2_oxygen_fraction_control_v1.json"


def _controls(fdo2: float) -> EcmoConsoleControls:
    return EcmoConsoleControls(
        rpm=3000.0,
        sweep_gas_flow_ml_min=600.0,
        fdo2=fdo2,
    )


def test_phase10b_true_venous_inlet_is_canonical_patient_boundary_source():
    patient = UnifiedNeonatalPatient()
    native = patient.snapshot(include_vascular_support=False)
    boundary = patient_boundary_from_snapshot(native, weight_kg=patient.config.weight_kg)

    assert boundary.native_venous_oxygen_saturation == pytest.approx(
        native.venous.oxygen.native_mixed_venous_saturation_pct / 100.0
    )
    assert boundary.native_venous_oxygen_saturation != pytest.approx(native.sao2_pct / 100.0)


def test_phase10b_lower_fdo2_monotonically_lowers_return_and_coupled_patient_oxygenation():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    patient = UnifiedNeonatalPatient()
    coupled = CoupledVaEcmoPatient(patient, _controls(1.0))

    post_oxy_po2 = []
    patient_pao2 = []
    patient_flow = []
    native_venous_sat = []

    for fdo2 in contract["preconditions"]["graded_probe_fdo2"]:
        coupled.set_controls(_controls(float(fdo2)))
        snap = coupled.snapshot()
        post_oxy_po2.append(snap.delivery.return_po2_mmhg)
        patient_pao2.append(snap.patient.pao2_mmhg)
        patient_flow.append(snap.delivery.ecmo_return_flow_ml_min)
        native_venous_sat.append(
            snap.native_patient.venous.oxygen.native_mixed_venous_saturation_pct
        )

    assert all(a > b for a, b in zip(post_oxy_po2, post_oxy_po2[1:]))
    assert all(a > b for a, b in zip(patient_pao2, patient_pao2[1:]))
    assert max(native_venous_sat) - min(native_venous_sat) < 1e-9

    flow_rel = float(contract["tolerances"]["flow_relative"])
    baseline_flow = patient_flow[0]
    for flow in patient_flow[1:]:
        assert flow == pytest.approx(baseline_flow, rel=flow_rel)


def test_phase10b_fdo2_only_change_preserves_coupled_patient_co2_with_fixed_sweep():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    patient = UnifiedNeonatalPatient()
    coupled = CoupledVaEcmoPatient(patient, _controls(1.0))

    paco2 = []
    for fdo2 in contract["preconditions"]["graded_probe_fdo2"]:
        coupled.set_controls(_controls(float(fdo2)))
        paco2.append(coupled.snapshot().patient.paco2_mmhg)

    tol = float(contract["tolerances"]["paco2_absolute_mmhg"])
    for value in paco2[1:]:
        assert value == pytest.approx(paco2[0], abs=tol)


def test_phase10b_same_runtime_fdo2_restoration_is_reversible():
    patient = UnifiedNeonatalPatient()
    coupled = CoupledVaEcmoPatient(patient, _controls(1.0))

    baseline = coupled.snapshot()
    coupled.set_controls(_controls(0.21))
    low = coupled.snapshot()
    coupled.set_controls(_controls(1.0))
    restored = coupled.snapshot()

    assert low.delivery.return_po2_mmhg < baseline.delivery.return_po2_mmhg
    assert low.patient.pao2_mmhg < baseline.patient.pao2_mmhg
    assert restored.delivery.return_po2_mmhg == pytest.approx(baseline.delivery.return_po2_mmhg)
    assert restored.patient.pao2_mmhg == pytest.approx(baseline.patient.pao2_mmhg)
    assert restored.patient.sao2_pct == pytest.approx(baseline.patient.sao2_pct)
    assert restored.delivery.ecmo_return_flow_ml_min == pytest.approx(
        baseline.delivery.ecmo_return_flow_ml_min
    )


def test_phase10b_contract_and_capability_matrix_no_longer_claim_coupled_path_is_blocked():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    expected = contract["expected_behavior"]
    assert any("coupled-patient" in item for item in expected)
    assert not any("arterial saturation as a venous surrogate" in item for item in contract["not_modeled"])

    matrix = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text(encoding="utf-8"))
    row = next(
        r for r in matrix["rows"]
        if r["Feature"] == "FdO2-to-coupled-patient oxygenation via true venous inlet state"
    )
    assert row["Implemented"] == "Y"
    assert row["Integrated"] == "Y"
    assert row["Learner-operable"] == "Y"
    assert "BLOCKED" not in row["Clinical/behavior validation"]
    assert "Phase 10b" in row["Fresh verification"]

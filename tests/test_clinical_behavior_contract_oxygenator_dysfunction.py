import json
from pathlib import Path

import pytest

from neoecmo import (
    EcmoConsoleControls,
    OxygenatorGasExchangeParameters,
    OxygenatorHydraulicParameters,
    outlet_o2_saturation,
    outlet_paco2_mmhg,
    outlet_po2_mmhg,
    run_ecmo_console,
)

CONTRACT_PATH = Path(__file__).parents[1] / "clinical_behavior_contracts" / "oxygenator_dysfunction_v1.json"


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _hydraulic_console(contract, obstruction):
    p = contract["hydraulic_branch"]["preconditions"]
    return run_ecmo_console(
        EcmoConsoleControls(
            rpm=float(p["rpm"]),
            sweep_gas_flow_ml_min=float(p["sweep_gas_flow_ml_min"]),
            fdo2=float(p["fdo2"]),
            bridge_clamp_position=float(p["bridge_clamp_position"]),
        ),
        native_venous_saturation=float(p["representative_inlet_venous_saturation"]),
        native_venous_paco2_mmhg=float(p["representative_inlet_paco2_mmhg"]),
        oxygenator_hydraulic_params=OxygenatorHydraulicParameters(
            obstruction_fraction=float(obstruction)
        ),
    )


def _gas_outputs(contract, obstruction):
    p = contract["gas_transfer_branch"]["preconditions"]
    params = OxygenatorGasExchangeParameters(obstruction_fraction=float(obstruction))
    flow = float(p["blood_flow_ml_min"])
    inlet_sat = float(p["inlet_saturation"])
    inlet_paco2 = float(p["inlet_paco2_mmhg"])
    fdo2 = float(p["fdo2"])
    sweep = float(p["sweep_gas_flow_ml_min"])
    return {
        "sat": outlet_o2_saturation(inlet_sat, flow, fdo2, params),
        "po2": outlet_po2_mmhg(inlet_sat, flow, fdo2, params),
        "paco2": outlet_paco2_mmhg(inlet_paco2, flow, sweep, float(obstruction)),
    }


def test_contract_definition_keeps_hydraulic_and_gas_failure_branches_separate():
    contract = _contract()
    assert contract["contract_id"] == "cbc.ecmo.oxygenator-dysfunction.v1"
    assert contract["status"] == "automated-behavior-contract"
    assert contract["clinical_review_status"] == "expert-review-pending"
    assert contract["hydraulic_branch"]
    assert contract["gas_transfer_branch"]
    assert any("no universal" in item for item in contract["explicit_non_rules"])


def test_hydraulic_obstruction_raises_oxygenator_delta_p_and_reduces_flow_at_fixed_rpm():
    contract = _contract()
    p = contract["hydraulic_branch"]["preconditions"]
    stimulus = contract["hydraulic_branch"]["stimulus"]

    clean = _hydraulic_console(contract, p["baseline_obstruction_fraction"])
    obstructed = _hydraulic_console(contract, stimulus["obstruction_fraction"])

    assert obstructed.circuit.oxygenator_delta_p_mmhg > clean.circuit.oxygenator_delta_p_mmhg
    assert obstructed.circuit.solved_total_flow_ml_min < clean.circuit.solved_total_flow_ml_min
    assert obstructed.circuit.solved_patient_flow_ml_min < clean.circuit.solved_patient_flow_ml_min


def test_hydraulic_restoration_returns_operating_point_to_clean_baseline():
    contract = _contract()
    p = contract["hydraulic_branch"]["preconditions"]
    tol = float(contract["tolerances"]["restoration_relative"])

    clean = _hydraulic_console(contract, p["baseline_obstruction_fraction"])
    _hydraulic_console(contract, contract["hydraulic_branch"]["stimulus"]["obstruction_fraction"])
    restored = _hydraulic_console(contract, p["baseline_obstruction_fraction"])

    assert restored.circuit.oxygenator_delta_p_mmhg == pytest.approx(
        clean.circuit.oxygenator_delta_p_mmhg, rel=tol
    )
    assert restored.circuit.solved_total_flow_ml_min == pytest.approx(
        clean.circuit.solved_total_flow_ml_min, rel=tol
    )
    assert restored.circuit.solved_patient_flow_ml_min == pytest.approx(
        clean.circuit.solved_patient_flow_ml_min, rel=tol
    )


def test_membrane_transfer_impairment_reduces_o2_transfer_and_co2_clearance_at_fixed_flow():
    contract = _contract()
    p = contract["gas_transfer_branch"]["preconditions"]
    obstruction = contract["gas_transfer_branch"]["stimulus"]["obstruction_fraction"]

    clean = _gas_outputs(contract, p["baseline_obstruction_fraction"])
    impaired = _gas_outputs(contract, obstruction)

    assert impaired["sat"] < clean["sat"]
    assert impaired["po2"] < clean["po2"]
    assert impaired["paco2"] > clean["paco2"]


def test_membrane_transfer_restoration_returns_outputs_to_clean_baseline():
    contract = _contract()
    p = contract["gas_transfer_branch"]["preconditions"]
    tol = float(contract["tolerances"]["restoration_relative"])

    clean = _gas_outputs(contract, p["baseline_obstruction_fraction"])
    _gas_outputs(contract, contract["gas_transfer_branch"]["stimulus"]["obstruction_fraction"])
    restored = _gas_outputs(contract, p["baseline_obstruction_fraction"])

    assert restored["sat"] == pytest.approx(clean["sat"], rel=tol)
    assert restored["po2"] == pytest.approx(clean["po2"], rel=tol)
    assert restored["paco2"] == pytest.approx(clean["paco2"], rel=tol)

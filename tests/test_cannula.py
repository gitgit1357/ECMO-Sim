from pathlib import Path

import pytest

from neoecmo import (
    DRAIN_10FR,
    RETURN_8FR,
    cannula_delta_p_mmhg,
    resistance_coefficient_from_datapoint,
    run_cannula_hydraulic_bench,
)

ROOT = Path(__file__).resolve().parents[1]


# --- basic hydraulics --------------------------------------------------


def test_zero_flow_gives_zero_delta_p():
    assert cannula_delta_p_mmhg(0.0, RETURN_8FR) == 0.0


def test_delta_p_increases_with_flow():
    deltas = [cannula_delta_p_mmhg(flow, RETURN_8FR) for flow in (0, 200, 400, 600, 800)]
    assert deltas == sorted(deltas)
    assert deltas[0] < deltas[-1]


def test_reversed_flow_gives_negative_delta_p():
    assert cannula_delta_p_mmhg(-400.0, RETURN_8FR) < 0.0
    assert cannula_delta_p_mmhg(-400.0, RETURN_8FR) == pytest.approx(
        -cannula_delta_p_mmhg(400.0, RETURN_8FR)
    )


# --- larger cannula = lower resistance at the same flow --------------------


def test_larger_drain_cannula_has_lower_resistance_than_smaller_return_cannula():
    flow = 400.0
    assert cannula_delta_p_mmhg(flow, DRAIN_10FR) < cannula_delta_p_mmhg(flow, RETURN_8FR)


# --- round-trip validation against the source literature data points ------


def test_return_8fr_default_reproduces_source_literature_datapoint():
    # Medtronic DLP 8Fr arterial cannula: ~600 mL/min at ~100 mmHg (PMC10655309)
    delta_p = cannula_delta_p_mmhg(600.0, RETURN_8FR)
    assert delta_p == pytest.approx(100.0, rel=0.01)


def test_drain_10fr_default_reproduces_source_literature_datapoint():
    # Medtronic DLP 10Fr arterial cannula: ~1100 mL/min at ~100 mmHg (PMC10655309)
    # (used as a placeholder for the drain/venous cannula — see docstring)
    delta_p = cannula_delta_p_mmhg(1100.0, DRAIN_10FR)
    assert delta_p == pytest.approx(100.0, rel=0.01)


def test_resistance_coefficient_from_datapoint_matches_return_8fr_default():
    k = resistance_coefficient_from_datapoint(delta_p_mmhg=100.0, flow_ml_min=600.0)
    assert k == pytest.approx(RETURN_8FR.quadratic_resistance_mmhg_per_ml_min2, rel=1e-3)


def test_resistance_coefficient_from_datapoint_rejects_nonpositive_flow():
    with pytest.raises(ValueError):
        resistance_coefficient_from_datapoint(delta_p_mmhg=100.0, flow_ml_min=0.0)


# --- bench sanity -----------------------------------------------------------


def test_bench_sweep_returns_one_point_per_flow_step():
    steps = (0, 200, 400, 600)
    points = run_cannula_hydraulic_bench(flow_steps_ml_min=steps)
    assert [p.flow_ml_min for p in points] == [float(s) for s in steps]
    assert points[0].delta_p_mmhg == 0.0


# --- module boundary ---------------------------------------------------------


def test_cannula_module_does_not_import_patient_physiology_modules():
    forbidden = ("neocirculation", "neolung", "neokidney", "neocoupling", "neopatient")
    for filename in ("cannula.py", "cannula_bench.py"):
        text = (ROOT / "src" / "neoecmo" / filename).read_text(encoding="utf-8")
        for name in forbidden:
            assert f"import {name}" not in text
            assert f"from {name}" not in text

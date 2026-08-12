from dataclasses import replace
from pathlib import Path

from neogui import learner_patient_reading
from neogui.ecmo_workspace import EcmoWorkspace


OWNED_INLINE_READS = (
    "displayed.map_mmhg",
    "displayed.patient_flow_ml_min",
    "displayed.sao2_pct",
    "displayed.pao2_mmhg",
    "displayed.paco2_mmhg",
)


def test_phase6_6a_static_guard_blocks_duplicate_inline_learner_projection_reads():
    source = Path("src/neogui/ecmo_workspace.py").read_text(encoding="utf-8")
    for forbidden in OWNED_INLINE_READS:
        assert forbidden not in source


def test_phase6_6a_live_tk_console_monitor_and_ribbon_share_one_projection_contract():
    app = EcmoWorkspace()
    try:
        snapshot = app.model.solve()
        baseline = learner_patient_reading(snapshot, physiology_updating=False)
        calls = []

        def spy(snap, *, physiology_updating=False):
            calls.append((snap, physiology_updating))
            return replace(
                baseline,
                map_mmhg=88.0,
                spo2_pct=77.7,
                ecmo_patient_flow_ml_min=1234.0,
                pao2_mmhg=66.0,
                paco2_mmhg=44.0,
                physiology_updating=physiology_updating,
            )

        app._learner_patient_project = spy
        app._patient_monitor_project = spy
        app._apply_snapshot(snapshot)
        app.root.update_idletasks()

        assert len(calls) == 1
        assert app.telemetry_tiles["map"].value.cget("text") == "88"
        assert app.telemetry_tiles["patient"].value.cget("text") == "1.234"
        assert app.patient_monitor_tiles["map"].value.cget("text") == "88 mmHg"
        assert app.patient_monitor_tiles["ecmo_flow"].value.cget("text") == "1.234 L/min"
        assert app.status_ribbon_labels["map"].cget("text") == "88 mmHg"
        assert app.status_ribbon_labels["spo2"].cget("text") == "77.7%"
        assert app.status_ribbon_labels["ecmo_flow"].cget("text") == "1.234 L/min"
    finally:
        app._close()


def test_phase6_6a_canonical_patient_flow_label_has_no_legacy_console_variant():
    source = Path("src/neogui/ecmo_workspace.py").read_text(encoding="utf-8")
    assert '"PATIENT MAP"' not in source
    assert '"PATIENT FLOW"' not in source
    assert source.count("ECMO PATIENT FLOW") >= 5

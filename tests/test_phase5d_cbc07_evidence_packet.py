import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = "validation_packets/CBC07_POSITIVE_AIRWAY_PRESSURE_HEMODYNAMICS_EVIDENCE_REVIEW_2026-08-10.md"
FEATURE = "CBC07 positive airway pressure hemodynamic behavior contract"

def test_cbc07_evidence_packet_exists_and_preserves_expert_gate():
    text = (ROOT / PACKET).read_text(encoding="utf-8")
    assert "external evidence packet complete; expert sign-off pending" in text
    assert "24389709" in text
    assert "17460022" in text
    assert "simulator canonical isolated regression path" in text
    assert "Not established as universal" in text

def test_cbc07_contract_reflects_phase2d_controls_and_nonuniversal_scope():
    data = json.loads((ROOT / "clinical_behavior_contracts/positive_airway_pressure_hemodynamics_v1.json").read_text())
    assert "full ventilator rate/mode/inspiratory-time control through UnifiedNeonatalPatient" not in data["not_modeled"]
    assert "learner-operable ventilator controls are added" not in data["future_retest_conditions"]
    assert any("Phase 2d" in x for x in data["notes"])
    assert data["preconditions"]["canonical_elevated_peep_cmh2o"] == 8.0
    assert data["preconditions"]["graded_probe_peep_cmh2o"] == [0.0, 5.0, 8.0, 12.0]
    assert "not_supported_as_universal" in data["evidence_scope"]

def test_living_matrix_points_to_cbc07_packet_and_direct_controls():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    row = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    assert "external evidence packet complete" in row["Clinical/behavior validation"]
    assert "Reviewed by practicing ECMO specialist (project author)" in row["Clinical/behavior validation"]
    assert row["GUI-exposed"] == "Y"
    assert row["Learner-operable"] == "Y"
    assert PACKET in row["Evidence"]

def test_matrix_csv_json_mirror_for_cbc07_status():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    jrow = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    with (ROOT / "CAPABILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        crow = next(r for r in csv.DictReader(f) if r["Feature"] == FEATURE)
    assert crow == jrow

def test_validation_queue_cbc01_cbc02_cbc07_statuses_are_consistent():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text())
    by_id = {i["contract_id"]: i for i in queue["items"]}
    expected = "single-reviewer-clinical-review-complete-evidence-packet-complete-independent-review-pending"
    assert by_id["cbc.lowflow.hypovolemia.v1"]["automated_status"] == expected
    assert by_id["cbc.ecmo.sweep-gas-failure.v1"]["automated_status"] == expected
    cbc07 = by_id["cbc.patient.positive-airway-pressure-hemodynamics.v1"]
    assert cbc07["automated_status"] == expected
    assert cbc07["evidence_packet"] == PACKET
    assert cbc07["current_matrix_authority"] == "CAPABILITY_MATRIX.json"

def test_fix_map_remains_untouched_and_overlay_tracks_cbc07():
    assert (ROOT / "FIX_MAP_v4.md").exists()
    overlay = (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10.md").read_text(encoding="utf-8")
    assert "CBC07 Positive-Airway-Pressure Hemodynamics external evidence packet complete" in overlay

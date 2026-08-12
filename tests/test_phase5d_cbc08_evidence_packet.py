import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = "validation_packets/CBC08_FDO2_OXYGEN_FRACTION_EVIDENCE_REVIEW_2026-08-10.md"
FEATURE = "CBC08 ECMO FdO2 oxygen-fraction behavior contract"

def test_cbc08_evidence_packet_exists_and_preserves_expert_gate():
    text = (ROOT / PACKET).read_text(encoding="utf-8")
    assert "external evidence packet complete; expert sign-off pending" in text
    assert "39162827" in text
    assert "28828371" in text
    assert "35883117" in text
    assert "regression settings only" in text

def test_cbc08_contract_adds_evidence_scope_without_changing_behavior_fixture():
    data = json.loads((ROOT / "clinical_behavior_contracts/fdo2_oxygen_fraction_control_v1.json").read_text())
    assert data["preconditions"]["graded_probe_fdo2"] == [1.0, 0.8, 0.6, 0.4, 0.21]
    assert data["tolerances"]["paco2_absolute_mmhg"] == 0.5
    assert data["tolerances"]["flow_relative"] == 0.005
    assert data["evidence_scope"]["external_evidence_packet"] == PACKET
    assert any("device-specific" in x for x in data["evidence_scope"]["not_supported_as_quantitative_claims"])

def test_living_matrix_points_to_cbc08_packet_and_direct_controls():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    row = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    assert "external evidence packet complete" in row["Clinical/behavior validation"]
    assert "Reviewed by practicing ECMO specialist (project author)" in row["Clinical/behavior validation"]
    assert row["Learner-operable"] == "Y"
    assert PACKET in row["Evidence"]

def test_matrix_csv_json_mirror_for_cbc08_status():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    jrow = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    with (ROOT / "CAPABILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        crow = next(r for r in csv.DictReader(f) if r["Feature"] == FEATURE)
    assert crow == jrow

def test_validation_queue_points_to_cbc08_packet_without_becoming_status_authority():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text())
    item = next(i for i in queue["items"] if i["contract_id"] == "cbc.ecmo.fdo2-oxygen-fraction-control.v1")
    assert item["evidence_packet"] == PACKET
    assert item["automated_status"] == "single-reviewer-clinical-review-complete-evidence-packet-complete-independent-review-pending"
    assert item["current_matrix_authority"] == "CAPABILITY_MATRIX.json"
    queue_md = (ROOT / "VALIDATION_REVIEW_QUEUE.md").read_text(encoding="utf-8")
    assert "### cbc.ecmo.fdo2-oxygen-fraction-control.v1" in queue_md
    assert "CBC08_FDO2_OXYGEN_FRACTION_EVIDENCE_REVIEW_2026-08-10.md" in queue_md

def test_fix_map_remains_untouched_and_overlay_tracks_cbc08():
    assert (ROOT / "FIX_MAP_v4.md").exists()
    overlay = (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10.md").read_text(encoding="utf-8")
    assert "CBC08 FdO2 Oxygen-Fraction Control external evidence packet complete" in overlay

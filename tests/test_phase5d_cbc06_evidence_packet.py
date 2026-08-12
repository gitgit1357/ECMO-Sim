import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = "validation_packets/CBC06_CKRT_NET_ULTRAFILTRATION_EVIDENCE_REVIEW_2026-08-10.md"
FEATURE = "CBC06 CKRT net ultrafiltration behavior contract"

def test_cbc06_evidence_packet_exists_and_preserves_expert_gate():
    text = (ROOT / PACKET).read_text(encoding="utf-8")
    assert "external evidence packet complete; expert sign-off pending" in text
    assert "23965637" in text
    assert "22743776" in text
    assert "regression stimuli" in text

def test_cbc06_contract_reflects_phase2b_controls_without_behavior_change():
    data = json.loads((ROOT / "clinical_behavior_contracts/ckrt_net_ultrafiltration_v1.json").read_text())
    assert "learner CKRT prescription GUI" not in data["not_modeled"]
    assert any("Phase 2b" in x for x in data["notes"])
    assert data["stimulus"]["net_ultrafiltration_rate_ml_min"] == 0.4
    assert data["preconditions"]["ckrt_blood_flow_ml_min"] == 30.0

def test_living_matrix_points_to_cbc06_evidence_packet_and_direct_controls():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    row = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    assert "external evidence packet complete" in row["Clinical/behavior validation"]
    assert "Reviewed by practicing ECMO specialist (project author)" in row["Clinical/behavior validation"]
    assert row["GUI-exposed"] == "Y"
    assert row["Learner-operable"] == "Y"
    assert PACKET in row["Evidence"]

def test_matrix_csv_json_mirror_for_cbc06_status():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    jrow = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    with (ROOT / "CAPABILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        crow = next(r for r in csv.DictReader(f) if r["Feature"] == FEATURE)
    assert crow == jrow

def test_validation_queue_points_to_cbc06_packet_without_becoming_status_authority():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text())
    item = next(i for i in queue["items"] if i["contract_id"] == "cbc.ecmo.ckrt-net-ultrafiltration.v1")
    assert item["evidence_packet"] == PACKET
    assert item["current_matrix_authority"] == "CAPABILITY_MATRIX.json"
    assert "independent-review-pending" in item["automated_status"]

def test_fix_map_remains_untouched_and_overlay_tracks_cbc06():
    assert (ROOT / "FIX_MAP_v4.md").exists()
    overlay = (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10.md").read_text(encoding="utf-8")
    assert "CBC06 CKRT Net Ultrafiltration external evidence packet complete" in overlay

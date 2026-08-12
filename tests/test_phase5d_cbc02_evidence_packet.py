import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = "validation_packets/CBC02_SWEEP_GAS_FAILURE_EVIDENCE_REVIEW_2026-08-10.md"
FEATURE = "CBC02 complete sweep-gas failure behavior contract"

def test_cbc02_evidence_packet_exists_and_preserves_expert_gate():
    text = (ROOT / PACKET).read_text(encoding="utf-8")
    assert "external evidence packet complete; expert sign-off pending" in text
    assert "post-transient" in text
    assert "not" in text.lower()
    assert "600 mL/min" in text

def test_cbc02_contract_carries_residual_gas_transient_caveat():
    data = json.loads((ROOT / "clinical_behavior_contracts/sweep_gas_failure_v1.json").read_text())
    assert any("residual oxygen" in x for x in data["allowed_exceptions"])
    assert any("post-transient" in x for x in data["notes"])

def test_living_matrix_points_to_cbc02_evidence_packet():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    row = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    assert "external evidence packet complete" in row["Clinical/behavior validation"]
    assert "Reviewed by practicing ECMO specialist (project author)" in row["Clinical/behavior validation"]
    assert PACKET in row["Evidence"]

def test_matrix_csv_json_mirror_for_cbc02_status():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    jrow = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    with (ROOT / "CAPABILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        crow = next(r for r in csv.DictReader(f) if r["Feature"] == FEATURE)
    assert crow == jrow

def test_validation_queue_points_to_cbc02_packet_without_becoming_status_authority():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text())
    item = next(i for i in queue["items"] if i["contract_id"] == "cbc.ecmo.sweep-gas-failure.v1")
    assert item["evidence_packet"] == PACKET
    assert item["current_matrix_authority"] == "CAPABILITY_MATRIX.json"

def test_fix_map_remains_untouched_and_overlay_tracks_phase5d():
    assert (ROOT / "FIX_MAP_v4.md").exists()
    overlay = (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10.md").read_text(encoding="utf-8")
    assert "CBC02 Sweep-Gas Failure evidence packet complete" in overlay

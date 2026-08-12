import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = "validation_packets/CBC01_HYPOVOLEMIA_PRELOAD_EVIDENCE_REVIEW_2026-08-10.md"
FEATURE = "Clinical Behavior Contract — hypovolemia/preload low flow"


def test_cbc01_evidence_packet_exists_and_preserves_expert_gate():
    text = (ROOT / PACKET).read_text(encoding="utf-8")
    assert "external evidence packet complete; expert sign-off pending" in text
    assert "not" in text.lower()
    assert "15%" in text
    assert "not a neonatal clinical threshold" in text


def test_living_matrix_points_to_cbc01_evidence_packet():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text(encoding="utf-8"))
    row = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    assert "external evidence packet complete" in row["Clinical/behavior validation"]
    assert "Reviewed by practicing ECMO specialist (project author)" in row["Clinical/behavior validation"]
    assert PACKET in row["Evidence"]


def test_matrix_csv_json_mirror_for_cbc01_status():
    data = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text(encoding="utf-8"))
    jrow = next(r for r in data["rows"] if r["Feature"] == FEATURE)
    with (ROOT / "CAPABILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        crow = next(r for r in csv.DictReader(f) if r["Feature"] == FEATURE)
    assert crow == jrow


def test_validation_queue_points_to_packet_without_becoming_status_authority():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text(encoding="utf-8"))
    item = next(i for i in queue["items"] if i["contract_id"] == "cbc.lowflow.hypovolemia.v1")
    assert item["evidence_packet"] == PACKET
    assert item["current_matrix_authority"] == "CAPABILITY_MATRIX.json"


def test_original_fix_map_remains_present_and_status_overlay_is_separate():
    assert (ROOT / "FIX_MAP_v4.md").exists()
    overlay = (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10.md").read_text(encoding="utf-8")
    assert "FIX_MAP_v4.md" in overlay
    assert "does not silently rewrite" in overlay

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = "validation_packets/CBC09_BRIDGE_RECIRCULATION_FLOW_DIVERSION_EVIDENCE_REVIEW_2026-08-10.md"
FEATURE = "CBC09 bridge recirculation / flow-diversion behavior contract"


def test_cbc09_evidence_packet_exists_and_preserves_expert_gate():
    text = (ROOT / PACKET).read_text(encoding="utf-8")
    assert "external evidence packet complete; expert sign-off pending" in text
    assert "35089258" in text
    assert "23735989" in text
    assert "19948749" in text
    assert "regression stimuli only" in text


def test_cbc09_contract_adds_evidence_scope_without_changing_behavior_fixture():
    data = json.loads((ROOT / "clinical_behavior_contracts/bridge_recirculation_flow_diversion_v1.json").read_text())
    assert data["preconditions"]["bridge_target_flow_probe_ml_min"] == [0, 25, 50, 75, 100, 150]
    assert data["tolerances"]["bridge_target_absolute_ml_min"] == 0.05
    assert data["tolerances"]["branch_conservation_absolute_ml_min"] == 0.1
    assert data["evidence_scope"]["external_evidence_packet"] == PACKET
    assert "mechanistic_inference_only" in data["evidence_scope"]


def test_living_matrix_marks_cbc09_evidence_complete_and_csv_mirrors_json():
    matrix = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    row = next(r for r in matrix["rows"] if r["Feature"] == FEATURE)
    assert "external evidence packet complete" in row["Clinical/behavior validation"]
    assert PACKET in row["Evidence"]
    with (ROOT / "CAPABILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    csv_row = next(r for r in csv_rows if r["Feature"] == FEATURE)
    assert csv_row == row


def test_validation_queue_marks_cbc09_packet_complete_in_json_and_markdown():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text())
    item = next(i for i in queue["items"] if i["contract_id"] == "cbc.ecmo.bridge-recirculation-flow-diversion.v1")
    assert item["automated_status"] == "single-reviewer-clinical-review-complete-evidence-packet-complete-independent-review-pending"
    assert item["evidence_packet"] == PACKET
    md = (ROOT / "VALIDATION_REVIEW_QUEUE.md").read_text(encoding="utf-8")
    section = md.split("### cbc.ecmo.bridge-recirculation-flow-diversion.v1",1)[1].split("### ",1)[0]
    assert "single-reviewer clinical review complete" in section.lower()
    assert PACKET in section


def test_roadmap_advances_next_priority_a_packet_to_cbc10():
    text = (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10-PHASE5D-CBC09.md").read_text(encoding="utf-8")
    assert "CBC09 Bridge Recirculation / Flow Diversion evidence packet complete" in text
    assert "CBC10 Fixed-Shunt Configuration evidence packet" in text


def test_original_fix_map_v4_remains_present_and_unmodified_by_status_overlay_model():
    assert (ROOT / "FIX_MAP_v4.md").exists()
    assert (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10.md").exists()

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = "validation_packets/CBC10_FIXED_SHUNT_CONFIGURATION_EVIDENCE_REVIEW_2026-08-10.md"
FEATURE = "CBC10 fixed-shunt configuration / hemofilter hydraulics behavior contract"


def test_cbc10_evidence_packet_exists_and_preserves_expert_gate():
    text = (ROOT / PACKET).read_text(encoding="utf-8")
    assert "external evidence packet complete; expert sign-off pending" in text
    assert "PMC8250911" in text
    assert "reduced-order" in text
    assert "does **not** establish" in text


def test_cbc10_contract_adds_evidence_scope_without_changing_behavior_fixture():
    data = json.loads((ROOT / "clinical_behavior_contracts/fixed_shunt_configuration_v1.json").read_text())
    assert data["preconditions"]["rpm"] == 2600
    assert data["preconditions"]["sweep_gas_flow_ml_min"] == 600
    assert data["tolerances"]["branch_conservation_absolute_ml_min"] == 0.1
    assert data["tolerances"]["hydraulic_equivalence_absolute_ml_min"] == 1e-6
    assert data["evidence_scope"]["external_evidence_packet"] == PACKET
    assert "reduced_order_assumption_only" in data["evidence_scope"]


def test_living_matrix_marks_cbc10_evidence_complete_and_csv_mirrors_json():
    matrix = json.loads((ROOT / "CAPABILITY_MATRIX.json").read_text())
    row = next(r for r in matrix["rows"] if r["Feature"] == FEATURE)
    assert "external evidence packet complete" in row["Clinical/behavior validation"]
    assert PACKET in row["Evidence"]
    with (ROOT / "CAPABILITY_MATRIX.csv").open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    csv_row = next(r for r in csv_rows if r["Feature"] == FEATURE)
    assert csv_row == row


def test_validation_queue_marks_cbc10_packet_complete_in_json_and_markdown():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text())
    item = next(i for i in queue["items"] if i["contract_id"] == "cbc.ecmo.fixed-shunt-configuration.v1")
    assert item["automated_status"] == "single-reviewer-clinical-review-complete-evidence-packet-complete-independent-review-pending"
    assert item["evidence_packet"] == PACKET
    md = (ROOT / "VALIDATION_REVIEW_QUEUE.md").read_text(encoding="utf-8")
    section = md.split("### cbc.ecmo.fixed-shunt-configuration.v1", 1)[1].split("### ", 1)[0]
    assert "single-reviewer clinical review complete" in section.lower()
    assert PACKET in section


def test_all_priority_a_items_now_have_evidence_packets_complete():
    queue = json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text())
    priority_a = [i for i in queue["items"] if i["priority"] == "A"]
    assert len(priority_a) == 7
    assert all(i["automated_status"] == "single-reviewer-clinical-review-complete-evidence-packet-complete-independent-review-pending" for i in priority_a)
    assert all(i.get("evidence_packet") for i in priority_a)


def test_roadmap_closes_priority_a_evidence_pass_without_rewriting_fix_map():
    text = (ROOT / "ROADMAP_CURRENT_STATUS_2026-08-10-PHASE5D-CBC10.md").read_text(encoding="utf-8")
    assert "Priority-A external evidence packet pass is now complete (7/7)" in text
    assert "human expert dispositions" in text
    assert (ROOT / "FIX_MAP_v4.md").exists()

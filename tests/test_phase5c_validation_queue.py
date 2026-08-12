import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _queue():
    return json.loads((ROOT / "VALIDATION_REVIEW_QUEUE.json").read_text(encoding="utf-8"))


def test_validation_queue_covers_all_current_cbc_json_contracts_once():
    queue = _queue()
    ids = [item["contract_id"] for item in queue["items"]]
    assert len(ids) == len(set(ids)) == 11

    contract_ids = []
    for path in (ROOT / "clinical_behavior_contracts").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "contract_id" in data:
            contract_ids.append(data["contract_id"])
    assert set(ids) == set(contract_ids)


def test_validation_queue_prioritizes_learner_operable_contracts_first():
    items = _queue()["items"]
    assert sum(item["priority"] == "A" for item in items) == 7
    assert sum(item["priority"] == "B" for item in items) == 4
    for item in items:
        if item["priority"] == "A":
            assert "direct" in item["learner_exposure"]


def test_validation_queue_is_explicitly_not_the_status_authority():
    queue = _queue()
    assert "not a competing" in queue["purpose"].lower()
    assert all(item["current_matrix_authority"] == "CAPABILITY_MATRIX.json" for item in queue["items"])


def test_every_validation_item_has_questions_evidence_boundary_and_gate():
    for item in _queue()["items"]:
        assert item["review_questions"]
        assert item["review_domains"]
        assert item["device_or_policy_evidence"]
        assert item["blocking_for_external_training"]

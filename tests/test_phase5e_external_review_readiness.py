import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path):
    return json.loads((ROOT / path).read_text())


def test_external_review_checklist_covers_all_current_cbcs_exactly_once():
    queue = _load('VALIDATION_REVIEW_QUEUE.json')
    checklist = _load('external_review/INDEPENDENT_REVIEW_CHECKLIST.json')
    queue_ids = [i['contract_id'] for i in queue['items']]
    review_ids = [i['contract_id'] for i in checklist['items']]
    assert len(queue_ids) == 11
    assert len(review_ids) == 11
    assert len(set(review_ids)) == 11
    assert set(review_ids) == set(queue_ids)


def test_priority_distribution_and_evidence_links_are_truthful():
    checklist = _load('external_review/INDEPENDENT_REVIEW_CHECKLIST.json')
    a = [i for i in checklist['items'] if i['priority'] == 'A']
    b = [i for i in checklist['items'] if i['priority'] == 'B']
    assert len(a) == 7
    assert len(b) == 4
    for item in a:
        assert item['evidence_packet']
        assert (ROOT / item['evidence_packet']).exists()
    for item in b:
        assert item['evidence_packet'] in (None, '')


def test_all_independent_dispositions_are_pending_and_gate_is_blocked():
    checklist = _load('external_review/INDEPENDENT_REVIEW_CHECKLIST.json')
    assert all(i['independent_disposition'] == 'PENDING' for i in checklist['items'])
    assert all(i['external_training_gate'] == 'BLOCKED_PENDING_INDEPENDENT_REVIEW' for i in checklist['items'])
    gate = (ROOT / 'external_review/EXTERNAL_TRAINING_GO_LIVE_GATE.md').read_text()
    assert 'BLOCKED' in gate
    assert 'independent facility-educator review pending' in gate


def test_single_reviewer_provenance_is_not_relabelled_as_independent():
    review = (ROOT / 'PHASE5D_SINGLE_REVIEWER_CLINICAL_REVIEW_2026-08-10.md').read_text()
    packet = (ROOT / 'external_review/INDEPENDENT_CLINICAL_REVIEW_PACKET.md').read_text()
    assert 'not independent external expert review' in review.lower()
    assert 'not independent' in packet.lower()
    assert 'No independent disposition is pre-filled or implied.' in packet


def test_capability_matrix_contains_review_readiness_and_go_live_block_rows():
    matrix = _load('CAPABILITY_MATRIX.json')
    by_name = {r['Feature']: r for r in matrix['rows']}
    ready = by_name['Phase 5e independent clinical-review readiness packet']
    gate = by_name['External-training / go-live clinical gate']
    assert ready['Implemented'] == 'Y'
    assert 'READY FOR INDEPENDENT REVIEW' in ready['Clinical/behavior validation']
    assert gate['Clinical/behavior validation'].startswith('BLOCKED')


def test_packet_surfaces_all_strictly_blocked_capability_rows():
    matrix = _load('CAPABILITY_MATRIX.json')
    packet = (ROOT / 'external_review/INDEPENDENT_CLINICAL_REVIEW_PACKET.md').read_text()
    strict_blocked = [r for r in matrix['rows'] if str(r['Clinical/behavior validation']).startswith('BLOCKED')]
    # The new go-live gate row is intentionally represented by the packet/gate itself.
    for row in strict_blocked:
        if row['Feature'] in {'External-training / go-live clinical gate', 'Formal regulatory/legal/IP/facility clearance gate'}:
            continue
        assert row['Feature'] in packet


def test_capability_matrix_csv_and_json_have_same_rows():
    import csv
    matrix = _load('CAPABILITY_MATRIX.json')
    with (ROOT / 'CAPABILITY_MATRIX.csv').open(newline='') as f:
        csv_rows = list(csv.DictReader(f))
    assert csv_rows == matrix['rows']


def test_roadmap_marks_phase5e_readiness_complete_but_external_review_pending():
    roadmap = (ROOT / 'ROADMAP_CURRENT_STATUS_2026-08-10.md').read_text()
    assert 'Phase 5e external-review readiness update' in roadmap
    assert 'readiness packaging is complete' in roadmap
    assert 'actual independent disposition is an external dependency' in roadmap

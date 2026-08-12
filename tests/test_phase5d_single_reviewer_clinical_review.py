import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_all_current_cbcs_have_single_reviewer_clinical_review():
    q = json.loads((ROOT / 'VALIDATION_REVIEW_QUEUE.json').read_text())
    assert len(q['items']) == 11
    assumption = q['expert_validation_assumption']
    assert assumption['status'] == 'single-reviewer-clinical-review-complete'
    assert assumption['reviewer_role'] == 'practicing ECMO specialist'
    assert 'project author' in assumption['reviewer_relationship_to_project']
    assert assumption['independent_external_review']['status'] == 'not yet started'
    assert all(
        i['expert_disposition'] == 'single-reviewer-clinical-review-complete-independent-review-pending'
        for i in q['items']
    )


def test_status_strings_cannot_claim_single_reviewer_without_also_flagging_independent_review_pending():
    """
    Structural guard: any future edit that keeps the "reviewed by an ECMO
    specialist" half of a status string must also keep the "independent
    review pending" half. This makes it hard to quietly upgrade the review
    disposition by dropping only the caveat.
    """
    q = json.loads((ROOT / 'VALIDATION_REVIEW_QUEUE.json').read_text())
    for i in q['items']:
        status = i['automated_status']
        if 'single-reviewer' in status:
            assert 'independent-review-pending' in status, (
                f"{i['contract_id']}: automated_status claims single-reviewer "
                f"review without flagging independent review as pending: {status}"
            )
        disposition = i['expert_disposition']
        if 'single-reviewer' in disposition:
            assert 'independent-review-pending' in disposition, (
                f"{i['contract_id']}: expert_disposition claims single-reviewer "
                f"review without flagging independent review as pending: {disposition}"
            )

    m = json.loads((ROOT / 'CAPABILITY_MATRIX.json').read_text())
    for r in m['rows']:
        v = r.get('Clinical/behavior validation', '')
        if 'Reviewed by practicing ECMO specialist' in v:
            assert 'independent external review' in v.lower() and 'pending' in v.lower(), (
                f"{r['Feature']}: capability matrix claims specialist review "
                f"without flagging independent review as pending: {v}"
            )


def test_expert_review_does_not_unblock_missing_mechanisms():
    m = json.loads((ROOT / 'CAPABILITY_MATRIX.json').read_text())
    blocked = [r for r in m['rows'] if 'BLOCKED' in r['Clinical/behavior validation']]
    assert blocked
    assert all('BLOCKED' in r['Clinical/behavior validation'] for r in blocked)


def test_historical_evidence_packets_are_not_rewritten_as_if_they_had_independent_signoff():
    text = (ROOT / 'validation_packets/CBC10_FIXED_SHUNT_CONFIGURATION_EVIDENCE_REVIEW_2026-08-10.md').read_text()
    assert 'expert sign-off pending' in text
    current = (ROOT / 'PHASE5D_SINGLE_REVIEWER_CLINICAL_REVIEW_2026-08-10.md').read_text()
    assert 'practicing ecmo specialist' in current.lower()
    assert 'not independent external expert review' in current.lower()

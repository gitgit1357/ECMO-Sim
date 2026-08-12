import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())

def test_claims_inventory_keeps_all_external_clearances_pending():
    d=load('commercial_review/CLAIMS_AND_REVIEW_INVENTORY.json')
    disp=d['current_dispositions']
    assert disp['independent_clinical_review']=='PENDING'
    assert disp['external_training_go_live'].startswith('BLOCKED')
    assert disp['regulatory_status']=='PENDING_FORMAL_REVIEW'
    assert disp['legal_ip_clearance']=='PENDING_FORMAL_REVIEW'
    assert disp['institutional_deployment_approval']=='PENDING_FACILITY_REVIEW'

def test_training_only_intended_use_and_nonclaims_are_explicit():
    d=load('commercial_review/CLAIMS_AND_REVIEW_INVENTORY.json')
    assert 'Simulation and training only' in d['intended_use']['current']
    joined=' '.join(d['claims_not_cleared']).lower()
    for term in ['fda','device equivalence','trademark','freedom to operate','commercial legal clearance']:
        assert term in joined

def test_official_source_inventory_contains_expected_authorities():
    d=load('commercial_review/CLAIMS_AND_REVIEW_INVENTORY.json')
    auth={x['authority'] for x in d['official_source_inventory']}
    assert {'FDA','U.S. Copyright Office','USPTO'} <= auth
    assert all(x['url'].startswith('https://') for x in d['official_source_inventory'])

def test_capability_matrix_records_readiness_and_pending_clearance_gate():
    m=load('CAPABILITY_MATRIX.json'); by={r['Feature']:r for r in m['rows']}
    assert by['Phase 5f commercial/regulatory/IP review readiness']['Implemented']=='Y'
    assert by['Formal regulatory/legal/IP/facility clearance gate']['Clinical/behavior validation'].startswith('BLOCKED')

def test_matrix_csv_json_mirror_after_phase5f():
    m=load('CAPABILITY_MATRIX.json')
    with (ROOT/'CAPABILITY_MATRIX.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    assert rows==m['rows']

def test_phase5f_does_not_claim_a_formal_conclusion():
    text=(ROOT/'commercial_review/REGULATORY_AND_IP_REVIEW_READINESS.md').read_text().lower()
    assert 'pending formal regulatory review' in text
    assert 'pending formal ip/legal review' in text
    assert 'not legal advice' in text

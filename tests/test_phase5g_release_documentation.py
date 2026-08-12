import csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())

def test_readme_describes_current_integrated_simulator_not_old_v03_front_door():
    text=(ROOT/'README.md').read_text()
    assert 'Neonatal ECMO Simulation Training Platform' in text
    assert 'v0.21.0' in text
    assert 'Patient Monitor' in text and 'Scenario Log' in text
    assert 'myocardial failure is therefore **not yet validated**' not in text.lower()

def test_pyproject_version_and_description_are_current():
    text=(ROOT/'pyproject.toml').read_text()
    assert 'version = "0.21.0"' in text
    assert 'Reduced-order neonatal ECMO simulation and training platform' in text

def test_release_checklist_marks_internal_complete_but_external_gate_blocked():
    text=(ROOT/'RELEASE_READINESS_CHECKLIST.md').read_text()
    assert '[x] Phase 0' in text
    assert '[x] Phase 5' in text
    assert '[ ] Independent facility ECMO educator review' in text
    assert 'BLOCKED pending independent clinical review' in text

def test_capability_matrix_records_phase5g_and_mirrors_csv():
    m=load('CAPABILITY_MATRIX.json')
    by={r['Feature']:r for r in m['rows']}
    assert by['Phase 5g release documentation / package metadata synchronization']['Implemented']=='Y'
    with (ROOT/'CAPABILITY_MATRIX.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    assert rows==m['rows']

def test_roadmap_states_internal_work_complete_with_external_dependencies_open():
    text=(ROOT/'ROADMAP_CURRENT_STATUS_2026-08-10.md').read_text()
    assert 'Internal FIX_MAP v4 build/readiness tasks are complete' in text
    assert 'external clinical/facility/regulatory/legal gates remain open dependencies' in text

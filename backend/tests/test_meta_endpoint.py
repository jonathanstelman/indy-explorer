import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app, _load_pipeline_metadata
from models import Resort

FAKE_RESORTS = [
    Resort(
        resort_id='id-1',
        name='Alpine Resort',
        region='West',
        city='Vail',
        state='CO',
        country='USA',
        reservation_status='none',
        indy_page='https://example.com/alpine',
        vertical=2000.0,
        acres=800.0,
        num_trails=100.0,
        num_trails_xc=10.0,
        num_lifts=10.0,
        trail_length_mi=50.0,
        pr_total=85.0,
        pr_snow=9.0,
        pr_resiliency=8.0,
        pr_size=7.5,
        pr_terrain_diversity=7.0,
        pr_challenge=6.5,
        pr_lifts=6.0,
        pr_crowd_flow=5.5,
        pr_facilities=5.0,
        pr_navigation=4.5,
        pr_mountain_aesthetic=9.5,
        pr_pass_affiliation='Indy Pass',
        blackout_all_dates=json.dumps(['2025-12-25', '2025-12-26']),
        ltt_blackout_all_dates=json.dumps(['2026-01-01']),
    ),
    Resort(
        resort_id='id-2',
        name='Nordic Lodge',
        region='Northeast',
        city='Stowe',
        state='VT',
        country='USA',
        reservation_status='none',
        indy_page='https://example.com/nordic',
        vertical=1000.0,
        acres=300.0,
        num_trails=50.0,
        num_trails_xc=30.0,
        num_lifts=5.0,
        trail_length_mi=25.0,
        pr_total=70.0,
        pr_snow=7.5,
        pr_resiliency=6.5,
        pr_size=6.0,
        pr_terrain_diversity=5.5,
        pr_challenge=5.0,
        pr_lifts=4.5,
        pr_crowd_flow=4.0,
        pr_facilities=3.5,
        pr_navigation=3.0,
        pr_mountain_aesthetic=8.0,
        pr_pass_affiliation='Cali Pass, Powder Alliance',
        blackout_all_dates=json.dumps(['2025-12-24', '2026-01-02']),
        ltt_blackout_all_dates=json.dumps(['2026-01-15']),
    ),
    Resort(
        resort_id='id-3',
        name='Tremblant',
        region='Northeast',
        city='Mont-Tremblant',
        state=None,
        country='Canada',
        reservation_status='none',
        indy_page='https://example.com/tremblant',
        # no numeric fields — tests that nulls are excluded from ranges
    ),
]

client = TestClient(app)


def test_meta_regions_countries_states():
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/meta')
    assert response.status_code == 200
    data = response.json()
    assert data['regions'] == ['Northeast', 'West']
    assert data['countries'] == ['Canada', 'USA']
    assert data['states'] == ['CO', 'VT']


def test_meta_pass_affiliations_split_deduped_sorted():
    # id-2's 'Cali Pass, Powder Alliance' is a combo value — meta should expose the
    # individual tags, not the raw combo string, so a user can filter on one tag
    # across all combos it appears in.
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/meta')
    data = response.json()
    assert data['pass_affiliations'] == ['Cali Pass', 'Powder Alliance']


def test_meta_pass_affiliations_excludes_indy_pass():
    # Every resort in this app is an Indy Pass resort by definition, so 'Indy Pass'
    # isn't a discriminating filter option here — worth suppressing rather than
    # showing a tag that (mis-)implies some resorts aren't Indy Pass affiliated.
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/meta')
    assert 'Indy Pass' not in response.json()['pass_affiliations']


def test_meta_numeric_ranges():
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/meta')
    data = response.json()
    assert data['vertical'] == {'min': 1000.0, 'max': 2000.0}
    assert data['acres'] == {'min': 300.0, 'max': 800.0}
    assert data['num_trails'] == {'min': 50.0, 'max': 100.0}
    assert data['num_trails_xc'] == {'min': 10.0, 'max': 30.0}
    assert data['num_lifts'] == {'min': 5.0, 'max': 10.0}
    assert data['trail_length_mi'] == {'min': 25.0, 'max': 50.0}
    assert data['pr_total'] == {'min': 70.0, 'max': 85.0}


def test_meta_null_values_excluded_from_ranges():
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/meta')
    data = response.json()
    # id-3 has no numeric fields; ranges should still be computed from id-1 and id-2
    assert data['pr_mountain_aesthetic'] == {'min': 8.0, 'max': 9.5}


def test_meta_blackout_date_ranges():
    with patch('main._resorts', FAKE_RESORTS):
        response = client.get('/meta')
    data = response.json()
    assert data['blackout_date_range'] == {'min': '2025-12-24', 'max': '2026-01-02'}
    assert data['ltt_date_range'] == {'min': '2026-01-01', 'max': '2026-01-15'}


def test_meta_empty_resorts():
    with patch('main._resorts', []):
        response = client.get('/meta')
    assert response.status_code == 200
    data = response.json()
    assert data['regions'] == []
    assert data['pass_affiliations'] == []
    assert data['vertical'] == {'min': None, 'max': None}
    assert data['acres'] == {'min': None, 'max': None}
    assert data['blackout_date_range'] == {'min': None, 'max': None}


def test_meta_last_pipeline_run_present():
    ts = '2026-04-22T01:47:15.286723+00:00'
    with patch('main._resorts', FAKE_RESORTS), patch('main._last_pipeline_run', ts):
        response = client.get('/meta')
    assert response.status_code == 200
    assert response.json()['last_pipeline_run'] == ts


def test_meta_last_pipeline_run_absent():
    with patch('main._resorts', FAKE_RESORTS), patch('main._last_pipeline_run', None):
        response = client.get('/meta')
    assert response.status_code == 200
    assert response.json()['last_pipeline_run'] is None


# --- _load_pipeline_metadata unit tests ---


def test_load_pipeline_metadata_reads_last_run():
    metadata = {'last_run': '2026-04-22T01:47:15+00:00', 'mode': 'full'}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(metadata, f)
        path = f.name
    assert _load_pipeline_metadata(path) == '2026-04-22T01:47:15+00:00'


def test_load_pipeline_metadata_missing_file():
    assert _load_pipeline_metadata('/nonexistent/path/pipeline_metadata.json') is None


def test_load_pipeline_metadata_malformed_json():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('not valid json{{{')
        path = f.name
    assert _load_pipeline_metadata(path) is None


def test_load_pipeline_metadata_missing_key():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'mode': 'full'}, f)
        path = f.name
    assert _load_pipeline_metadata(path) is None

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from models import Resort


# Helper to build a minimal Resort with the fields we care about
def make_resort(resort_id, name, blackout_dates=None, ltt_blackout_dates=None, ltt_available=False):
    return Resort(
        resort_id=resort_id,
        name=name,
        region='West',
        reservation_status='Not Required',
        indy_page=f'https://example.com/{resort_id}',
        ltt_available=ltt_available,
        blackout_all_dates=json.dumps(blackout_dates or []),
        ltt_blackout_all_dates=json.dumps(ltt_blackout_dates or []),
    )


FAKE_RESORTS = [
    make_resort(
        'id-1',
        'Alpine Peak',
        blackout_dates=['2025-12-25', '2025-12-26', '2026-01-01'],
        ltt_blackout_dates=['2025-12-25'],
        ltt_available=True,
    ),
    make_resort(
        'id-2',
        'Nordic Valley',
        blackout_dates=['2026-02-14', '2026-02-15'],
        ltt_blackout_dates=[],
        ltt_available=True,
    ),
    make_resort(
        'id-3',
        'Powder Ridge',
        blackout_dates=[],
        ltt_blackout_dates=[],
        ltt_available=False,
    ),
]


@pytest.fixture(autouse=True)
def patch_resorts():
    with patch('main._resorts', FAKE_RESORTS):
        yield


@pytest.fixture
def client():
    return TestClient(app)


# --- blackout date range ---


def test_blackout_date_range_excludes_resort_with_date_in_range(client):
    # Christmas day is in Alpine Peak's blackout list
    response = client.get('/resorts?blackout_date_from=2025-12-25&blackout_date_to=2025-12-25')
    assert response.status_code == 200
    names = {r['name'] for r in response.json()}
    assert 'Alpine Peak' not in names
    assert 'Nordic Valley' in names
    assert 'Powder Ridge' in names


def test_blackout_date_range_spanning_multiple_resorts(client):
    # Dec 26 – Feb 14 spans Alpine Peak (Dec 26) and Nordic Valley (Feb 14)
    response = client.get('/resorts?blackout_date_from=2025-12-26&blackout_date_to=2026-02-14')
    names = {r['name'] for r in response.json()}
    assert names == {'Powder Ridge'}


def test_blackout_date_range_no_overlap_returns_all(client):
    response = client.get('/resorts?blackout_date_from=2025-07-04&blackout_date_to=2025-07-04')
    assert len(response.json()) == 3


def test_blackout_date_from_only_acts_as_open_ended_lower_bound(client):
    # from=2026-02-14 with no to — should exclude Nordic Valley (Feb 14, 15)
    response = client.get('/resorts?blackout_date_from=2026-02-14')
    names = {r['name'] for r in response.json()}
    assert 'Nordic Valley' not in names
    assert 'Alpine Peak' in names
    assert 'Powder Ridge' in names


def test_blackout_date_to_only_acts_as_open_ended_upper_bound(client):
    # to=2025-12-25 with no from — should exclude Alpine Peak (Dec 25)
    response = client.get('/resorts?blackout_date_to=2025-12-25')
    names = {r['name'] for r in response.json()}
    assert 'Alpine Peak' not in names
    assert 'Nordic Valley' in names


def test_blackout_date_range_resort_with_empty_list_always_passes(client):
    response = client.get('/resorts?blackout_date_from=2025-12-25&blackout_date_to=2025-12-25')
    names = {r['name'] for r in response.json()}
    assert 'Powder Ridge' in names


# --- ltt date range ---


def test_ltt_date_range_excludes_resort_with_date_in_range(client):
    # Dec 25 is in Alpine Peak's LTT blackout list
    response = client.get('/resorts?ltt_date_from=2025-12-25&ltt_date_to=2025-12-25')
    names = {r['name'] for r in response.json()}
    assert 'Alpine Peak' not in names
    assert 'Nordic Valley' in names
    assert 'Powder Ridge' in names


def test_ltt_date_range_no_overlap_returns_all(client):
    response = client.get('/resorts?ltt_date_from=2025-07-04&ltt_date_to=2025-07-04')
    assert len(response.json()) == 3


def test_ltt_date_range_resort_with_empty_ltt_blackout_always_passes(client):
    # Nordic Valley has empty ltt_blackout — should never be excluded
    response = client.get('/resorts?ltt_date_from=2025-12-25&ltt_date_to=2025-12-25')
    names = {r['name'] for r in response.json()}
    assert 'Nordic Valley' in names


# --- ltt_available ---


def test_ltt_available_true(client):
    response = client.get('/resorts?ltt_available=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Alpine Peak', 'Nordic Valley'}


def test_ltt_available_false(client):
    response = client.get('/resorts?ltt_available=false')
    names = {r['name'] for r in response.json()}
    assert names == {'Powder Ridge'}


def test_ltt_available_in_response_shape(client):
    response = client.get('/resorts')
    assert all('ltt_available' in r for r in response.json())


# --- composability ---


def test_ltt_available_and_ltt_date_range_combined(client):
    # Only LTT resorts, but not blacked out on Dec 25
    response = client.get(
        '/resorts?ltt_available=true&ltt_date_from=2025-12-25&ltt_date_to=2025-12-25'
    )
    names = {r['name'] for r in response.json()}
    # Alpine Peak is LTT but blacked out Dec 25 via ltt_date_from/to
    assert names == {'Nordic Valley'}


def test_blackout_and_ltt_date_range_combined(client):
    response = client.get(
        '/resorts?blackout_date_from=2025-12-25&blackout_date_to=2025-12-25'
        '&ltt_date_from=2025-12-25&ltt_date_to=2025-12-25'
    )
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley', 'Powder Ridge'}


def test_all_filter_types_combined(client):
    response = client.get(
        '/resorts?ltt_available=true'
        '&blackout_date_from=2025-12-25&blackout_date_to=2025-12-25'
        '&ltt_date_from=2026-02-14&ltt_date_to=2026-02-14'
    )
    # Alpine Peak: LTT ✓, blacked out Dec 25 (regular) ✗
    # Nordic Valley: LTT ✓, not blacked out Dec 25 ✓, Feb 14 not in ltt_blackout ✓
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley'}

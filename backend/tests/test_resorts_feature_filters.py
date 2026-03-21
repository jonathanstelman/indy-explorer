import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from models import ResortSummary

FAKE_RESORTS = [
    ResortSummary(
        resort_id='id-1',
        name='Alpine Peak',
        region='West',
        city='Denver',
        state='CO',
        country='USA',
        reservation_status='Required',
        indy_page='https://example.com/alpine-peak',
        has_alpine=True,
        has_cross_country=False,
        has_night_skiing=True,
        has_terrain_parks=True,
        is_dog_friendly=False,
        has_snowshoeing=False,
        is_allied=False,
        vertical=3000.0,
        num_trails=100.0,
        num_lifts=15.0,
        trail_length_mi=80.0,
    ),
    ResortSummary(
        resort_id='id-2',
        name='Nordic Valley',
        region='Northeast',
        city='Stowe',
        state='VT',
        country='USA',
        reservation_status='Not Required',
        indy_page='https://example.com/nordic-valley',
        has_alpine=False,
        has_cross_country=True,
        has_night_skiing=False,
        has_terrain_parks=False,
        is_dog_friendly=True,
        has_snowshoeing=True,
        is_allied=True,
        vertical=1200.0,
        num_trails=40.0,
        num_lifts=5.0,
        trail_length_mi=30.0,
    ),
    ResortSummary(
        resort_id='id-3',
        name='Mid Mountain',
        region='West',
        city='Salt Lake City',
        state='UT',
        country='USA',
        reservation_status='Not Required',
        indy_page='https://example.com/mid-mountain',
        has_alpine=True,
        has_cross_country=True,
        has_night_skiing=False,
        has_terrain_parks=True,
        is_dog_friendly=False,
        has_snowshoeing=True,
        is_allied=False,
        vertical=2000.0,
        num_trails=70.0,
        num_lifts=10.0,
        trail_length_mi=None,
    ),
]


@pytest.fixture(autouse=True)
def patch_resorts():
    with patch('main._resorts', FAKE_RESORTS):
        yield


@pytest.fixture
def client():
    return TestClient(app)


# --- Boolean feature flag filters ---


def test_filter_has_alpine_true(client):
    response = client.get('/resorts?has_alpine=true')
    assert response.status_code == 200
    names = {r['name'] for r in response.json()}
    assert names == {'Alpine Peak', 'Mid Mountain'}


def test_filter_has_alpine_false(client):
    response = client.get('/resorts?has_alpine=false')
    assert response.status_code == 200
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley'}


def test_filter_has_cross_country(client):
    response = client.get('/resorts?has_cross_country=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley', 'Mid Mountain'}


def test_filter_has_night_skiing(client):
    response = client.get('/resorts?has_night_skiing=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Alpine Peak'}


def test_filter_has_terrain_parks(client):
    response = client.get('/resorts?has_terrain_parks=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Alpine Peak', 'Mid Mountain'}


def test_filter_is_dog_friendly(client):
    response = client.get('/resorts?is_dog_friendly=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley'}


def test_filter_has_snowshoeing(client):
    response = client.get('/resorts?has_snowshoeing=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley', 'Mid Mountain'}


def test_filter_is_allied(client):
    response = client.get('/resorts?is_allied=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley'}


# --- reservation_required ---


def test_reservation_required_true(client):
    response = client.get('/resorts?reservation_required=true')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Alpine Peak'


def test_reservation_required_false(client):
    response = client.get('/resorts?reservation_required=false')
    assert response.status_code == 200
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley', 'Mid Mountain'}


# --- Numeric range filters ---


def test_min_vertical(client):
    response = client.get('/resorts?min_vertical=2000')
    names = {r['name'] for r in response.json()}
    assert names == {'Alpine Peak', 'Mid Mountain'}


def test_max_vertical(client):
    response = client.get('/resorts?max_vertical=2000')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley', 'Mid Mountain'}


def test_vertical_range(client):
    response = client.get('/resorts?min_vertical=1500&max_vertical=2500')
    names = {r['name'] for r in response.json()}
    assert names == {'Mid Mountain'}


def test_min_trails(client):
    response = client.get('/resorts?min_trails=70')
    names = {r['name'] for r in response.json()}
    assert names == {'Alpine Peak', 'Mid Mountain'}


def test_max_trails(client):
    response = client.get('/resorts?max_trails=40')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley'}


def test_min_lifts(client):
    response = client.get('/resorts?min_lifts=10')
    names = {r['name'] for r in response.json()}
    assert names == {'Alpine Peak', 'Mid Mountain'}


def test_max_lifts(client):
    response = client.get('/resorts?max_lifts=5')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley'}


def test_min_trail_length(client):
    response = client.get('/resorts?min_trail_length=50')
    names = {r['name'] for r in response.json()}
    # Mid Mountain has None trail_length_mi — excluded
    assert names == {'Alpine Peak'}


def test_max_trail_length(client):
    response = client.get('/resorts?max_trail_length=30')
    names = {r['name'] for r in response.json()}
    assert names == {'Nordic Valley'}


def test_range_excludes_null_values(client):
    # Mid Mountain has no trail_length_mi — should be excluded from range filter
    response = client.get('/resorts?min_trail_length=1')
    names = {r['name'] for r in response.json()}
    assert 'Mid Mountain' not in names


# --- Composability ---


def test_bool_and_range_combined(client):
    response = client.get('/resorts?has_alpine=true&max_vertical=2500')
    names = {r['name'] for r in response.json()}
    assert names == {'Mid Mountain'}


def test_bool_and_reservation_combined(client):
    response = client.get('/resorts?has_alpine=true&reservation_required=false')
    names = {r['name'] for r in response.json()}
    assert names == {'Mid Mountain'}

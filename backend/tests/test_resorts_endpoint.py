import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from models import Resort

FAKE_RESORTS = [
    Resort(
        resort_id='id-1',
        name='Vail',
        region='West',
        city='Vail',
        state='CO',
        country='USA',
        reservation_status='required',
        indy_page='https://example.com/vail',
    ),
    Resort(
        resort_id='id-2',
        name='Stowe',
        region='Northeast',
        city='Stowe',
        state='VT',
        country='USA',
        reservation_status='none',
        indy_page='https://example.com/stowe',
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
    ),
]


@pytest.fixture(autouse=True)
def patch_resorts():
    with patch('main._resorts', FAKE_RESORTS):
        yield


@pytest.fixture
def client():
    return TestClient(app)


def test_get_resorts_returns_all(client):
    response = client.get('/resorts')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_resorts_response_shape(client):
    response = client.get('/resorts')
    resort = response.json()[0]
    assert 'resort_id' in resort
    assert 'name' in resort
    assert 'region' in resort
    assert 'latitude' in resort
    assert 'longitude' in resort


def test_search_by_name(client):
    response = client.get('/resorts?search=vail')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Vail'


def test_search_by_state(client):
    response = client.get('/resorts?search=vt')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Stowe'


def test_search_by_country(client):
    response = client.get('/resorts?search=canada')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Tremblant'


def test_search_is_case_insensitive(client):
    response = client.get('/resorts?search=STOWE')
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_single_region(client):
    response = client.get('/resorts?region=West')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Vail'


def test_filter_multiple_regions(client):
    response = client.get('/resorts?region=West&region=Northeast')
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_filter_by_country(client):
    response = client.get('/resorts?country=Canada')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Tremblant'


def test_filter_by_state(client):
    response = client.get('/resorts?state=CO')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Vail'


def test_combined_filters(client):
    response = client.get('/resorts?region=Northeast&country=USA')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['name'] == 'Stowe'


def test_no_match_returns_empty(client):
    response = client.get('/resorts?search=zzznomatch')
    assert response.status_code == 200
    assert response.json() == []

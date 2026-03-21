import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from models import Resort


def make_resort(resort_id, name, **kwargs):
    return Resort(
        resort_id=resort_id,
        name=name,
        region='West',
        reservation_status='Not Required',
        indy_page=f'https://example.com/{resort_id}',
        **kwargs,
    )


FAKE_RESORTS = [
    make_resort(
        'id-1',
        'Peak A',
        pr_total=85.0,
        pr_snow=9.0,
        pr_resiliency=8.0,
        pr_size=7.0,
        pr_terrain_diversity=8.5,
        pr_challenge=9.0,
        pr_lifts=7.5,
        pr_crowd_flow=8.0,
        pr_facilities=7.0,
        pr_navigation=8.0,
        pr_mountain_aesthetic=9.0,
        pr_lodging='yes',
        pr_apres_ski='extensive',
        pr_access_road='good',
        pr_ability_low='beginner',
        pr_ability_high='expert',
    ),
    make_resort(
        'id-2',
        'Peak B',
        pr_total=60.0,
        pr_snow=6.0,
        pr_resiliency=5.0,
        pr_size=6.0,
        pr_terrain_diversity=6.0,
        pr_challenge=6.0,
        pr_lifts=5.0,
        pr_crowd_flow=6.0,
        pr_facilities=6.0,
        pr_navigation=6.0,
        pr_mountain_aesthetic=6.0,
        pr_lodging='limited',
        pr_apres_ski='moderate',
        pr_access_road='acceptable',
        pr_ability_low='intermediate',
        pr_ability_high='advanced',
    ),
    make_resort(
        'id-3',
        'No Rankings',
        # no PR fields — simulates a resort without Peak Rankings data
    ),
]


@pytest.fixture(autouse=True)
def patch_resorts():
    with patch('main._resorts', FAKE_RESORTS):
        yield


@pytest.fixture
def client():
    return TestClient(app)


# --- has_peak_rankings ---


def test_has_peak_rankings_true(client):
    response = client.get('/resorts?has_peak_rankings=true')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A', 'Peak B'}


def test_has_peak_rankings_false(client):
    response = client.get('/resorts?has_peak_rankings=false')
    names = {r['name'] for r in response.json()}
    assert names == {'No Rankings'}


def test_pr_total_and_rank_in_response(client):
    response = client.get('/resorts')
    for r in response.json():
        assert 'pr_total' in r
        assert 'pr_overall_rank' in r


# --- pr_total range ---


def test_pr_total_min(client):
    response = client.get('/resorts?pr_total_min=70')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}


def test_pr_total_max(client):
    response = client.get('/resorts?pr_total_max=70')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak B'}


def test_pr_total_range(client):
    response = client.get('/resorts?pr_total_min=55&pr_total_max=80')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak B'}


def test_pr_total_excludes_null(client):
    response = client.get('/resorts?pr_total_min=1')
    names = {r['name'] for r in response.json()}
    assert 'No Rankings' not in names


# --- per-category score ranges ---


def test_pr_snow_min(client):
    response = client.get('/resorts?pr_snow_min=8')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}


def test_pr_size_max(client):
    response = client.get('/resorts?pr_size_max=6')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak B'}


def test_pr_challenge_range(client):
    response = client.get('/resorts?pr_challenge_min=5&pr_challenge_max=7')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak B'}


def test_category_score_excludes_null(client):
    response = client.get('/resorts?pr_snow_min=1')
    names = {r['name'] for r in response.json()}
    assert 'No Rankings' not in names


# --- categorical multi-value filters ---


def test_pr_lodging_single(client):
    response = client.get('/resorts?pr_lodging=yes')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}


def test_pr_lodging_multi(client):
    response = client.get('/resorts?pr_lodging=yes&pr_lodging=limited')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A', 'Peak B'}


def test_pr_apres_ski(client):
    response = client.get('/resorts?pr_apres_ski=extensive')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}


def test_pr_access_road(client):
    response = client.get('/resorts?pr_access_road=good&pr_access_road=acceptable')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A', 'Peak B'}


def test_pr_ability_low(client):
    response = client.get('/resorts?pr_ability_low=beginner')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}


def test_pr_ability_high(client):
    response = client.get('/resorts?pr_ability_high=expert')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}


def test_categorical_excludes_no_data_resorts(client):
    # 'No Rankings' has no pr_lodging — should not match any value filter
    response = client.get('/resorts?pr_lodging=yes&pr_lodging=limited&pr_lodging=no')
    names = {r['name'] for r in response.json()}
    assert 'No Rankings' not in names


def test_categorical_case_insensitive(client):
    response = client.get('/resorts?pr_lodging=YES')
    names = {r['name'] for r in response.json()}
    assert 'Peak A' in names


# --- composability ---


def test_has_peak_rankings_and_pr_total_min(client):
    response = client.get('/resorts?has_peak_rankings=true&pr_total_min=70')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}


def test_score_range_and_categorical(client):
    response = client.get('/resorts?pr_total_min=50&pr_lodging=limited')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak B'}


def test_multiple_categorical_filters(client):
    response = client.get('/resorts?pr_lodging=yes&pr_apres_ski=extensive')
    names = {r['name'] for r in response.json()}
    assert names == {'Peak A'}

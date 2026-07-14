import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from pydantic import ValidationError

from data import load_resorts
from models import Resort


BASE_KWARGS = dict(
    resort_id='r1',
    name='Test Resort',
    region='Test Region',
    indy_page='https://example.com/test',
    reservation_status='Not Required',
)


def test_negative_acres_is_nulled(caplog):
    with caplog.at_level('WARNING'):
        resort = Resort(**BASE_KWARGS, acres=-5)
    assert resort.acres is None
    assert any('acres' in r.message for r in caplog.records)


def test_acres_within_bounds_is_kept():
    resort = Resort(**BASE_KWARGS, acres=500)
    assert resort.acres == 500


def test_acres_absurdly_large_is_nulled():
    # simulates a scraped value with an extra digit tacked on
    resort = Resort(**BASE_KWARGS, acres=500000)
    assert resort.acres is None


def test_difficulty_over_100_is_nulled():
    resort = Resort(**BASE_KWARGS, difficulty_beginner=150)
    assert resort.difficulty_beginner is None


def test_difficulty_within_bounds_is_kept():
    resort = Resort(**BASE_KWARGS, difficulty_beginner=40)
    assert resort.difficulty_beginner == 40


def test_pr_subscore_of_11_is_kept():
    # Peak Rankings has actually given a resort an 11 (Spinal Tap style)
    resort = Resort(**BASE_KWARGS, pr_snow=11)
    assert resort.pr_snow == 11


def test_pr_subscore_over_11_is_nulled():
    resort = Resort(**BASE_KWARGS, pr_snow=15)
    assert resort.pr_snow is None


def test_pr_rank_of_zero_is_nulled():
    resort = Resort(**BASE_KWARGS, pr_overall_rank=0)
    assert resort.pr_overall_rank is None


def test_pr_total_negative_is_nulled():
    resort = Resort(**BASE_KWARGS, pr_total=-1)
    assert resort.pr_total is None


def test_malformed_optional_url_is_nulled():
    resort = Resort(**BASE_KWARGS, website='not-a-url')
    assert resort.website is None


def test_valid_optional_url_is_kept():
    resort = Resort(**BASE_KWARGS, website='https://example.com')
    assert resort.website == 'https://example.com'


def test_malformed_indy_page_raises():
    kwargs = dict(BASE_KWARGS)
    kwargs['indy_page'] = 'not-a-url'
    with pytest.raises(ValidationError):
        Resort(**kwargs)


def test_load_resorts_still_loads_real_data_without_hard_failures():
    resorts = load_resorts()
    assert len(resorts) > 0

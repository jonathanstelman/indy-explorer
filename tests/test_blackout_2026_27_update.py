"""Mid-season 26/27 sheet updates: Learn to Turn launch rows (issue #159).

Fixtures are real rows copied from Indy's published 26/27 Google Sheets tabs (2026-11-21).
"""

import pandas as pd
import pytest

import utils
from blackout import (
    BLACKOUT_RESORT_NAME_MAP,
    map_sheet_resort_name,
    normalize_additional_dates,
    parse_blackout_sheet,
)
from ltt_blackout import LTT_RESORT_NAME_MAP, parse_ltt_sheet
from utils import get_all_dates_in_range


@pytest.fixture(autouse=True)
def _season_2026_27(monkeypatch):
    monkeypatch.setattr(utils, 'SEASON_START_YEAR', 2026)


@pytest.fixture
def blackout_map():
    return parse_blackout_sheet(pd.read_csv('tests/fixtures/blackout_sheet_2026_27_update.csv'))


@pytest.fixture
def ltt_map():
    return parse_ltt_sheet(pd.read_csv('tests/fixtures/ltt_sheet_2026_27_update.csv'))


# ---- Names ----


@pytest.mark.parametrize(
    'raw, expected',
    [
        ('Belleayre Mountain, NY (Allied Resort)', 'Belleayre Mountain'),
        ('Gore Mountain, NY (Allied Parter)', 'Gore Mountain'),  # sheet typo
        ('Whiteface Mountain, NY (Allied Partner)', 'Whiteface Mountain'),
    ],
)
def test_strip_allied_tag(raw, expected):
    assert utils.strip_sheet_name_suffix(raw) == expected


@pytest.mark.parametrize(
    'raw, name_map, expected',
    [
        ('King Pine Ski Area, NH', 'blackout', 'King Pine'),
        # Indy renamed these in the roster to match the sheet (2026-11-21).
        ('Belleayre Mountain, NY (Allied Resort)', 'blackout', 'Belleayre Mountain'),
        ('Gore Mountain, NY (Allied Parter)', 'blackout', 'Gore Mountain'),
        ('Whiteface Mountain, NY (Allied Partner)', 'blackout', 'Whiteface Mountain'),
        ('Loup Loup, WA', 'ltt', 'Loup Loup Ski Bowl'),
        ('King Pine, NH', 'ltt', 'King Pine'),
        ('Snow Ridge, NY', 'ltt', 'Snow Ridge'),
        ('Bolton Valley Resort, VT', 'ltt', 'Bolton Valley Resort'),
        ('Hockley Valley Resort, ON', 'ltt', 'Hockley Valley Resort'),
        ('Waterville Valley Resort, NH', 'ltt', 'Waterville Valley Resort'),
        ('Greek Peak Mountain Resort, NY', 'ltt', 'Greek Peak Mountain Resort'),
        ('Big Rock, ME', 'ltt', 'Big Rock Mountain'),
    ],
)
def test_updated_sheet_names_map_to_roster(raw, name_map, expected):
    maps = {'blackout': BLACKOUT_RESORT_NAME_MAP, 'ltt': LTT_RESORT_NAME_MAP}
    assert map_sheet_resort_name(raw, maps[name_map]) == expected


def test_allied_partners_and_king_pine_parse_under_roster_names(blackout_map):
    assert {'Belleayre Mountain', 'Gore Mountain', 'Whiteface Mountain', 'King Pine'} <= set(
        blackout_map
    )


# ---- LTT "X" cells ----


def test_ltt_x_cell_means_blackout(ltt_map):
    king_pine = ltt_map['King Pine']
    assert set(king_pine['named_ranges']) == {'MLK Weekend', "President's Weekend"}
    dates = set(king_pine['all_ltt_blackout_dates'])
    assert set(get_all_dates_in_range('2027-01-16', '2027-01-18')) <= dates
    assert set(get_all_dates_in_range('2027-02-13', '2027-02-15')) <= dates
    assert 'X' not in king_pine['notes']


# ---- Malformed "MM-DD,YYYY" range ends ----


@pytest.mark.parametrize(
    'text',
    ['02/13/27-02-21,2027', '02/13/27-02/21,2027'],
)
def test_range_end_with_comma_before_year(text):
    assert normalize_additional_dates(text) == get_all_dates_in_range('2027-02-13', '2027-02-21')


def test_belleayre_keeps_presidents_week_range(blackout_map):
    dates = set(blackout_map['Belleayre Mountain']['all_blackout_dates'])
    assert set(get_all_dates_in_range('2027-02-13', '2027-02-21')) <= dates


# ---- Lift-ticket "Partial (See Additional)" ----


def test_partial_cell_uses_only_additional_dates(blackout_map):
    """King Pine: X on MLK/Presidents; Partial elsewhere, with the dates in Additional."""
    king_pine = blackout_map['King Pine']
    assert set(king_pine['named_ranges']) == {'MLK Weekend', "President's Weekend"}
    expected = (
        set(get_all_dates_in_range('2026-12-26', '2027-01-03'))
        | set(get_all_dates_in_range('2027-01-16', '2027-01-18'))
        | set(get_all_dates_in_range('2027-02-13', '2027-02-20'))
    )
    assert set(king_pine['all_blackout_dates']) == expected


def test_partial_cell_with_only_a_note_adds_no_dates(blackout_map):
    stoke = blackout_map['Stoke Mountain']
    assert stoke['all_blackout_dates'] == []
    assert stoke['notes'] == ['Stoke Mountain is closed Thanksgiving Day and Christmas Day.']


# ---- Peak Rankings follow the ORDA renames ----


@pytest.mark.parametrize(
    'sheet_name, roster_name',
    [
        ('Belleayre', 'Belleayre Mountain'),
        ('Gore', 'Gore Mountain'),
        ('Whiteface', 'Whiteface Mountain'),
    ],
)
def test_peak_rankings_map_renamed_orda_resorts(sheet_name, roster_name):
    from peak_rankings import build_peak_rankings_map

    rankings = build_peak_rankings_map(pd.DataFrame([{'name': sheet_name, 'total': 40}]))
    assert roster_name in rankings

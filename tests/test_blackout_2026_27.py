"""26/27 season blackout + Learn to Turn parsing (issue #155).

Fixtures are real rows copied from Indy's published 26/27 Google Sheets tabs.
"""

import json

import pandas as pd
import pytest

import utils
from blackout import merge_blackout_into_resorts, normalize_additional_dates, parse_blackout_sheet
from ltt_blackout import merge_ltt_into_resorts, parse_ltt_sheet


@pytest.fixture(autouse=True)
def _season_2026_27(monkeypatch):
    monkeypatch.setattr(utils, 'SEASON_START_YEAR', 2026)


@pytest.fixture
def blackout_map():
    return parse_blackout_sheet(pd.read_csv('tests/fixtures/blackout_sheet_2026_27.csv'))


@pytest.fixture
def ltt_map():
    return parse_ltt_sheet(pd.read_csv('tests/fixtures/ltt_sheet_2026_27.csv'))


# ---- Season years ----


def test_named_range_dates_use_season_start_year():
    assert utils.split_date_range('Dec 19 - Jan 3') == ('2026-12-19', '2027-01-03')
    assert utils.convert_date_string_format('Feb 13') == '2027-02-13'


def test_numeric_dates_without_year_use_season_start_year():
    assert normalize_additional_dates('12/27-12/28') == ['2026-12-27', '2026-12-28']
    assert normalize_additional_dates('2/6') == ['2027-02-06']


# ---- Names ----


@pytest.mark.parametrize(
    'raw, expected',
    [
        ('Pats Peak, NH', 'Pats Peak'),
        ('Hochzeiger Bergbahnen Pitztal AG, ', 'Hochzeiger Bergbahnen Pitztal AG'),
        ('Big Rock, Maine', 'Big Rock'),
        ('Bethel Village Trails, ME (Nordic)', 'Bethel Village Trails'),
        ('Levi, Finland', 'Levi, Finland'),  # a real roster name: country, not a state
        ('Cannon Mountain', 'Cannon Mountain'),
    ],
)
def test_strip_sheet_name_suffix(raw, expected):
    assert utils.strip_sheet_name_suffix(raw) == expected


def test_blackout_sheet_names_are_normalized(blackout_map):
    assert '49 Degrees North' in blackout_map  # "49° North Mountain Resort, WA" + name map
    assert 'Brundage Mountain Resort' in blackout_map
    assert 'Hochzeiger Bergbahnen Pitztal AG' in blackout_map


# ---- Lift-ticket blackouts ----


def test_christmas_range_spans_into_next_year(blackout_map):
    dates = blackout_map['49 Degrees North']['all_blackout_dates']
    assert '2026-12-19' in dates and '2027-01-03' in dates
    assert not any(d.startswith('2025') or d.startswith('2026-01') for d in dates)


def test_additional_dates_split_on_and(blackout_map):
    dates = blackout_map['Brundage Mountain Resort']['all_blackout_dates']
    assert '2027-01-16' in dates and '2027-02-13' in dates
    big_white = blackout_map['Big White Ski Resort']['all_blackout_dates']
    assert '2027-02-16' in big_white and '2027-03-21' in big_white


def test_blackouts_end_after_trims_later_dates(blackout_map):
    shawnee = blackout_map['Shawnee Mountain Ski Area']
    # Peak Saturdays (Jan 9 - Mar 6) is X, but "All blackouts end after 3/1/2027"
    assert '2027-02-27' in shawnee['all_blackout_dates']
    assert '2027-03-06' not in shawnee['all_blackout_dates']
    assert 'All blackouts end after 3/1/2027' in shawnee['notes']


def test_closure_text_in_range_cell_becomes_note_not_dates(blackout_map):
    eagle = blackout_map['Eagle Point']
    assert eagle['all_blackout_dates'] == []
    assert 'CLOSED FOR 26/27 DUE TO WILDFIRE' in eagle['notes']


def test_fully_parsed_additional_dates_add_no_note(blackout_map):
    assert blackout_map['Brundage Mountain Resort']['notes'] == []


# ---- Additional-dates edge cases ----


def test_availability_windows_produce_no_dates():
    """These say when the pass CAN be used; turning them into blackouts inverts them."""
    for text in [
        'Only available on Saturdays and Sundays, subject to availability.',
        'Valid only Opening Day-12/24/2026 (daily) and 3/1/2027-Closing Day (Mon-Thu only)',
        'Winter4Kids is only open to Indy Passholders for two days this season: '
        '12/20/2026 & 3/7/2027',
    ]:
        assert normalize_additional_dates(text, '2026-12-19', '2027-03-07') == []


def test_weekday_scoped_ranges():
    out = normalize_additional_dates(
        'Saturdays 11/28/2026-3/27/2027; Sundays 11/29/2026-3/28/2027; 2/13/2027-2/21/2027'
    )
    assert '2026-11-28' in out  # Saturday
    assert '2026-11-29' in out  # Sunday
    assert '2026-11-30' not in out  # Monday, outside the 2/13-2/21 range
    assert '2027-02-17' in out  # Wednesday, inside 2/13-2/21
    assert '2027-03-28' in out


def test_unparseable_part_does_not_crash_or_drop_the_rest():
    out = normalize_additional_dates(
        '12/1/2026-12/27/2026, 12/31/2026-1/1/2027, ALL JAN & FEB MONDAY-FRIDAY, '
        '2/27/2027-2/28/2027'
    )
    assert '2026-12-01' in out and '2027-01-01' in out and '2027-02-28' in out


# ---- Learn to Turn ----


def test_ltt_names_and_tbd_rows_kept(ltt_map):
    assert 'Bethel Village Trails' in ltt_map  # "(Nordic)" suffix stripped
    marquette = ltt_map['Marquette Mountain']  # all cells TBD — still offers LTT
    assert marquette['ltt_available'] is True
    assert marquette['all_ltt_blackout_dates'] == []
    assert any('TBD' in n for n in marquette['notes'])


def test_ltt_reads_renamed_additional_column(ltt_map):
    dates = ltt_map['Bolton Valley Resort']['all_ltt_blackout_dates']
    assert '2026-11-28' in dates  # from "Saturdays 11/28/2026-..." in Additional


def test_ltt_availability_window_is_a_note_not_dates(ltt_map):
    holiday = ltt_map['Mt. Holiday']
    assert holiday['all_ltt_blackout_dates'] == []
    assert any('Only available on Saturdays and Sundays' in n for n in holiday['notes'])


def test_ltt_end_after_applies_partial_ranges_then_trims(ltt_map):
    """Shawnee LTT: peak weekends are Partial with 'All blackouts end after March 1'."""
    dates = ltt_map['Shawnee Mountain Ski Area']['all_ltt_blackout_dates']
    assert '2027-02-27' in dates  # Peak Saturday before the cutoff
    assert '2027-03-06' not in dates


# ---- Merge ----


def test_notes_merged_as_json_lists(blackout_map, ltt_map):
    resorts = pd.DataFrame([{'name': 'Eagle Point'}, {'name': 'Mt. Holiday'}])
    out = merge_ltt_into_resorts(merge_blackout_into_resorts(resorts, blackout_map), ltt_map)
    out = out.set_index('name')
    assert json.loads(out.loc['Eagle Point', 'blackout_notes']) == [
        'CLOSED FOR 26/27 DUE TO WILDFIRE'
    ]
    assert json.loads(out.loc['Mt. Holiday', 'blackout_notes']) == []
    assert len(json.loads(out.loc['Mt. Holiday', 'ltt_blackout_notes'])) == 1


@pytest.mark.parametrize(
    'raw, name_map, expected',
    [
        # Stripping ", ID" would otherwise send this to the Vermont "Magic Mountain".
        ('Magic Mountain Ski Resort, ID', 'blackout', 'Magic Mountain Idaho'),
        ('Magic Mountain, VT', 'ltt', 'Magic Mountain'),
        ('Greak Peak Mountain Resort, NY', 'ltt', 'Greek Peak Mountain Resort'),  # sheet typo
        ('Black Mountain, NH', 'ltt', 'Black Mountain Ski Area'),
        ('Woodstock Inn & Resort Nordic Center, VT (Nordic)', 'ltt', 'Woodstock Nordic Center'),
    ],
)
def test_26_27_sheet_names_map_to_roster(raw, name_map, expected):
    from blackout import BLACKOUT_RESORT_NAME_MAP, map_sheet_resort_name
    from ltt_blackout import LTT_RESORT_NAME_MAP

    maps = {'blackout': BLACKOUT_RESORT_NAME_MAP, 'ltt': LTT_RESORT_NAME_MAP}
    assert map_sheet_resort_name(raw, maps[name_map]) == expected


# ---- Same-named resorts (two "Powder Ridge" resorts: Kimball, MN and Middlefield, CT) ----


def _powder_ridges():
    return pd.DataFrame(
        [
            {'name': 'Powder Ridge', 'location_name': 'Middlefield, Connecticut'},
            {'name': 'Powder Ridge', 'location_name': 'Kimball, MN, USA'},
        ]
    )


def test_ltt_powder_ridge_ct_maps_to_one_resort(ltt_map):
    from blackout import map_sheet_resort_name
    from ltt_blackout import LTT_RESORT_NAME_MAP

    key = map_sheet_resort_name('Powder Ridge, CT', LTT_RESORT_NAME_MAP)
    out = merge_ltt_into_resorts(_powder_ridges(), {key: ltt_map['Marquette Mountain']})
    by_loc = out.set_index('location_name')
    assert bool(by_loc.loc['Middlefield, Connecticut', 'ltt_available']) is True
    assert bool(by_loc.loc['Kimball, MN, USA', 'ltt_available']) is False


def test_plain_name_shared_by_two_resorts_is_not_applied_to_either(blackout_map, caplog):
    entry = blackout_map['49 Degrees North']
    with caplog.at_level('WARNING'):
        out = merge_blackout_into_resorts(_powder_ridges(), {'Powder Ridge': entry})
    assert (out['blackout_count'] == 0).all()
    assert any('Powder Ridge' in r.message and 'ambiguous' in r.message for r in caplog.records)

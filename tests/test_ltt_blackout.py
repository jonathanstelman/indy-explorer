import json
import pandas as pd
import pytest

from src.ltt_blackout import (
    parse_ltt_sheet,
    merge_ltt_into_resorts,
    _fix_cross_year_numeric_ranges,
    _normalize_ltt_additional_dates,
)


FIXTURE_PATH = 'tests/fixtures/ltt_sheet.csv'


def load_fixture() -> pd.DataFrame:
    return pd.read_csv(FIXTURE_PATH)


def test_parse_ltt_sheet_blackout_only():
    df = load_fixture()
    mapping = parse_ltt_sheet(df)

    assert 'Resort Blackout' in mapping
    info = mapping['Resort Blackout']
    assert info['ltt_available'] is True
    # Christmas/New Years Dec 20-Jan 4 and MLK Jan 17-19 should both be covered
    assert '2025-12-25' in info['all_ltt_blackout_dates']
    assert '2026-01-17' in info['all_ltt_blackout_dates']
    # Peak Saturdays was NO BLACKOUT — none of those dates should appear
    assert '2026-01-10' not in info['all_ltt_blackout_dates']  # Jan 10 is a Sat but NO BLACKOUT


def test_parse_ltt_sheet_no_blackout():
    df = load_fixture()
    mapping = parse_ltt_sheet(df)

    assert 'Resort No Blackout' in mapping
    info = mapping['Resort No Blackout']
    assert info['ltt_available'] is True
    assert info['all_ltt_blackout_dates'] == []
    assert info['named_ranges'] == []


def test_parse_ltt_sheet_partial_only_uses_additional():
    """PARTIAL (SEE ADDITIONAL) should NOT add the full named range; only additional dates apply."""
    df = load_fixture()
    mapping = parse_ltt_sheet(df)

    assert 'Resort Partial' in mapping
    info = mapping['Resort Partial']
    assert info['ltt_available'] is True

    # Christmas/New Years is PARTIAL → full range (Dec 20-Jan 4) should NOT be wholesale added
    # Dec 20 is in the range but NOT in the additional dates — should be absent
    assert '2025-12-20' not in info['all_ltt_blackout_dates']
    # MLK Weekend is BLACKOUT → Jan 17-19 should be present
    assert '2026-01-17' in info['all_ltt_blackout_dates']
    # Additional dates 12/26/25-01/02/2026 should be present
    assert '2025-12-26' in info['all_ltt_blackout_dates']
    assert '2026-01-02' in info['all_ltt_blackout_dates']
    # Jan 3 is NOT in the additional range
    assert '2026-01-03' not in info['all_ltt_blackout_dates']


def test_parse_ltt_sheet_all_weekends_in_additional():
    """'All weekends' in the additional column should expand to weekend dates in season range."""
    df = load_fixture()
    mapping = parse_ltt_sheet(df)

    assert 'Resort All Weekends' in mapping
    info = mapping['Resort All Weekends']
    # Christmas/New Years is BLACKOUT (Dec 20-Jan 4) → all those dates included
    assert '2025-12-20' in info['all_ltt_blackout_dates']
    # Additional 'All weekends' expands to Sat/Sun within the full season range.
    # Jan 10 is a Saturday (in Peak Saturdays range, which is NO BLACKOUT but is used as
    # season bounds) — it should appear via the weekend expansion.
    assert '2026-01-10' in info['all_ltt_blackout_dates']
    # Jan 11 is Sunday
    assert '2026-01-11' in info['all_ltt_blackout_dates']
    # Jan 12 is Monday — not a weekend, should NOT be added by "All weekends"
    # (Jan 12 is also outside the Christmas/New Years BLACKOUT range)
    assert '2026-01-12' not in info['all_ltt_blackout_dates']


def test_parse_ltt_sheet_deduplication():
    """When a resort appears twice, keep the row with BLACKOUT/NO BLACKOUT values."""
    df = load_fixture()
    mapping = parse_ltt_sheet(df)

    assert 'Resort Duplicate' in mapping
    info = mapping['Resort Duplicate']
    # The data row has BLACKOUT for Christmas, so Dec 25 should be present
    assert '2025-12-25' in info['all_ltt_blackout_dates']
    # Additional date 01/04/2026 should be present
    assert '2026-01-04' in info['all_ltt_blackout_dates']


def test_parse_ltt_sheet_no_survey_skipped():
    """Rows where all named-range cells are 'No Survey' should be excluded from the map."""
    df = load_fixture()
    mapping = parse_ltt_sheet(df)

    assert 'Resort No Survey' not in mapping


def test_parse_ltt_sheet_applies_name_map():
    """LTT_RESORT_NAME_MAP should remap resort names correctly."""
    df = pd.DataFrame(
        {
            'PARTICIPATING INDY LEARN TO TURN RESORT (NO ACCESS UNLESS RESORT IS LISTED)': [
                "Nub's Nob Ski Resort",
                'Smokey Mountains Ski Club',
                'Shawnee Mountain',
            ],
            "Christmas/New Years\nDec 20 - Jan 4": ['BLACKOUT', 'NO BLACKOUT', 'BLACKOUT'],
            'Additional Blackout Dates/Details': ['', '', ''],
        }
    )
    mapping = parse_ltt_sheet(df)

    # "Nub's Nob Ski Resort" should be remapped to 'Nubs Nob'
    assert 'Nubs Nob' in mapping
    assert "Nub's Nob Ski Resort" not in mapping

    # 'Smokey Mountains Ski Club' is mapped to None — should be excluded
    assert 'Smokey Mountains Ski Club' not in mapping

    # 'Shawnee Mountain' has no entry in LTT_RESORT_NAME_MAP — stays as-is
    assert 'Shawnee Mountain' in mapping


def test_merge_ltt_into_resorts():
    df = load_fixture()
    ltt_map = parse_ltt_sheet(df)

    resorts_df = pd.DataFrame(
        {
            'name': [
                'Resort Blackout',
                'Resort No Blackout',
                'Resort Partial',
                'Unknown Resort',
            ]
        }
    )
    merged = merge_ltt_into_resorts(resorts_df, ltt_map)

    assert 'ltt_available' in merged.columns
    assert 'ltt_blackout_all_dates' in merged.columns
    assert 'ltt_blackout_count' in merged.columns

    # LTT resort should be marked available
    assert merged.loc[merged['name'] == 'Resort Blackout', 'ltt_available'].iloc[0] == True

    # Unknown resort should not be LTT-available
    unknown_row = merged.loc[merged['name'] == 'Unknown Resort']
    assert unknown_row['ltt_available'].iloc[0] == False
    assert unknown_row['ltt_blackout_count'].iloc[0] == 0
    assert json.loads(unknown_row['ltt_blackout_all_dates'].iloc[0]) == []

    # No-blackout LTT resort: available but zero blackout dates
    no_bo = merged.loc[merged['name'] == 'Resort No Blackout']
    assert no_bo['ltt_available'].iloc[0] == True
    assert no_bo['ltt_blackout_count'].iloc[0] == 0


def test_fix_cross_year_numeric_ranges():
    # December start, January end with 2-digit year — needs year correction
    assert '12/26/25-1/2/26' in _fix_cross_year_numeric_ranges('12/26-1/2/26')

    # Same-month range — no change needed
    result = _fix_cross_year_numeric_ranges('2/16-2/20/26')
    assert result == '2/16-2/20/26'

    # Already has explicit start year — no change
    result = _fix_cross_year_numeric_ranges('12/26/25-1/2/26')
    assert '12/26/25-1/2/26' in result


def test_normalize_ltt_additional_dates_cross_year():
    """End-to-end: '12/26-1/2/26' should produce the correct Dec 26-Jan 2 date range."""
    dates = _normalize_ltt_additional_dates('12/26-1/2/26')
    assert '2025-12-26' in dates
    assert '2026-01-02' in dates
    assert '2025-12-27' in dates

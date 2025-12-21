import json
import pandas as pd

from src.blackout import (
    normalize_additional_dates,
    parse_blackout_sheet,
    merge_blackout_into_resorts,
)
from src.utils import filter_dates_for_weekday, get_all_dates_in_range


def test_normalize_additional_dates():
    s = "Dec 25"
    out = normalize_additional_dates(s)
    assert "2025-12-25" in out

    s2 = "Jan 2 - Jan 3, Feb 1"
    out2 = normalize_additional_dates(s2)
    assert "2026-01-02" in out2
    assert "2026-01-03" in out2
    assert "2026-02-01" in out2

    assert normalize_additional_dates("") == []

    s3 = "Dec 28, Jan 4, 11, 18, 25, Feb 1"
    out3 = normalize_additional_dates(s3)
    assert "2025-12-28" in out3
    assert "2026-01-11" in out3
    assert "2026-02-01" in out3

    s4 = "Dec 21 - Dec 22; Dec 28 - Dec 29; Jan 4 - Jan 5"
    out4 = normalize_additional_dates(s4)
    assert "2025-12-21" in out4
    assert "2025-12-22" in out4
    assert "2025-12-28" in out4
    assert "2025-12-29" in out4
    assert "2026-01-04" in out4
    assert "2026-01-05" in out4

    season_start = "2025-12-21"
    season_end = "2026-01-05"
    expected_weekends = set(
        filter_dates_for_weekday(get_all_dates_in_range(season_start, season_end), 5)
    )
    expected_weekends.update(
        filter_dates_for_weekday(get_all_dates_in_range(season_start, season_end), 6)
    )
    out5 = normalize_additional_dates(
        "All weekends", season_start=season_start, season_end=season_end
    )
    assert expected_weekends.issubset(set(out5))

    out6 = normalize_additional_dates("All weekends")
    assert out6 == []


def test_parse_blackout_sheet_and_merge(tmp_path):
    csv_path = "tests/fixtures/blackout_sheet.csv"
    df = pd.read_csv(csv_path)

    mapping = parse_blackout_sheet(df)

    assert "Resort A" in mapping
    assert mapping["Resort A"]["named_ranges"] == ["Peak Saturdays"]
    # Dec 25 should be present
    assert "2025-12-25" in mapping["Resort A"]["all_blackout_dates"]

    assert "Resort B" in mapping
    assert mapping["Resort B"]["named_ranges"] == ["Peak Sundays"]
    assert "2026-01-02" in mapping["Resort B"]["all_blackout_dates"]

    # Merge into a small resorts df
    resorts_df = pd.DataFrame({"name": ["Resort A", "Resort B", "Resort C", "Unknown Resort"]})
    merged = merge_blackout_into_resorts(resorts_df, mapping)

    # check added columns
    assert "blackout_named_ranges" in merged.columns
    assert (
        merged.loc[merged["name"] == "Resort A", "blackout_named_ranges"].iloc[0]
        == "Peak Saturdays"
    )

    # unknown resort -> empty
    assert merged.loc[merged["name"] == "Unknown Resort", "blackout_count"].iloc[0] == 0


def test_parse_blackout_sheet_applies_name_map():
    df = pd.DataFrame(
        {
            "Resort": ["Shawnee Mountain", "Buck Hill", "X = Blackout Date"],
            "Peak Saturdays\nDec 6 - Dec 13": ["X", "X", "X"],
            "Additional Blackout Dates": ["", "", ""],
        }
    )

    mapping = parse_blackout_sheet(df)

    assert "Shawnee Mountain Ski Area" in mapping
    assert "Buck Hill" not in mapping
    assert "X = Blackout Date" not in mapping

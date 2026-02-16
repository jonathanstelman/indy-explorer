"""LTT (Learn To Turn) blackout dates parsing helpers.

This module parses the published Google Sheets CSV (cached locally) that contains
named LTT blackout date ranges and per-resort flags indicating which ranges apply.

The LTT sheet uses different cell values than the regular blackout sheet:
  - 'BLACKOUT'              → apply all dates in the named range
  - 'PARTIAL (SEE ADDITIONAL)' → do NOT apply the named range; only the additional
                                  dates column contains the actual blackout dates
  - 'NO BLACKOUT'           → no blackout for this range
  - 'No Survey' / blank     → skip (no data)

Public API:
- parse_ltt_sheet(df: pd.DataFrame) -> dict[str, dict]
    Returns a mapping of resort name -> {
        'ltt_available': True,
        'named_ranges': list[str],
        'additional_dates': list[str],
        'all_ltt_blackout_dates': list[str]  # ISO YYYY-MM-DD
    }
- merge_ltt_into_resorts(resorts_df, ltt_map) -> pd.DataFrame
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from src.blackout import normalize_additional_dates, _parse_named_ranges
    from src.utils import get_all_dates_in_range
except ModuleNotFoundError:
    from blackout import normalize_additional_dates, _parse_named_ranges
    from utils import get_all_dates_in_range

LTT_GSHEET_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTUXA5uhe2QwuQvCTpaSpIQmNNWIAp4gADGo5DIUeDwMOfgg9a8nEMU2K_4J9_24E2dGaLgbBnplpqg/pub?gid=484077440&single=true&output=csv'

logger = logging.getLogger(__name__)


LTT_RESORT_NAME_MAP = {
    # Sheet name → resorts_raw.json name
    'Bear Creek Mountain Resort': 'Bear Creek',
    'Berkshire East': 'Berkshire East Mountain Resort',
    'Black Mountain Ski Area, NH': 'Black Mountain Ski Area',
    'Blacktail Mountain Ski Area': 'Blacktail Mountain Resort',
    'Bluewood': 'Ski Bluewood',
    'Eagle Point Resort': 'Eagle Point',
    'Jay Peak': 'Jay Peak Resort',
    'Manning Park Resort': 'Manning Park',
    'Marquette Mountain Resort': 'Marquette Mountain',
    'Mt. Abram Ski Resort & Bike Park': 'Mt. Abram',
    "Nub's Nob Ski Area": 'Nubs Nob',
    "Nub's Nob Ski Resort": 'Nubs Nob',
    'Ski Big Bear at Masthope Mountain': 'Ski Big Bear',
    'Sunlight Mountain': 'Sunlight Mountain Resort',
    'Titus Mountain Family Ski Center': 'Titus Mountain',
    'Waterville Valley': 'Waterville Valley Resort',
    # Names not present in resorts_raw.json — explicitly ignored
    'Smokey Mountains Ski Club': None,
}


def get_ltt_dates_from_google_sheets(
    sheet_url: Optional[str] = LTT_GSHEET_URL,
    read_mode: str = 'live',
    cache_path: str = 'data/ltt_dates_raw.csv',
) -> pd.DataFrame:
    """Fetch LTT blackout dates from a published Google Sheets URL (with optional cache)."""
    if read_mode == 'cache' and os.path.exists(cache_path):
        logger.info('Loading LTT dates from cached CSV file: %s', cache_path)
        return pd.read_csv(cache_path)

    logger.info('Fetching LTT dates from Google Sheets URL: %s', sheet_url)
    return pd.read_csv(sheet_url)


def _normalize_ltt_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize LTT sheet columns, renaming the long first column header to 'Resort'."""
    normalized = []
    for i, col in enumerate(df.columns):
        if i == 0:
            normalized.append('Resort')
        else:
            col_str = '' if col is None else str(col).strip()
            normalized.append(col_str)
    out = df.copy()
    out.columns = normalized
    return out


_LTT_DATA_VALUES = {'BLACKOUT', 'NO BLACKOUT', 'PARTIAL (SEE ADDITIONAL)', 'PARTIAL'}


def _is_valid_data_row(row: pd.Series, named_range_cols: List[str]) -> bool:
    """Return True if the row has at least one real LTT data value in the named-range columns."""
    for col in named_range_cols:
        val = row.get(col)
        if isinstance(val, str) and val.strip().upper() in _LTT_DATA_VALUES:
            return True
    return False


def _deduplicate_ltt_resorts(df: pd.DataFrame, named_range_cols: List[str]) -> pd.DataFrame:
    """For resort names that appear more than once, keep only the valid data row.

    The duplicate rows are either empty, contain holiday-label strings (e.g.,
    'Christmas/New Year') or all-'No Survey' values. The data row has BLACKOUT /
    NO BLACKOUT / PARTIAL values in the named-range columns.
    """
    resort_col = df['Resort']
    seen: dict[str, int] = {}  # name -> first valid row index
    drop_indices = []

    for idx, row in df.iterrows():
        name = str(row['Resort']).strip() if pd.notna(row['Resort']) else ''
        if not name:
            drop_indices.append(idx)
            continue

        is_valid = _is_valid_data_row(row, named_range_cols)

        if name not in seen:
            seen[name] = idx
            if not is_valid:
                drop_indices.append(idx)
        else:
            prev_idx = seen[name]
            if is_valid:
                # Replace the previously recorded (invalid) row with this valid one
                drop_indices.append(prev_idx)
                seen[name] = idx
            else:
                drop_indices.append(idx)

    return df.drop(index=drop_indices)


def _fix_cross_year_numeric_ranges(text: str) -> str:
    """Fix numeric date ranges where December start month is paired with a January-ish end
    that carries an explicit year (e.g. '12/26-1/2/26' → '12/26/25-1/2/26').

    Without this fix, the start date would inherit the end year (2026) and produce
    2026-12-26, which is after 2026-01-02 and would yield an empty range.
    """
    # Match: start MM/DD (no year, not preceded by / or digit) - end MM/DD/YY or MM/DD/YYYY
    # Negative lookbehind (?<![/\d]) ensures we don't match a 2-part slice of a 3-part date.
    # Negative lookahead (?!/\d) ensures start is truly 2-part (no trailing /year).
    pattern = re.compile(r'(?<![/\d])(\d{1,2}/\d{1,2})(?!/\d)\s*-\s*(\d{1,2}/\d{1,2}/(\d{2,4}))\b')

    def _fix_match(m: re.Match) -> str:
        start_raw, end_raw, year_raw = m.group(1), m.group(2), m.group(3)
        start_parts = start_raw.split('/')
        end_parts = end_raw.split('/')
        try:
            start_month = int(start_parts[0])
            end_month = int(end_parts[0])
            end_year = int(year_raw) + (2000 if len(year_raw) == 2 else 0)
        except ValueError:
            return m.group(0)

        if start_month > end_month:
            # Cross-year range: start year is one less than end year
            start_year = end_year - 1
            short_start_year = str(start_year)[-2:]
            return f'{start_raw}/{short_start_year}-{end_raw}'
        return m.group(0)

    return pattern.sub(_fix_match, text)


def _normalize_ltt_additional_dates(
    text: str, season_start: Optional[str] = None, season_end: Optional[str] = None
) -> List[str]:
    """Wrapper around normalize_additional_dates that pre-processes cross-year numeric ranges."""
    if not text or (isinstance(text, float) and pd.isna(text)):
        return []
    fixed = _fix_cross_year_numeric_ranges(str(text))
    return normalize_additional_dates(fixed, season_start=season_start, season_end=season_end)


def parse_ltt_sheet(df_raw: pd.DataFrame) -> Dict[str, Dict]:
    """Given an LTT sheet DataFrame, return a per-resort LTT blackout mapping.

    The returned mapping keys are normalized resort names (via LTT_RESORT_NAME_MAP).
    Resorts not visible in the HTML view but present in the CSV (hidden rows, 'No Survey'
    rows) are filtered out by _deduplicate_ltt_resorts.

    Example return value:
    {
        "Pats Peak": {
            "ltt_available": True,
            "named_ranges": ["Christmas/New Years", "Peak Saturdays"],
            "additional_dates": ["2026-01-17"],
            "all_ltt_blackout_dates": ["2025-12-20", ..., "2026-01-17"]
        },
        ...
    }
    """
    df_raw = _normalize_ltt_columns(df_raw)
    # Parse named ranges from headers (reuses blackout logic — same header format)
    named_ranges = _parse_named_ranges(df_raw)

    named_range_col_names = list(named_ranges.keys())

    # Deduplicate using the FULL column names (with \n date range) since df_raw hasn't been
    # renamed yet. Named-range columns are those whose header contains \n or \\n.
    named_range_full_cols = [
        c for c in df_raw.columns if c != 'Resort' and ('\n' in str(c) or '\\n' in str(c))
    ]
    df_raw = _deduplicate_ltt_resorts(df_raw, named_range_full_cols)

    # Rename columns to short names for lookup
    def _header_name(header: str) -> str:
        if '\n' in header:
            return header.split('\n', 1)[0]
        if '\\n' in header:
            return header.split('\\n', 1)[0]
        return header

    ltt_df = df_raw.copy()
    ltt_df.columns = [_header_name(c) for c in ltt_df.columns]
    ltt_df = ltt_df.set_index('Resort')

    all_named_dates = [d for info in named_ranges.values() for d in info.get('dates', [])]
    season_start = min(all_named_dates) if all_named_dates else None
    season_end = max(all_named_dates) if all_named_dates else None

    resort_map: Dict[str, Dict] = {}

    for resort_name, row in ltt_df.iterrows():
        if not resort_name or (isinstance(resort_name, float) and pd.isna(resort_name)):
            continue
        resort_name = str(resort_name).strip()
        mapped_name = LTT_RESORT_NAME_MAP.get(resort_name, resort_name)
        if mapped_name is None:
            continue

        # Skip rows where all named-range cells are 'No Survey' or blank
        all_cells = [str(row.get(name, '')).strip().upper() for name in named_range_col_names]
        if all(c in ('NO SURVEY', '', 'NAN') for c in all_cells):
            logger.debug('Skipping LTT resort with no survey data: %s', resort_name)
            continue

        named_applied: List[str] = []
        all_dates: set = set()

        for name, info in named_ranges.items():
            try:
                cell = row.get(name)
            except Exception:
                cell = None
            if not isinstance(cell, str):
                continue
            cell_upper = cell.strip().upper()
            if cell_upper == 'BLACKOUT':
                # Apply full named range
                named_applied.append(name)
                all_dates.update(info['dates'])
            # PARTIAL (SEE ADDITIONAL): named range does NOT apply wholesale;
            # the additional dates column will contain the specific blackout dates.
            # NO BLACKOUT / blank / No Survey: skip.

        additional = _normalize_ltt_additional_dates(
            row.get('Additional Blackout Dates/Details'),
            season_start=season_start,
            season_end=season_end,
        )
        all_dates.update(additional)

        resort_map[mapped_name] = {
            'ltt_available': True,
            'named_ranges': sorted(named_applied),
            'additional_dates': sorted(additional),
            'all_ltt_blackout_dates': sorted(all_dates),
        }

    return resort_map


def merge_ltt_into_resorts(resorts_df: pd.DataFrame, ltt_map: Dict[str, Dict]) -> pd.DataFrame:
    """Merge LTT info into `resorts_df` (by `name` column).

    Adds the following columns:
      - ltt_available (bool)
      - ltt_blackout_all_dates (JSON list string)
      - ltt_blackout_count (int)

    Resorts not found in the LTT map get ltt_available=False and empty blackout lists.
    """

    def _map_for_name(name: str) -> Tuple[bool, str, int]:
        info = ltt_map.get(name)
        if not info:
            return False, '[]', 0
        all_dates = json.dumps(info.get('all_ltt_blackout_dates', []))
        count = len(info.get('all_ltt_blackout_dates', []))
        return True, all_dates, count

    mapped = resorts_df['name'].apply(lambda n: _map_for_name(n))
    resorts_df['ltt_available'] = mapped.apply(lambda t: t[0])
    resorts_df['ltt_blackout_all_dates'] = mapped.apply(lambda t: t[1])
    resorts_df['ltt_blackout_count'] = mapped.apply(lambda t: t[2])

    missing_in_resorts = sorted(set(ltt_map.keys()) - set(resorts_df['name']))
    if missing_in_resorts:
        logger.warning('LTT resorts missing from resorts_df:')
        for name in missing_in_resorts:
            logger.warning('- %s', name)

    return resorts_df


def print_ltt_name_mismatches(ltt_df_raw: pd.DataFrame) -> None:
    """Print QA summary for LTT sheet resort names vs resorts_raw.json."""
    with open('data/resorts_raw.json', 'r', encoding='utf-8') as json_file:
        resorts_dict = json.load(json_file)
    resorts_df = pd.DataFrame(resorts_dict).transpose()
    ltt_df_raw = _normalize_ltt_columns(ltt_df_raw)

    resorts_set = {str(name).strip() for name in resorts_df['name'].tolist() if name}
    ltt_raw_set = {
        str(name).strip() for name in ltt_df_raw['Resort'].tolist() if name and str(name).strip()
    }

    ltt_mapped = []
    ignored_names = []
    remapped = []
    for name in ltt_raw_set:
        mapped = LTT_RESORT_NAME_MAP.get(name, name)
        if mapped is None:
            ignored_names.append(name)
            continue
        if mapped != name:
            remapped.append((name, mapped))
        ltt_mapped.append(mapped)

    missing_in_resorts = sorted(set(ltt_mapped) - resorts_set)
    missing_in_ltt = sorted(resorts_set - set(ltt_mapped))

    logger.info('LTT name QA summary')
    logger.info('%s', '-' * 30)
    logger.info('Resorts in resorts_raw.json: %d', len(resorts_set))
    logger.info('Raw LTT sheet resort names: %d', len(ltt_raw_set))
    logger.info('Names used after mapping: %d', len(set(ltt_mapped)))

    if ignored_names:
        logger.info('Ignored names (explicitly mapped to None):')
        for name in sorted(ignored_names):
            logger.info('- %s', name)

    if remapped:
        logger.info('Remapped names (sheet -> resorts_raw.json):')
        for raw_name, mapped_name in sorted(remapped, key=lambda t: t[0].lower()):
            logger.info('- %s -> %s', raw_name, mapped_name)

    if missing_in_resorts:
        logger.info('LTT-only names (after mapping, not in resorts_raw.json):')
        for name in missing_in_resorts:
            logger.info('- %s', name)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    ltt_df = get_ltt_dates_from_google_sheets(read_mode='cache')
    ltt_map = parse_ltt_sheet(ltt_df)
    logger.info('Parsed LTT info for %d resorts.', len(ltt_map))
    logger.info('%s', json.dumps(ltt_map, indent=2))


if __name__ == '__main__':
    main()

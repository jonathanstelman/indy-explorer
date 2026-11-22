"""Blackout dates parsing helpers.

This module parses the published Google Sheets CSV (cached locally) that contains
named blackout date ranges and per-resort flags indicating which ranges apply.

Public API:
- parse_blackout_sheet(df: pd.DataFrame) -> dict[str, dict]
    Returns a mapping of resort name -> {
        'named_ranges': list[str],
        'additional_dates': list[str],
        'all_blackout_dates': list[str]  # ISO YYYY-MM-DD
    }
- normalize_additional_dates(text: str) -> list[str]

This module relies on helpers from `src.utils` for date parsing and expansion.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from src.utils import (
        convert_date_string_format,
        filter_dates_for_weekday,
        get_all_dates_in_range,
        season_bounds,
        season_year,
        split_date_range,
        strip_sheet_name_suffix,
    )
except ModuleNotFoundError:
    from utils import (
        convert_date_string_format,
        filter_dates_for_weekday,
        get_all_dates_in_range,
        season_bounds,
        season_year,
        split_date_range,
        strip_sheet_name_suffix,
    )

# BLACKOUT_DATES_AND_RESERVATIONS_URL = 'https://www.indyskipass.com/blackout-dates-reservations'
# 26/27 season tab, embedded on https://www.indyskipass.com/blackout-dates-reservations.
# Previous seasons: 25/26 gid=1762546441, 24/25 gid=1371665852. When switching tabs, bump
# utils.SEASON_START_YEAR too.
BLACKOUT_DATE_GSHEET_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTUXA5uhe2QwuQvCTpaSpIQmNNWIAp4gADGo5DIUeDwMOfgg9a8nEMU2K_4J9_24E2dGaLgbBnplpqg/pub?gid=1360740952&single=true&output=csv'

logger = logging.getLogger(__name__)


BLACKOUT_RESORT_NAME_MAP = {
    '49° North': '49 Degrees North',
    '49° North Mountain Resort': '49 Degrees North',
    'Bear Valley': 'Bear Valley Mountain Resort',
    'Beaver Mountain Ski Area': 'Beaver Mountain',
    'Brundage Mountain': 'Brundage Mountain Resort',
    'Crystal Mountain, MI': 'Crystal Mountain',
    'Detroit Mountain Recreation Area': 'Detroit Mountain',
    'Dodge Ridge Mountain Resort': 'Dodge Ridge',
    'Eagle Point Resort': 'Eagle Point',
    'Hochzeiger Pitztal': 'Hochzeiger Bergbahnen Pitztal AG',
    'Hoodoo Ski Area': 'Hoodoo',
    'Hyland Hills Ski Area': 'Hyland Hills',
    'Kelly Canyon Resort': 'Kelly Canyon',
    'King Pine Ski Area': 'King Pine',
    'Levi Ski Resort': 'Levi, Finland',
    'Magic Mountain Ski Resort': 'Magic Mountain Idaho',  # "..., ID"; plain name is VT
    'Manning Park Resort': 'Manning Park',
    'Manning Park Resort Nordic Centre': 'Manning Park XC',
    'Meadowlark Ski Lodge': 'Meadowlark Ski Resort',
    'Mohawk Mountain Ski Area': 'Mohawk Mountain',
    'Montage Mountain Resorts': 'Montage Mountain',
    'Mont Ripley': 'Mont Ripley Ski Area',
    'Mountain High Resort': 'Mountain High',
    'Mt. La Crosse': 'Mt La Crosse',
    'Mt. Shasta Ski Park': 'Mt. Shasta',
    'Mt. Washington Alpine Resort': 'Mt. Washington',
    "Nub's Nob Ski Area": 'Nubs Nob',
    "Nub's Nob": 'Nubs Nob',
    "Owl's Head": 'Destination Owls Head',
    'Pats Peak Ski Area': 'Pats Peak',
    "Peek'n Peak Resort": 'Peek ‘n Peak',
    'Ragged Mountain Resort': 'Ragged Mountain',
    'Schuss Mountain Shanty Creek': 'Schuss Mountain at Shanty Creek',
    'Shanty Creek Resort': 'Schuss Mountain at Shanty Creek',
    'Silver Mountain Resort': 'Silver Mountain',
    'Spirit Mountain Recreation Area': 'Spirit Mountain',
    'Shawnee Mountain': 'Shawnee Mountain Ski Area',
    'Ski Big Bear at Masthope Mountain': 'Ski Big Bear',
    'Sundown Mountain Resort': 'Sundown Mountain',
    'Terry Peak Ski Area': 'Terry Peak',
    'Tree Tops Ski Resort': 'Treetops Resort',
    'Tussey Mountain Ski Area': 'Tussey Mountain',
    'Waterville Valley': 'Waterville Valley Resort',
    'White Pass Ski Area': 'White Pass',
    # Names present in the blackout sheet but not in resorts.csv (ignored).
    'Buck Hill': None,
    'Sunrise Park': None,
    'Swiss Valley Ski & Snowboard Area': None,
    'X = Blackout Date': None,
}


def get_blackout_dates_from_google_sheets(
    sheet_url: Optional[str] = BLACKOUT_DATE_GSHEET_URL,
    read_mode: str = 'live',
    cache_path: str = 'data/blackout_dates_raw.csv',
) -> pd.DataFrame:
    """Fetch blackout dates from a published Google Sheets URL (with optional cache)."""
    url = sheet_url

    if read_mode == 'cache' and os.path.exists(cache_path):
        logger.info('Loading blackout dates from cached CSV file: %s', cache_path)
        return pd.read_csv(cache_path)

    logger.info('Fetching blackout dates from Google Sheets URL: %s', url)
    return pd.read_csv(url)


def _normalize_blackout_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize blackout sheet columns, ensuring the resort column is named 'Resort'."""
    normalized = []
    for col in df.columns:
        col_str = '' if col is None else str(col).strip()
        if not col_str or (isinstance(col, float) and pd.isna(col)):
            normalized.append('Resort')
        else:
            normalized.append(col_str)
    out = df.copy()
    out.columns = normalized
    return out


def _numeric_date_has_year(date_str: str) -> bool:
    return len(date_str.split('/')) == 3


def _parse_numeric_date(date_str: str, default_year: Optional[int] = None) -> Optional[str]:
    date_str = date_str.strip()
    parts = date_str.split('/')
    if len(parts) < 2:
        return None
    try:
        month = int(parts[0])
        day = int(parts[1])
        if len(parts) == 3:
            year = int(parts[2])
            if year < 100:
                year += 2000
        else:
            if default_year is not None:
                year = default_year
            else:
                year = season_year(month)
        return f'{year:04d}-{month:02d}-{day:02d}'
    except ValueError:
        return None


def _expand_numeric_part(part: str) -> List[str]:
    cleaned = part.split('.', 1)[0].strip()
    if not cleaned:
        return []

    range_match = re.match(
        r'^(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*-\s*(\d{1,2}/\d{1,2}(?:/\d{2,4})?)$',
        cleaned,
    )
    if range_match:
        start_raw, end_raw = range_match.groups()
        end_date = _parse_numeric_date(end_raw)
        if not end_date:
            return []
        end_year = int(end_date.split('-', 1)[0])
        start_year = end_year if not _numeric_date_has_year(start_raw) else None
        start_date = _parse_numeric_date(start_raw, default_year=start_year)
        if not start_date:
            return []
        return get_all_dates_in_range(start_date, end_date)

    single_date = _parse_numeric_date(cleaned)
    return [single_date] if single_date else []


def print_blackout_name_mismatches(blackouts_df_raw: pd.DataFrame) -> None:
    """Print QA summary for blackout sheet resort names vs resorts_raw.json.

    Output includes:
    - Names ignored by mapping (explicitly None)
    - Names remapped to match resorts_raw.json
    - Blackout-only names (after mapping)
    - Resorts missing blackout entries
    """
    with open('data/resorts_raw.json', 'r', encoding='utf-8') as json_file:
        resorts_dict = json.load(json_file)
    resorts_df = pd.DataFrame(resorts_dict).transpose()
    blackouts_df_raw = _normalize_blackout_columns(blackouts_df_raw)

    resorts_set = {str(name).strip() for name in resorts_df['name'].tolist() if name}
    blackout_raw_list = [
        str(name).strip()
        for name in blackouts_df_raw['Resort'].tolist()
        if name and str(name).strip()
    ]
    blackout_raw_set = set(blackout_raw_list)

    blackout_mapped = []
    ignored_names = []
    remapped = []
    for name in blackout_raw_set:
        mapped = BLACKOUT_RESORT_NAME_MAP.get(name, name)
        if mapped is None:
            ignored_names.append(name)
            continue
        if mapped != name:
            remapped.append((name, mapped))
        blackout_mapped.append(mapped)

    missing_in_resorts = sorted(set(blackout_mapped) - resorts_set)
    missing_in_blackout = sorted(resorts_set - set(blackout_mapped))

    logger.info('Blackout name QA summary')
    logger.info('%s', '-' * 30)
    logger.info('Resorts in resorts_raw.json: %d', len(resorts_set))
    logger.info('Raw blackout sheet resort names: %d', len(blackout_raw_set))
    logger.info('Names used after mapping: %d', len(set(blackout_mapped)))

    if ignored_names:
        logger.info('Ignored names (explicitly mapped to None):')
        for name in sorted(ignored_names):
            logger.info('- %s', name)

    if remapped:
        logger.info('Remapped names (sheet -> resorts_raw.json):')
        for raw_name, mapped_name in sorted(remapped, key=lambda t: t[0].lower()):
            logger.info('- %s -> %s', raw_name, mapped_name)

    if missing_in_resorts:
        logger.info('Blackout-only names (after mapping, not in resorts_raw.json):')
        for name in missing_in_resorts:
            logger.info('- %s', name)

    # if missing_in_blackout:
    #     print('\nResorts missing blackout entries (in resorts.csv, not in sheet):')
    #     for name in missing_in_blackout:
    #         print(f'- {name}')

    if not ignored_names and not remapped and not missing_in_resorts and not missing_in_blackout:
        logger.info('Blackout and resort names are in sync.')


def _parse_named_ranges(df: pd.DataFrame) -> Dict[str, Dict]:
    """Parse the column headers that represent named ranges.

    Returns a mapping of named_range -> {'raw_text': str, 'dates': [YYYY-MM-DD,...]}
    """
    df = _normalize_blackout_columns(df)

    def _split_header(header: str) -> Optional[Tuple[str, str]]:
        if "\n" in header:
            return header.split("\n", 1)
        if "\\n" in header:
            return header.split("\\n", 1)
        return None

    named = {}
    for c in df.columns:
        if c in ["Resort", "Additional Blackout Dates"]:
            continue
        # header format: "Name\nMon D - Mon D"
        split_header = _split_header(c)
        if not split_header:
            continue
        name, date_range = split_header
        date_range = re.sub(r'\s*-\s*', ' - ', date_range.strip())
        start_date, end_date = split_date_range(date_range)
        dates = get_all_dates_in_range(start_date, end_date)

        # allow special filtering for named groups
        if name.strip().lower().startswith("peak satur"):
            dates = filter_dates_for_weekday(dates, weekday=5)
        elif name.strip().lower().startswith("peak sund"):
            dates = filter_dates_for_weekday(dates, weekday=6)

        named[name] = {"raw_text": date_range, "dates": dates}

    return named


def _season_weekend_dates(season_start: str, season_end: str) -> List[str]:
    dates = get_all_dates_in_range(season_start, season_end)
    weekend = set(filter_dates_for_weekday(dates, weekday=5))
    weekend.update(filter_dates_for_weekday(dates, weekday=6))
    return sorted(weekend)


# Cells that say when a pass CAN be used ("Only available on Saturdays and Sundays",
# "Valid only Opening Day-12/24/2026 ...") rather than listing blackouts. Their dates are
# the complement within the assumed season (availability_window_blackouts()), and the text
# is also kept as a note, since details like "before 3 PM" can't be drawn.
_AVAILABILITY_WINDOW = re.compile(r'\b(only|available|valid)\b', re.IGNORECASE)
_WEEKDAY_SCOPED = re.compile(r'^(saturdays?|sundays?)\s+(.+)$', re.IGNORECASE)
_WEEKEND_WORDS = re.compile(r'weekend|saturday|sunday', re.IGNORECASE)
_END_AFTER = re.compile(r'blackouts end after\s+(.+?)\s*\.?$', re.IGNORECASE)
_PART_SPLIT = re.compile(r'\s*(?:[;,&]|\band\b)\s*', re.IGNORECASE)
_MONTH_RE = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b')
# Words that parse into dates; anything else left over in a cell is worth showing as a note.
_PARSED_WORDS = re.compile(
    r'\b(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|jun(e)?|jul(y)?|aug(ust)?|'
    r'sep(tember)?|oct(ober)?|nov(ember)?|dec(ember)?|and|all|saturdays?|sundays?|weekends?|'
    r'throughout|the|season)\b',
    re.IGNORECASE,
)


_DAY = r'(mon|tue|wed|thu|fri|sat|sun)[a-z]*'
_DAY_RANGE = re.compile(rf'\b{_DAY}\s*-\s*{_DAY}\b', re.IGNORECASE)
_DAY_WORD = re.compile(rf'\b{_DAY}\b', re.IGNORECASE)
_DAY_INDEX = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
_NUMERIC_DATE = r'\d{1,2}/\d{1,2}(?:/\d{2,4})?'
_NUMERIC_RANGE = re.compile(rf'({_NUMERIC_DATE})\s*-\s*({_NUMERIC_DATE})')
_NUMERIC_SINGLE = re.compile(rf'(?<![\d/]){_NUMERIC_DATE}(?![\d/])')
_MONTH_NAME = r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*'
# "ALL JAN & FEB MONDAY-FRIDAY": weekdays within whole months.
_ALL_MONTHS_DAYS = re.compile(
    rf'\ball\s+({_MONTH_NAME}(?:\s*(?:&|and|,)\s*{_MONTH_NAME})*)\s+{_DAY}\s*-\s*{_DAY}\b',
    re.IGNORECASE,
)


def _weekdays_in(text: str) -> set:
    """Weekday indexes (Mon=0) named in text: "Saturdays and Sundays", "Mon-Thu"."""
    days = set()
    for start, end in _DAY_RANGE.findall(text):
        a, b = _DAY_INDEX[start[:3].lower()], _DAY_INDEX[end[:3].lower()]
        days.update(range(a, b + 1) if a <= b else [*range(a, 7), *range(0, b + 1)])
    for day in _DAY_WORD.findall(_DAY_RANGE.sub(' ', text)):
        days.add(_DAY_INDEX[day[:3].lower()])
    return days


def _weekday(iso_date: str) -> int:
    return datetime.strptime(iso_date, '%Y-%m-%d').weekday()


def _substitute_season_bounds(text: str) -> str:
    """Replace "Opening Day" / "Closing Day" with the assumed season bounds (Nov 1 / May 31)."""
    start, end = season_bounds()
    to_numeric = lambda iso: '{1}/{2}/{0}'.format(*[int(x) for x in iso.split('-')])
    text = re.sub(r'opening\s+day', to_numeric(start), text, flags=re.IGNORECASE)
    return re.sub(r'closing\s+day', to_numeric(end), text, flags=re.IGNORECASE)


# A range end written "02-21,2027" or "02/21,2027" (Belleayre/Gore/Whiteface 26/27): the
# comma would split the year off as its own part, and the dash isn't a date separator.
_COMMA_YEAR_RANGE_END = re.compile(r'-\s*(\d{1,2})[-/](\d{1,2}),\s*(\d{4})\b')


def _fix_comma_year_range_ends(text: str) -> str:
    return _COMMA_YEAR_RANGE_END.sub(r'-\1/\2/\3', text)


def _numeric_dates_in(text: str) -> List[str]:
    """All numeric dates and ranges in a piece of free text."""
    dates: List[str] = []
    for match in _NUMERIC_RANGE.finditer(text):
        dates.extend(_expand_numeric_part(match.group(0)))
    for match in _NUMERIC_SINGLE.finditer(_NUMERIC_RANGE.sub(' ', text)):
        single = _parse_numeric_date(match.group(0))
        if single:
            dates.append(single)
    return dates


def _availability_window(text) -> Optional[Tuple[set, set]]:
    """(allowed dates, explicitly dated allowed dates) for an availability window, or None.

    Each part (split on and/&/,/;) contributes allowed dates: its dates, narrowed to any
    weekdays it names, or, with no dates, those weekdays across the assumed season
    (season_bounds()). Text with "only" but no days or dates ("can only accommodate
    passholders aged 14+") isn't a window.
    """
    if not is_availability_window(text):
        return None
    season = get_all_dates_in_range(*season_bounds())
    allowed: set = set()
    explicit: set = set()
    found = False
    for part in _PART_SPLIT.split(_substitute_season_bounds(str(text))):
        dates = _numeric_dates_in(part)
        days = _weekdays_in(part)
        if dates:
            dated = {d for d in dates if not days or _weekday(d) in days}
            allowed.update(dated)
            explicit.update(dated)
            found = True
        elif days:
            allowed.update(d for d in season if _weekday(d) in days)
            found = True
    return (allowed, explicit) if found else None


def availability_window_blackouts(text: str) -> Optional[List[str]]:
    """Blackout dates implied by an availability window, or None if text isn't one.

    "Valid only Opening Day-12/24/2026 (daily) and 3/1/2027-Closing Day (Mon-Thu only)" ->
    every date in the assumed season outside those windows.
    """
    window = _availability_window(text)
    if window is None:
        return None
    return sorted(set(get_all_dates_in_range(*season_bounds())) - window[0])


def window_open_dates(text) -> set:
    """Dates an availability window explicitly names as open ("only open ... 12/20/2026 &
    3/7/2027"). These override named-range blackouts; weekday-only windows ("available
    Thursdays and Fridays") don't, since Indy also marks their blackout periods."""
    window = _availability_window(text) if isinstance(text, str) else None
    return window[1] if window else set()


def _all_months_weekday_dates(text: str) -> Tuple[List[str], str]:
    """Expand "ALL JAN & FEB MONDAY-FRIDAY" phrases; return (dates, text without them)."""
    dates: List[str] = []
    for match in _ALL_MONTHS_DAYS.finditer(text):
        days = _weekdays_in(match.group(0))
        for month_name in re.findall(_MONTH_NAME, match.group(1), re.IGNORECASE):
            month = datetime.strptime(month_name[:3].title(), '%b').month
            year = season_year(month)
            last = (datetime(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)).day
            month_dates = get_all_dates_in_range(
                f'{year}-{month:02d}-01', f'{year}-{month:02d}-{last:02d}'
            )
            dates.extend(d for d in month_dates if _weekday(d) in days)
    return dates, _ALL_MONTHS_DAYS.sub(' ', text)


def is_availability_window(text) -> bool:
    return bool(text) and isinstance(text, str) and bool(_AVAILABILITY_WINDOW.search(text))


def additional_dates_note(text) -> Optional[str]:
    """Return the cell text if it says more than the dates parsed from it, else None."""
    if not text or (isinstance(text, float) and pd.isna(text)):
        return None
    raw = str(text).strip()
    leftover = _PARSED_WORDS.sub(' ', re.sub(r'[\d/\-;,&.]', ' ', raw))
    return raw if re.search(r'[A-Za-z]', leftover) else None


def end_after_cutoff(text) -> Optional[str]:
    """Parse "All blackouts end after 3/1/2027" / "... after March 1" to an ISO date."""
    if not text or not isinstance(text, str):
        return None
    m = _END_AFTER.search(text.strip())
    if not m:
        return None
    raw = m.group(1).strip()
    if '/' in raw:
        return _parse_numeric_date(raw)
    for fmt in ('%B %d', '%b %d'):
        try:
            parsed = datetime.strptime(raw, fmt)
        except ValueError:
            continue
        return f'{season_year(parsed.month):04d}-{parsed.month:02d}-{parsed.day:02d}'
    return None


def _expand_part(part: str, last_month: Optional[str]) -> List[str]:
    if '/' in part:
        return _expand_numeric_part(part)
    if not _MONTH_RE.search(part) and last_month:
        if '-' in part:
            start_raw, end_raw = [p.strip() for p in part.split('-', 1)]
            if start_raw and not _MONTH_RE.search(start_raw):
                start_raw = f'{last_month} {start_raw}'
            if end_raw and not _MONTH_RE.search(end_raw):
                end_raw = f'{last_month} {end_raw}'
            part = f'{start_raw} - {end_raw}'
        else:
            part = f'{last_month} {part}'
    if '-' in part:
        start, end = split_date_range(re.sub(r'\s*-\s*', ' - ', part))
        return get_all_dates_in_range(start, end)
    return [convert_date_string_format(part)]


def normalize_additional_dates(
    text: str, season_start: Optional[str] = None, season_end: Optional[str] = None
) -> List[str]:
    """Normalize an "Additional Blackout Dates" cell into a list of ISO dates.

    Parts are separated by commas, semicolons, "&" or "and". Each part is a single date or
    a range, in "Dec 25" or "12/25/2026" form; a missing month inherits the previous part's.
    "Saturdays <range>" / "Sundays <range>" keep only that weekday; "ALL JAN & FEB
    MONDAY-FRIDAY" covers those weekdays in those months. A part that only names weekends
    ("All weekends") expands to every weekend between season_start and season_end.
    "Opening Day" / "Closing Day" mean the assumed season bounds (season_bounds()).
    Availability windows ("Only available on Saturdays and Sundays") become every other
    date in the assumed season (availability_window_blackouts()). Parts that can't be
    parsed are skipped rather than failing the whole cell.
    """
    if not text or (isinstance(text, float) and pd.isna(text)):
        return []
    raw = str(text).strip()
    if not raw:
        return []
    if is_availability_window(raw):
        return availability_window_blackouts(raw) or []

    raw = _fix_comma_year_range_ends(raw)
    month_weekday_dates, raw = _all_months_weekday_dates(_substitute_season_bounds(raw))
    out: set = set(month_weekday_dates)
    last_month: Optional[str] = None
    for part in _PART_SPLIT.split(raw):
        part = part.split('.', 1)[0].strip()
        if not part:
            continue

        scoped = _WEEKDAY_SCOPED.match(part)
        if scoped and re.search(r'\d', scoped.group(2)):
            weekday = 5 if scoped.group(1).lower().startswith('sat') else 6
            out.update(filter_dates_for_weekday(_expand_numeric_part(scoped.group(2)), weekday))
            continue

        if _WEEKEND_WORDS.search(part) and not re.search(r'\d', part):
            if season_start and season_end:
                out.update(_season_weekend_dates(season_start, season_end))
            continue

        try:
            out.update(_expand_part(part, last_month))
        except (ValueError, IndexError):
            logger.debug('Skipping unparseable blackout date part: %r', part)
            continue

        month_match = _MONTH_RE.search(part)
        if month_match:
            last_month = month_match.group(1)
    return sorted(d for d in out if d)


def map_sheet_resort_name(raw_name, name_map: Dict[str, Optional[str]]) -> Optional[str]:
    """Normalize a sheet resort name to its resorts.csv name (None = ignore this row).

    Looks up the name as written first (older sheets used e.g. "Crystal Mountain, MI" as a
    map key), then with any ", ST" / "(Nordic)" suffix stripped.
    """
    name = str(raw_name).strip()
    if name in name_map:
        return name_map[name]
    stripped = strip_sheet_name_suffix(name)
    return name_map.get(stripped, stripped)


def match_sheet_entries(resorts_df: pd.DataFrame, sheet_map: Dict[str, Dict], label: str) -> list:
    """Match each resort row to its sheet entry (or None).

    A sheet key is either a resort name or "name|location_name", the latter for resorts
    that share a name (two "Powder Ridge" resorts: Kimball, MN and Middlefield, CT). A plain
    name shared by more than one resort is ambiguous: it's applied to neither, with a
    warning, rather than silently copied onto both.
    """
    names = resorts_df['name']
    locations = (
        resorts_df['location_name']
        if 'location_name' in resorts_df.columns
        else pd.Series([None] * len(resorts_df), index=resorts_df.index)
    )
    name_counts = names.value_counts()
    used, ambiguous, entries = set(), set(), []
    for name, location in zip(names, locations):
        loc_key = f'{name}|{location}'
        if loc_key in sheet_map:
            entries.append(sheet_map[loc_key])
            used.add(loc_key)
        elif name in sheet_map and name_counts.get(name, 0) > 1:
            ambiguous.add(name)
            entries.append(None)
        elif name in sheet_map:
            entries.append(sheet_map[name])
            used.add(name)
        else:
            entries.append(None)

    for name in sorted(ambiguous):
        logger.warning(
            '%s entry for %r is ambiguous (several resorts share that name) — not applied; '
            'map it to "name|location_name".',
            label,
            name,
        )
    missing = sorted(set(sheet_map) - used - ambiguous)
    if missing:
        logger.warning('%s resorts missing from resorts_df:', label)
        for name in missing:
            logger.warning('- %s', name)
    return entries


def parse_blackout_sheet(df_raw: pd.DataFrame) -> Dict[str, Dict]:
    """Given a blackout-sheet DataFrame, return a per-resort blackout mapping.

    The returned mapping keys are the resort names as they appear in the sheet.

    Example return value:
    {
        "Resort A": {
            "named_ranges": ["Holiday Peak", "Spring Break"],
            "additional_dates": ["2025-12-25", "2026-01-01"],
            "all_blackout_dates": ["2025-12-20", "2025-12-21", ..., "2026-03-15"]
        },
        ...
    }
    """

    df_raw = _normalize_blackout_columns(df_raw)
    named_ranges = _parse_named_ranges(df_raw)

    def _header_name(header: str) -> str:
        if "\n" in header:
            return header.split("\n", 1)[0]
        if "\\n" in header:
            return header.split("\\n", 1)[0]
        return header

    blackout_dates_df = df_raw.copy()
    blackout_dates_df.columns = [_header_name(c) for c in blackout_dates_df.columns]
    blackout_dates_df = blackout_dates_df.set_index('Resort')
    # drop legend row
    blackout_dates_df = blackout_dates_df[blackout_dates_df.index != "X = Blackout Date"]

    resort_map: Dict[str, Dict] = {}

    all_named_dates = [d for info in named_ranges.values() for d in info.get("dates", [])]
    season_start = min(all_named_dates) if all_named_dates else None
    season_end = max(all_named_dates) if all_named_dates else None

    for resort_name, row in blackout_dates_df.iterrows():
        if not resort_name or (isinstance(resort_name, float) and pd.isna(resort_name)):
            continue
        resort_name = map_sheet_resort_name(resort_name, BLACKOUT_RESORT_NAME_MAP)
        if resort_name is None:
            continue

        named_applied: List[str] = []
        all_dates = set()
        notes: List[str] = []

        additional_text = row.get("Additional Blackout Dates")
        cutoff = end_after_cutoff(additional_text)

        for name, info in named_ranges.items():
            try:
                cell = row.get(name)
            except Exception:
                cell = None
            if isinstance(cell, str):
                cell_value = cell.strip().upper()
                # "Partial (See Additional)": the Additional column lists the dates, so the
                # range isn't applied wholesale (same rule as the LTT sheet), unless
                # "All blackouts end after <date>" says it applies up to that cutoff.
                if cell_value == "X" or (cutoff and cell_value.startswith("PARTIAL")):
                    named_applied.append(name)
                    all_dates.update(info["dates"])
                elif cell_value.startswith("PARTIAL"):
                    continue
                elif cell_value and cell.strip() not in notes:
                    # e.g. "CLOSED FOR 26/27 DUE TO WILDFIRE"
                    notes.append(cell.strip())

        additional = normalize_additional_dates(
            additional_text,
            season_start=season_start,
            season_end=season_end,
        )
        all_dates.update(additional)

        all_dates -= window_open_dates(additional_text)
        if cutoff:
            all_dates = {d for d in all_dates if d <= cutoff}
        note = additional_dates_note(additional_text)
        if note:
            notes.append(note)

        resort_map[resort_name] = {
            "named_ranges": sorted(named_applied),
            "additional_dates": sorted(additional),
            "all_blackout_dates": sorted(all_dates),
            "notes": notes,
        }

    return resort_map


def merge_blackout_into_resorts(
    resorts_df: pd.DataFrame, blackout_map: Dict[str, Dict]
) -> pd.DataFrame:
    """Merge blackout info into `resorts_df` (by `name` column).

    Adds the following columns:
      - blackout_named_ranges (comma-separated string)
      - blackout_additional_dates (JSON list string)
      - blackout_all_dates (JSON list string)
      - blackout_count (int)
      - blackout_notes (JSON list string): Indy's wording for anything not turned into dates

    If a resort is not found in the blackout map, blanks are used.
    """

    def _map_for_entry(info: Optional[Dict]) -> Tuple[str, str, str, int, str]:
        if not info:
            return "", "[]", "[]", 0, "[]"
        named = ",".join(info.get("named_ranges", []))
        additional = json.dumps(info.get("additional_dates", []))
        all_dates = json.dumps(info.get("all_blackout_dates", []))
        count = len(info.get("all_blackout_dates", []))
        notes = json.dumps(info.get("notes", []), ensure_ascii=False)
        return named, additional, all_dates, count, notes

    entries = match_sheet_entries(resorts_df, blackout_map, 'Blackout')
    mapped = pd.Series([_map_for_entry(e) for e in entries], index=resorts_df.index)
    resorts_df["blackout_named_ranges"] = mapped.apply(lambda t: t[0])
    resorts_df["blackout_additional_dates"] = mapped.apply(lambda t: t[1])
    resorts_df["blackout_all_dates"] = mapped.apply(lambda t: t[2])
    resorts_df["blackout_count"] = mapped.apply(lambda t: t[3])
    resorts_df["blackout_notes"] = mapped.apply(lambda t: t[4])

    return resorts_df


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    blackout_date_df = get_blackout_dates_from_google_sheets(read_mode='cache')
    # blackout_date_df.to_csv('data/blackout_dates_raw.csv', index=False)
    blackout_date_df = blackout_date_df.rename(columns={" ": "Resort"})

    # print_blackout_name_mismatches(blackout_date_df)
    blackout_map = parse_blackout_sheet(blackout_date_df)

    logger.info('Parsed blackout info for %d resorts.', len(blackout_map))
    logger.info('%s', json.dumps(blackout_map, indent=2))


if __name__ == '__main__':
    main()

from datetime import datetime, timedelta
import os
import re
import json
import logging
from typing import Optional, Dict

from dotenv import load_dotenv
import googlemaps
import numpy as np
import pandas as pd

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
# Initialize client lazily and safely: if no API key is provided (e.g., in CI), don't
# attempt to create a googlemaps.Client at import time which raises ValueError.
gmaps = None
if API_KEY:
    try:
        gmaps = googlemaps.Client(key=API_KEY)
    except Exception as e:
        # Fail gracefully in environments without an API key; tests will monkeypatch `gmaps`.
        logger.warning("Could not initialize googlemaps client: %s", e)
        gmaps = None


def get_normalized_location(location_name: str) -> Dict[str, Optional[str]]:
    """
    Uses Google Maps Geocoding API to extract city, state, and country.

    Args:
        location_name (str): Name of the location to geocode.

    Returns:
        dict: A dictionary containing city, state, country, and the geocoded point as
        geo_latitude/geo_longitude (used to sanity-check Indy's own coordinates).
    """
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    geo_latitude: Optional[float] = None
    geo_longitude: Optional[float] = None

    def _result():
        return {
            "city": city,
            "state": state,
            "country": country,
            "geo_latitude": geo_latitude,
            "geo_longitude": geo_longitude,
        }

    try:
        geocode_result = gmaps.geocode(location_name)
        if not geocode_result:
            return _result()

        result = geocode_result[0]  # get the first result
        components = result['address_components']
        for component in components:
            if "locality" in component["types"]:
                city = component["long_name"]
            if "administrative_area_level_1" in component["types"]:
                state = component["long_name"]
            if "country" in component["types"]:
                country = component["long_name"]

        point = result.get('geometry', {}).get('location', {})
        geo_latitude = point.get('lat')
        geo_longitude = point.get('lng')

        return _result()

    except Exception as e:
        logger.warning("Error fetching data for %s: %s", location_name, e)
        return _result()


# Indy's point is usually the ski area itself and the geocoded point is the town (or
# region) in location_name. Beyond this distance, check which country Indy's point is in.
COUNTRY_CHECK_KM = 100


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Works on scalars or numpy/pandas arrays."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def get_country_at(latitude: float, longitude: float) -> Optional[str]:
    """Reverse-geocode a point to its country name, or None if the lookup fails."""
    try:
        results = gmaps.reverse_geocode((latitude, longitude), result_type='country')
        for result in results or []:
            for component in result.get('address_components', []):
                if 'country' in component.get('types', []):
                    return component['long_name']
    except Exception as e:
        logger.warning("Error reverse geocoding %s, %s: %s", latitude, longitude, e)
    return None


def generate_resort_locations_csv(
    resorts_json_path='data/resorts_raw.json',
    output_csv_path='data/resort_locations.csv',
    full=False,
):
    """
    Iterates through resorts JSON, fetches normalized locations, and saves to CSV.
    Needed for caching location data to avoid repeated API calls.

    Incremental by default: resorts already present in output_csv_path (matched by the
    (name, location_name) pair, so two different resorts sharing a name — e.g. two
    "Powder Ridge" resorts — stay distinguishable) are left as-is and not re-geocoded.
    Pass full=True to re-geocode every resort and overwrite the existing cache.

    Cached rows missing geo_latitude/geo_longitude (rows written before those columns
    existed) get one lookup to backfill the coordinates only — their city/state/country
    are left as-is.

    When Indy's own coordinates for a resort are more than COUNTRY_CHECK_KM from the
    geocoded point, the country Indy's point falls in is looked up and stored as
    indy_point_country, along with the coordinates it was checked for
    (indy_checked_latitude/longitude) so the check reruns if Indy's coordinates change.
    """

    # Load resorts data
    with open(resorts_json_path, 'r', encoding='utf-8') as f:
        resorts = json.load(f)

    # Collect unique (name, location_name) pairs, and Indy's coordinates for each
    locations = []
    indy_coords = {}
    for resort in resorts.values():
        name = resort.get('name')
        location_name = resort.get('location_name')
        if name and location_name:
            locations.append((name, location_name))
            coords = resort.get('coordinates') or {}
            if coords.get('latitude') is not None and coords.get('longitude') is not None:
                indy_coords[(name, location_name)] = (coords['latitude'], coords['longitude'])

    # Remove duplicates
    unique_locations = list({(n, l) for n, l in locations})

    geo_cols = [
        'geo_latitude',
        'geo_longitude',
        'indy_point_country',
        'indy_checked_latitude',
        'indy_checked_longitude',
    ]
    existing_df = pd.DataFrame(
        columns=['name', 'location_name', 'city', 'state', 'country'] + geo_cols
    )
    cached_pairs = set()
    if not full and os.path.exists(output_csv_path):
        existing_df = pd.read_csv(output_csv_path)
        if 'location_name' in existing_df.columns:
            cached_pairs = set(zip(existing_df['name'], existing_df['location_name']))
        else:
            # Legacy cache predating the location_name column — fall back to matching
            # by name alone (can't distinguish same-named resorts, but avoids a mass
            # re-geocode of an otherwise-valid cache).
            logger.warning(
                '%s predates the location_name column; matching cached rows by name only.',
                output_csv_path,
            )
            cached_pairs = {(n, None) for n in existing_df['name']}
        for col in geo_cols:
            if col not in existing_df.columns:
                existing_df[col] = np.nan

    # Backfill coordinates for cached rows of current resorts that don't have them yet
    if 'location_name' in existing_df.columns:
        current_pairs = set(unique_locations)
        backfilled = 0
        for idx, row in existing_df.iterrows():
            if (row['name'], row['location_name']) not in current_pairs:
                continue
            if pd.notna(row['geo_latitude']) and pd.notna(row['geo_longitude']):
                continue
            logger.info("Backfilling coordinates for: %s / %s", row['name'], row['location_name'])
            loc = get_normalized_location(row['location_name'])
            existing_df.loc[idx, 'geo_latitude'] = loc.get('geo_latitude')
            existing_df.loc[idx, 'geo_longitude'] = loc.get('geo_longitude')
            backfilled += 1
        if backfilled:
            logger.info("Backfilled coordinates for %d cached rows.", backfilled)

    # Fetch normalized locations for anything not already cached
    new_rows = []
    for name, location_name in unique_locations:
        pair = (name, location_name) if 'location_name' in existing_df.columns else (name, None)
        if pair in cached_pairs:
            continue
        logger.info("Retrieving location for: %s / %s", name, location_name)
        loc = get_normalized_location(location_name)
        new_rows.append(
            {
                'name': name,
                'location_name': location_name,
                'city': loc.get('city'),
                'state': loc.get('state'),
                'country': loc.get('country'),
                'geo_latitude': loc.get('geo_latitude'),
                'geo_longitude': loc.get('geo_longitude'),
            }
        )
        # Mark as cached immediately so a duplicate (name, location_name) pair later in
        # this same batch isn't geocoded twice.
        cached_pairs.add(pair)

    new_df = pd.DataFrame(new_rows, columns=existing_df.columns)
    if existing_df.empty:
        df = new_df
    elif new_rows:
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = existing_df

    # Country-check Indy's point where it's far from the geocoded one
    if 'location_name' in df.columns:
        df = df.astype({'indy_point_country': 'object'})
        checked = 0
        for idx, row in df.iterrows():
            point = indy_coords.get((row['name'], row['location_name']))
            if point is None or pd.isna(row['geo_latitude']) or pd.isna(row['geo_longitude']):
                continue
            if haversine_km(point[0], point[1], row['geo_latitude'], row['geo_longitude']) <= (
                COUNTRY_CHECK_KM
            ):
                continue
            if np.isclose(row['indy_checked_latitude'], point[0]) and np.isclose(
                row['indy_checked_longitude'], point[1]
            ):
                continue
            df.loc[idx, 'indy_point_country'] = get_country_at(*point)
            df.loc[idx, 'indy_checked_latitude'] = point[0]
            df.loc[idx, 'indy_checked_longitude'] = point[1]
            checked += 1
        if checked:
            logger.info("Country-checked Indy coordinates for %d resorts.", checked)

    # Save to CSV
    df.to_csv(output_csv_path, index=False)
    logger.info("Wrote %s (%d new, %d total)", output_csv_path, len(new_rows), len(df))


# Date Utilities

# Start year of the ski season the blackout sheets describe (2026 = the 26/27 season).
# Dates without an explicit year are placed in it: Jul-Dec -> this year, Jan-Jun -> the
# next. Bump it when switching the blackout/LTT sheet URLs to a new season's tabs.
SEASON_START_YEAR = 2026


def season_year(month: int) -> int:
    """Year a month falls in for the current season (Jul-Dec -> start year, else +1)."""
    return SEASON_START_YEAR if month >= 7 else SEASON_START_YEAR + 1


# Trailing state/province on sheet resort names: "Pats Peak, NH", "Big Rock, Maine",
# "Hochzeiger Bergbahnen Pitztal AG, " (empty), and a "(Nordic)" tag.
_STATE_AND_PROVINCE_NAMES = (
    'Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|'
    'Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|'
    'Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|'
    'New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|'
    'Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|'
    'Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Alberta|British Columbia|'
    'Manitoba|New Brunswick|Newfoundland|Nova Scotia|Ontario|Quebec|Saskatchewan'
)
_NAME_SUFFIX = re.compile(rf',\s*(?:[A-Z]{{2}}|{_STATE_AND_PROVINCE_NAMES})?\s*$')
_NORDIC_TAG = re.compile(r'\s*\(nordic\)\s*$', re.IGNORECASE)


def strip_sheet_name_suffix(name: str) -> str:
    """Strip a trailing ", ST" / ", State" / "(Nordic)" from a resort name in Indy's sheets.

    Country suffixes are left alone ("Levi, Finland" is a real roster name).
    """
    name = _NORDIC_TAG.sub('', str(name).strip())
    return _NAME_SUFFIX.sub('', name).strip()


def split_date_range(date_range: str) -> tuple[str, str]:
    """
    Splits a date range string formatted as "Jan 1 - Mar 31" into start and end dates.
    Must handle some implicit rules:
    - Dates fall in the season starting SEASON_START_YEAR (see season_year())
    - If the two dates are in the same month, then the second date does not include the month

    """
    start_str, end_str = date_range.split(' - ')
    start_parts = start_str.strip().split(' ')
    end_parts = end_str.strip().split(' ')

    # start date
    start_month_str = start_parts[0]
    start_day_str = start_parts[1]
    start_month = datetime.strptime(start_month_str, '%b').month
    start_day = int(start_day_str)
    start_year = season_year(start_month)

    # end date
    if len(end_parts) == 2:
        end_month_str = end_parts[0]
        end_day_str = end_parts[1]
        end_month = datetime.strptime(end_month_str, '%b').month
    else:
        end_month = start_month
        end_day_str = end_parts[0]
    end_day = int(end_day_str)
    end_year = season_year(end_month)

    start_date = f'{start_year}-{start_month:02d}-{start_day:02d}'
    end_date = f'{end_year}-{end_month:02d}-{end_day:02d}'

    return start_date, end_date


def convert_date_string_format(date_string: str):
    """
    Converts a date formatted as Jan 1 to YYYY-MM-DD

    The year comes from the month, within the season starting SEASON_START_YEAR.
    """
    month_day = date_string.strip().split(' ')
    month_str = month_day[0]
    day_str = month_day[1]
    month = datetime.strptime(month_str, '%b').month
    day = int(day_str)
    year = season_year(month)
    return f'{year}-{month:02d}-{day:02d}'


def get_all_dates_in_range(start_date: str, end_date: str) -> list[str]:
    """
    Given a start date and end date in YYYY-MM-DD format, returns a list of all dates in that range (inclusive).
    """
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    delta = end_dt - start_dt

    return [(start_dt + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]


def filter_dates_for_weekday(dates: list[str], weekday: int) -> list[str]:
    """
    Given a list of dates in YYYY-MM-DD format, returns a list of dates that fall on the given weekday.
    Weekday is an integer where Monday is 0 and Sunday is 6.
    """
    filtered_dates = []
    for date_str in dates:
        date_dt = datetime.strptime(date_str, '%Y-%m-%d')
        if date_dt.weekday() == weekday:
            filtered_dates.append(date_str)
    return filtered_dates

from datetime import datetime, timedelta
import os
import json
from typing import Optional, Dict

from dotenv import load_dotenv
import googlemaps
import pandas as pd

load_dotenv()



# Location Utilities
API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=API_KEY)


def get_normalized_location(location_name: str) -> Dict[str, Optional[str]]:
    """
    Uses Google Maps Geocoding API to extract city, state, and country.
    
    Args:
        location_name (str): Name of the location to geocode.

    Returns:
        dict: A dictionary containing city, state, and country.
    """
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    try:
        geocode_result = gmaps.geocode(location_name)
        if not geocode_result:
            return {"city": city, "state": state, "country": country}

        result = geocode_result[0] # get the first result
        components = result['address_components']
        for component in components:
            if "locality" in component["types"]:
                city = component["long_name"]
            if "administrative_area_level_1" in component["types"]:
                state = component["long_name"]
            if "country" in component["types"]:
                country = component["long_name"]

        return {"city": city, "state": state, "country": country}

    except Exception as e:
        print(f"Error fetching data for {location_name}: {e}")
        return {"city": city, "state": state, "country": country}


def generate_resort_locations_csv(
    resorts_json_path='data/resorts_raw.json',
    output_csv_path='data/resort_locations.csv'
):
    """
    Iterates through resorts JSON, fetches normalized locations, and saves to CSV.
    Needed for caching location data to avoid repeated API calls.
    """

    # Load resorts data
    with open(resorts_json_path, 'r', encoding='utf-8') as f:
        resorts = json.load(f)

    # Collect unique (name, location_name) pairs
    locations = []
    for resort in resorts.values():
        name = resort.get('name')
        location_name = resort.get('location_name')
        if name and location_name:
            locations.append((name, location_name))

    # Remove duplicates
    unique_locations = list({(n, l) for n, l in locations})

    # Fetch normalized locations
    rows = []
    for name, location_name in unique_locations:
        print(f"Retrieving location for: {name} / {location_name}")
        loc = get_normalized_location(location_name)
        rows.append({
            'name': name,
            'city': loc.get('city'),
            'state': loc.get('state'),
            'country': loc.get('country')
        })

    # Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_csv_path, index=False)
    print(f"Wrote {output_csv_path}")


# Date Utilities

def split_date_range(date_range: str) -> tuple[str, str]:
    """
    Splits a date range string formatted as "Jan 1 - Mar 31" into start and end dates.
    Must handle some implicit rules:
    - If the date is between July and Dec, then it's in the current year (2025)
    - If the date is between Jan and May, then it's in the next year (2026)
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
    start_year = 2025 if start_month in [7, 8, 9, 10, 11, 12] else 2026

    # end date
    if len(end_parts) == 2:
        end_month_str = end_parts[0]
        end_day_str = end_parts[1]
        end_month = datetime.strptime(end_month_str, '%b').month
    else:
        end_month = start_month
        end_day_str = end_parts[0]
    end_day = int(end_day_str)
    end_year = 2025 if end_month in [7, 8, 9, 10, 11, 12] else 2026

    start_date = f'{start_year}-{start_month:02d}-{start_day:02d}'
    end_date = f'{end_year}-{end_month:02d}-{end_day:02d}'

    return start_date, end_date


def convert_date_string_format(date_string: str):
    """
    Converts a date formatted as Jan 1 to YYYY-MM-DD

    Need to determine the year based on the given month
    If month is between Jan and May, then year is next year
    """
    month_day = date_string.strip().split(' ')
    month_str = month_day[0]
    day_str = month_day[1]
    month = datetime.strptime(month_str, '%b').month
    day = int(day_str)
    year = 2026 if month in [1, 2, 3, 4, 5] else 2025
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
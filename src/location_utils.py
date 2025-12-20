import os
import json
from typing import Optional, Dict

from dotenv import load_dotenv
import googlemaps
import pandas as pd

load_dotenv()
API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
# Initialize client lazily and safely: if no API key is provided (e.g., in CI), don't
# attempt to create a googlemaps.Client at import time which raises ValueError.
gmaps = None
if API_KEY:
    try:
        gmaps = googlemaps.Client(key=API_KEY)
    except Exception as e:
        # Fail gracefully in environments without an API key; tests will monkeypatch `gmaps`.
        print(f"Could not initialize googlemaps client: {e}")
        gmaps = None


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

        result = geocode_result[0]  # get the first result
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
    output_csv_path='data/resort_locations.csv',
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
        rows.append(
            {
                'name': name,
                'city': loc.get('city'),
                'state': loc.get('state'),
                'country': loc.get('country'),
            }
        )

    # Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_csv_path, index=False)
    print(f"Wrote {output_csv_path}")

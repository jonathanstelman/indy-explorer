import os
from typing import Optional, Dict

from dotenv import load_dotenv
import googlemaps

load_dotenv()
API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")


# Initialize Google Maps Client
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

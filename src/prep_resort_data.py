"""
Prepare raw resorts data to produce a prepared file for use with Streamlit
"""

import json
import pandas as pd
from typing import Tuple

from location_utils import get_normalized_location


def get_regions_from_location_name(location_name: str) -> Tuple[str, str, str]:
    """
    Gets the city, state, and country from Indy's "city" field using Google Map's Geocoding API
    """
    location_json = get_normalized_location(location_name)
    return location_json['city'], location_json['state'], location_json['country']


with open('data/resorts_raw.json', 'r', encoding='utf-8') as json_file:
    resorts_dict = json.load(json_file)
resorts = pd.DataFrame(resorts_dict).transpose()

# Webpage URL
resorts['web_page'] = resorts['href'].apply(
    lambda x: 'https://www.indyskipass.com' + x if x else 'n/a'
)

# Display text
bool_map = {False: 'No', True: 'Yes'}
resorts['is_alpine_xc_display'] = resorts.is_alpine_xc.map(bool_map)
resorts['is_open_nights_display'] = resorts.is_open_nights.map(bool_map)
resorts['has_terrain_parks_display'] = resorts.has_terrain_parks.map(bool_map)
resorts['is_allied_display'] = resorts.is_allied.map(bool_map)

# Location
resorts['longitude'] = resorts['coordinates'].apply(lambda l: l.get('longitude') if l else None)
resorts['latitude'] = resorts['coordinates'].apply(lambda l: l.get('latitude') if l else None)
resorts['city'], resorts['state'], resorts['country'] = zip(*resorts.location_name.apply(get_regions_from_location_name))


# Clean up
cols = [
    'name',
    'location_name',
    'city',
    'state',
    'country',
    'longitude',
    'latitude',
    'vertical',
    'is_nordic',
    'is_alpine_xc',
    'is_xc_only',
    'is_allied',
    'num_trails',
    'num_lifts',
    'is_open_nights',
    'has_terrain_parks',
    'web_page',
    'is_alpine_xc_display',
    'is_open_nights_display',
    'has_terrain_parks_display',
    'is_allied_display',
]
resorts = resorts[cols]
resorts.to_csv('data/resorts.csv')


pd.options.display.max_columns = None
pd.options.display.max_rows = None

print(resorts)

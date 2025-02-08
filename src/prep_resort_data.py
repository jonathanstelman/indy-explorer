"""
Prepare raw resorts data to produce a prepared file for use with Streamlit
"""

import json
from typing import Tuple
import pandas as pd
import numpy as np

from location_utils import get_normalized_location


def get_regions_from_location_name(location_name: str) -> Tuple[str, str, str]:
    """
    Gets the city, state, and country from Indy's "city" field using Google Map's Geocoding API
    """
    location_json = get_normalized_location(location_name)
    return location_json['city'], location_json['state'], location_json['country']

# Get resort data from main page
with open('data/resorts_raw.json', 'r', encoding='utf-8') as json_file:
    resorts_dict = json.load(json_file)


# Add data from resort-specific pages
for _id, resort_data in resorts_dict.items():
    resort_slug = resort_data['href'].split('/')[-1]
    with open(f'data/{resort_slug}.json', 'r', encoding='utf-8') as json_file:
        resort_page = json.load(json_file)
        resorts_dict[_id].update(resort_page)

# Add cached location data
locations = pd.read_csv('data/resort_locations.csv')

# Create DataFrame
resorts = pd.DataFrame(resorts_dict).transpose()

# Webpage URL
resorts['indy_page'] = resorts['href'].apply(
    lambda x: 'https://www.indyskipass.com' + x if x else 'n/a'
)

# Separate the resort type labels
def is_alpine(resort):
    """Determine if the resort is an alpine resort
    """
    if (not resort.is_nordic) and (not resort.is_alpine_xc) and (not resort.is_xc_only):
        return True
    if resort.is_alpine_xc:
        return True
    return False

resorts['has_alpine'] = resorts.apply(is_alpine, axis=1)
resorts['has_cross_country'] = resorts['is_nordic']


# Fix discrepancies between main page and resort page
# Issues related to bad parsing of cross-country resorts - defer to main page
resorts.drop(columns=['lifts'], inplace=True)
resorts.drop(columns=['trails'], inplace=True)
resorts.rename(columns={'is_open_nights': 'has_night_skiing'}, inplace=True)
resorts.drop(columns=['terrain_parks'], inplace=True)

# Location
resorts['longitude'] = resorts['coordinates'].apply(lambda l: l.get('longitude') if l else None)
resorts['latitude'] = resorts['coordinates'].apply(lambda l: l.get('latitude') if l else None)
# resorts['city'], resorts['state'], resorts['country'] = zip(*resorts.location_name.apply(get_regions_from_location_name))
resorts = pd.merge(resorts, locations, left_on='name', right_on='name', how='left')


# Formatting and units
def feet_to_meters(feet):
    """
    Convert feet to meters, safely handling missing values
    """
    return int(feet * 0.30479999) if pd.notnull(feet) else np.nan
resorts["vertical_meters"] = resorts.vertical.apply(feet_to_meters)


# Fields for table display
bool_map = {False: 'No', True: 'Yes'}
table_cols = [
    'has_alpine', 'has_cross_country', 'has_night_skiing', 'has_terrain_parks',
    'is_allied', 'is_dog_friendly', 'has_snowshoeing'
]
for col in table_cols:
    resorts[col + '_display'] = resorts[col].map(bool_map)


# Fields for tooltip display
def nan_to_text(value):
    """Convert NaN to '--' for tooltip display
    """
    return '---' if pd.isnull(value) else value

resorts['num_trails_tt'] = resorts['num_trails'].apply(nan_to_text)
resorts['num_lifts_tt'] = resorts['num_lifts'].apply(nan_to_text)
resorts['acres_tt'] = resorts['acres'].apply(lambda x: f"{x} acres" if pd.notnull(x) else '---')
resorts['vertical_tt'] = resorts.apply(
    lambda r: f"{r.vertical} ft / {int(r.vertical_meters)} m" if pd.notnull(r.vertical) else '---',
    axis=1
)


# Clean up
cols = [
    'name',
    'location_name',
    'description',
    'city',
    'state',
    'country',
    'indy_page',
    'website',
    'latitude',
    'longitude',
    'vertical',
    'vertical_meters',
    'has_alpine',
    'has_cross_country',
    'is_allied',
    'acres',
    'num_trails',
    'trail_length_mi',
    'trail_length_km',
    'num_lifts',
    'vertical_base_ft',
    'vertical_summit_ft',
    'vertical_elevation_ft',
    'has_night_skiing',
    'has_terrain_parks',
    'is_dog_friendly',
    'has_snowshoeing',
    'difficulty_beginner',
    'difficulty_intermediate',
    'difficulty_advanced',
    'snowfall_average_in',
    'snowfall_high_in',
    'has_alpine_display',
    'has_cross_country_display',
    'is_dog_friendly_display',
    'has_night_skiing_display',
    'has_terrain_parks_display',
    'is_allied_display',
    'acres_tt',
    'vertical_tt',
    'num_trails_tt',
    'num_lifts_tt',
]

resorts = resorts[cols]
resorts.to_csv('data/resorts.csv')

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


# Add data from resort page
for _id, resort_data in resorts_dict.items():
    resort_slug = resort_data['href'].split('/')[-1]
    with open(f'data/{resort_slug}.json', 'r', encoding='utf-8') as json_file:
        resort_page = json.load(json_file)
        resorts_dict[_id].update(resort_page)

# Create DataFrame
resorts = pd.DataFrame(resorts_dict).transpose()

# Webpage URL
resorts['indy_page'] = resorts['href'].apply(
    lambda x: 'https://www.indyskipass.com' + x if x else 'n/a'
)

# Fix discrepancies between main page and resort page
# Issues related to bad parsing of cross-country resorts - defer to main page
resorts.drop(columns=['lifts'], inplace=True)
resorts.drop(columns=['trails'], inplace=True)
resorts.rename(columns={'is_open_nights': 'has_night_skiing'}, inplace=True)
resorts.drop(columns=['terrain_parks'], inplace=True)

# Display text
bool_map = {False: 'No', True: 'Yes'}
resorts['is_alpine_xc_display'] = resorts.is_alpine_xc.map(bool_map)
resorts['night_skiing_display'] = resorts.has_night_skiing.map(bool_map)
resorts['has_terrain_parks_display'] = resorts.has_terrain_parks.map(bool_map)
resorts['is_allied_display'] = resorts.is_allied.map(bool_map)
resorts['is_cross_country_display'] = resorts['is_cross_country'].map(bool_map)
resorts['is_dog_friendly_display'] = resorts['is_dog_friendly'].map(bool_map)
resorts['has_snowshoeing_display'] = resorts['has_snowshoeing'].map(bool_map)

# Location
resorts['longitude'] = resorts['coordinates'].apply(lambda l: l.get('longitude') if l else None)
resorts['latitude'] = resorts['coordinates'].apply(lambda l: l.get('latitude') if l else None)
resorts['city'], resorts['state'], resorts['country'] = zip(*resorts.location_name.apply(get_regions_from_location_name))



# Clean up
cols = [
    # 'id',
    # 'slug',
    'name',
    'location_name',
    # 'description',
    # 'coordinates',
    'city',
    'state',
    'country',
    # 'href',
    'indy_page',
    'website',
    'latitude',
    'longitude',
    'vertical',
    'is_nordic',
    'is_alpine_xc',
    'is_xc_only', # from main page
    'is_cross_country', # from resort page
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
    'is_dog_friendly_display',
    'is_alpine_xc_display',
    'night_skiing_display',
    'has_terrain_parks_display',
    'is_allied_display',
]

resorts = resorts[cols]
resorts.to_csv('data/resorts.csv')

# pd.options.display.max_columns = None
# pd.options.display.max_rows = None
# print(resorts)

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

# Location
resorts['longitude'] = resorts['coordinates'].apply(lambda l: l.get('longitude') if l else None)
resorts['latitude'] = resorts['coordinates'].apply(lambda l: l.get('latitude') if l else None)
# resorts['city'], resorts['state'], resorts['country'] = zip(*resorts.location_name.apply(get_regions_from_location_name))



# Clean up
cols = [
    # 'id',
    # 'slug',
    'name',
    'location_name',
    # 'description',
    # 'coordinates',
    # 'city',
    # 'state',
    # 'country',
    # 'href',
    'indy_page',
    'url',
    'latitude',
    'longitude',
    'vertical',
    'is_nordic',
    'is_alpine_xc',
    'is_xc_only',
    'is_allied',
    'num_trails',
    # 'trails', # from resort page
    'num_lifts',
    # 'lifts', # from resort page
    'vertical_base',
    'vertical_summit',
    'vertical_elevation',
    # 'is_open_nights',
    'night_skiing', # from main page
    'has_terrain_parks',
    # 'terrain_parks', # from resort page
    'acres', # from resort page
    'difficulty_beginner',
    'difficulty_intermediate',
    'difficulty_advanced',
    'snowfall_average',
    'snowfall_high',
    'is_alpine_xc_display',
    'night_skiing_display',
    'has_terrain_parks_display',
    'is_allied_display',
]

resorts = resorts[cols]

# find places where resorts page differs from main page
# qa_cols = ['name', 'has_terrain_parks', 'terrain_parks', 'indy_page']
# mismatched = resorts[resorts['has_terrain_parks'] != resorts['terrain_parks']][qa_cols]
# mismatched.to_csv('resorts_qa.csv')

resorts.to_csv('data/resorts_v2.csv')

# pd.options.display.max_columns = None
# pd.options.display.max_rows = None


# # print(resorts)

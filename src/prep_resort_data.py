"""
Prepare raw resorts data to produce a prepared file for use with Streamlit
"""

import argparse
import json
import logging
from typing import Tuple
import pandas as pd
import numpy as np
import os

from blackout import (
    get_blackout_dates_from_google_sheets,
    parse_blackout_sheet,
    merge_blackout_into_resorts,
)
from reservations import build_reservation_map, merge_reservations_into_resorts
from peak_rankings import (
    fetch_peak_rankings_csv,
    build_peak_rankings_map,
    merge_peak_rankings_into_resorts,
    PR_COLUMNS,
)
from utils import get_normalized_location, generate_resort_locations_csv


logger = logging.getLogger(__name__)


def get_regions_from_location_name(location_name: str) -> Tuple[str, str, str]:
    """
    Gets the city, state, and country from Indy's "city" field using Google Map's Geocoding API
    """
    location_json = get_normalized_location(location_name)
    return location_json['city'], location_json['state'], location_json['country']


def is_alpine(resort):
    """Determine if the resort is an alpine resort"""
    if (not resort.is_nordic) and (not resort.is_alpine_xc) and (not resort.is_xc_only):
        return True
    if resort.is_alpine_xc:
        return True
    return False


def feet_to_meters(feet):
    """
    Convert feet to meters, safely handling missing values
    """
    return int(feet * 0.30479999) if pd.notnull(feet) else np.nan


def nan_to_text(value, replace_text='---'):
    """
    Convert NaN to '---' for tooltip display
    """
    if pd.isnull(value) or value == '':
        return replace_text
    else:
        return value


def main(refresh_blackout=False):
    logger.info('Loading raw resort data...')
    # Get resort data from main page
    with open('data/resorts_raw.json', 'r', encoding='utf-8') as json_file:
        resorts_dict = json.load(json_file)
    logger.debug('Loaded %d resorts from data/resorts_raw.json.', len(resorts_dict))

    logger.info('Merging resort page extracts...')
    # Add data from resort-specific pages
    for _id, resort_data in resorts_dict.items():
        resort_slug = resort_data['href'].split('/')[-1]
        with open(
            f'data/resort_page_extracts/{resort_slug}.json', 'r', encoding='utf-8'
        ) as json_file:
            resort_page = json.load(json_file)
            resorts_dict[_id].update(resort_page)
    logger.debug('Merged %d resort page extracts.', len(resorts_dict))

    # Get location data, generating if needed
    if not os.path.exists('data/resort_locations.csv'):
        logger.info('data/resort_locations.csv not found. Generating...')
        generate_resort_locations_csv()

    # Add cached location data
    logger.info('Loading cached location data...')
    locations = pd.read_csv('data/resort_locations.csv')
    logger.debug('Loaded %d location rows.', len(locations))

    # Create DataFrame
    logger.info('Building resorts DataFrame...')
    resorts = pd.DataFrame(resorts_dict).transpose()
    logger.debug('Resorts DataFrame rows: %d.', len(resorts))

    # Webpage URL
    resorts['indy_page'] = resorts['href'].apply(
        lambda x: 'https://www.indyskipass.com' + x if x else 'n/a'
    )

    # Separate the resort type labels
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
    missing_locations = resorts['city'].isna().sum()
    if missing_locations:
        logger.warning('Missing location data for %d resorts after merge.', missing_locations)

    # Formatting and units
    resorts["vertical_meters"] = resorts.vertical.apply(feet_to_meters)

    # Fields for table display
    bool_map = {False: 'No', True: 'Yes'}
    table_cols = [
        'has_alpine',
        'has_cross_country',
        'has_night_skiing',
        'has_terrain_parks',
        'is_allied',
        'is_dog_friendly',
        'has_snowshoeing',
    ]
    for col in table_cols:
        resorts[col + '_display'] = resorts[col].map(bool_map)

    # Fields for tooltip display
    resorts['location_name_tt'] = resorts['location_name'].apply(nan_to_text, replace_text='n/a')
    resorts['num_trails_tt'] = resorts['num_trails'].apply(nan_to_text)
    resorts['num_lifts_tt'] = resorts['num_lifts'].apply(nan_to_text)
    resorts['acres_tt'] = resorts['acres'].apply(lambda x: f"{x} acres" if pd.notnull(x) else '---')
    resorts['vertical_tt'] = resorts.apply(
        lambda r: (
            f"{r.vertical} ft / {int(r.vertical_meters)} m" if pd.notnull(r.vertical) else '---'
        ),
        axis=1,
    )

    # Clean up
    cols = [
        'name',
        'location_name',
        'description',
        'region',
        'city',
        'state',
        'country',
        'indy_page',
        'website',
        'reservation_status',
        'reservation_url',
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
        'location_name_tt',
        'acres_tt',
        'vertical_tt',
        'num_trails_tt',
        'num_lifts_tt',
        'blackout_named_ranges',
        'blackout_additional_dates',
        'blackout_all_dates',
        'blackout_count',
        'pr_snow',
        'pr_resiliency',
        'pr_size',
        'pr_terrain_diversity',
        'pr_challenge',
        'pr_lifts',
        'pr_crowd_flow',
        'pr_facilities',
        'pr_navigation',
        'pr_mountain_aesthetic',
        'pr_total',
        'pr_overall_rank',
        'pr_regional_rank',
        'pr_region',
        'pr_lodging',
        'pr_apres_ski',
        'pr_access_road',
        'pr_ability_low',
        'pr_ability_high',
        'pr_nearest_cities',
        'pr_pass_affiliation',
        'pr_total_tt',
    ]

    # Merge blackout data (fail fast if anything goes wrong)
    logger.info('Processing blackout dates...')
    blackout_path = 'data/blackout_dates_raw.csv'
    if refresh_blackout or not os.path.exists(blackout_path):
        if refresh_blackout:
            logger.info('Refreshing blackout dates from Google Sheets...')
        else:
            logger.info('%s not found. Fetching latest blackout dates...', blackout_path)
        blackout_df = get_blackout_dates_from_google_sheets(
            read_mode='live', cache_path=blackout_path
        )
        blackout_df.to_csv(blackout_path, index=False)
    else:
        logger.info('Loading blackout dates from %s...', blackout_path)
        blackout_df = pd.read_csv(blackout_path)
    logger.debug('Loaded %d blackout rows.', len(blackout_df))
    blackout_map = parse_blackout_sheet(blackout_df)
    if not blackout_map:
        logger.warning('Blackout map is empty. Check blackout sheet parsing.')
    else:
        logger.debug('Parsed blackout data for %d resorts.', len(blackout_map))
    resorts = merge_blackout_into_resorts(resorts, blackout_map)

    logger.info('Processing reservations...')
    reservations_path = 'data/reservations_raw.json'
    if os.path.exists(reservations_path):
        with open(reservations_path, 'r', encoding='utf-8') as json_file:
            reservations_raw = json.load(json_file)
        reservation_map = build_reservation_map(reservations_raw)
        resorts = merge_reservations_into_resorts(resorts, reservation_map)
    else:
        logger.warning('Reservations data missing at %s. Using defaults.', reservations_path)
        resorts['reservation_status'] = 'Not Required'
        resorts['reservation_url'] = ''

    logger.info('Processing Peak Rankings...')
    peak_rankings_path = 'data/peak_rankings_raw.csv'
    if os.path.exists(peak_rankings_path):
        peak_rankings_df = pd.read_csv(peak_rankings_path)
        peak_rankings_map = build_peak_rankings_map(peak_rankings_df)
        resorts = merge_peak_rankings_into_resorts(resorts, peak_rankings_map)
    else:
        logger.warning('Peak Rankings data missing at %s. Using defaults.', peak_rankings_path)
        for col in PR_COLUMNS:
            resorts[col] = np.nan

    # Peak Rankings tooltip field
    resorts['pr_total_tt'] = resorts.apply(
        lambda r: (
            f"Score: {int(r.pr_total)} (Rank #{int(r.pr_overall_rank)})"
            if pd.notnull(r.get('pr_total')) and pd.notnull(r.get('pr_overall_rank'))
            else '---'
        ),
        axis=1,
    )

    resorts = resorts[cols]
    resorts.to_csv('data/resorts.csv', index_label='index')
    logger.info('Prepared resort data written to data/resorts.csv')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare resort data for the app.')
    parser.add_argument(
        '--refresh-blackout',
        action='store_true',
        help='Force re-download of blackout dates even if the CSV exists.',
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        help='Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).',
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError(f'Invalid log level: {args.log_level}')
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    main(refresh_blackout=args.refresh_blackout)

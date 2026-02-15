"""Peak Rankings data integration.

Fetches resort scores and rankings from peakrankings.com (published as a Google
Sheet), normalizes resort names to match the Indy Pass dataset, and merges the
rankings into the resorts DataFrame.

Public API:
- fetch_peak_rankings_csv(read_mode, cache_path) -> pd.DataFrame
- build_peak_rankings_map(df) -> Dict[str, Dict]
- merge_peak_rankings_into_resorts(resorts_df, rankings_map) -> pd.DataFrame
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import Dict

import pandas as pd

PEAK_RANKINGS_GSHEET_URL = (
    'https://docs.google.com/spreadsheets/d/'
    '1YDRKdIro4IJTAK8iyTReSSAMFdyEAGsQxxCSGgxCw5I/gviz/tq?tqx=out:csv'
)

DEFAULT_CACHE_PATH = 'data/peak_rankings_raw.csv'

# Map Peak Rankings resort names -> Indy Pass resort names (for mismatches).
# Populated after running once and checking logs for unmatched names.
PEAK_RANKINGS_NAME_MAP: Dict[str, str] = {
    'Bear Valley': 'Bear Valley Mountain Resort',
    'Big White': 'Big White Ski Resort',
    'Bolton Valley': 'Bolton Valley Resort',
    'Cannon': 'Cannon Mountain',
    'Castle Mountain': 'Castle Mountain Resort',
    'Jay Peak': 'Jay Peak Resort',
    'Loveland': 'Loveland Ski Area',
    'Mount Shasta Ski Park': 'Mt. Shasta',
    "Peek'n Peak": 'Peek \u2018n Peak',
    'Saddleback': 'Saddleback Mountain',
    'Snow King': 'Snow King Mountain Resort',
    'Waterville Valley': 'Waterville Valley Resort',
}

# Columns to extract from the raw sheet and their pr_ prefixed names.
FIELD_MAP = {
    'snow': 'pr_snow',
    'resiliency': 'pr_resiliency',
    'size': 'pr_size',
    'terrainDiversity': 'pr_terrain_diversity',
    'challenge': 'pr_challenge',
    'lifts': 'pr_lifts',
    'crowdFlow': 'pr_crowd_flow',
    'facilities': 'pr_facilities',
    'navigation': 'pr_navigation',
    'mountainAesthetic': 'pr_mountain_aesthetic',
    'Total': 'pr_total',
    'overallRank': 'pr_overall_rank',
    'regionalRank': 'pr_regional_rank',
    'regionForRank': 'pr_region',
    'lodging': 'pr_lodging',
    'apresSki': 'pr_apres_ski',
    'accessRoadTrafficFlow': 'pr_access_road',
    'abilityRangeLow': 'pr_ability_low',
    'abilityRangeHigh': 'pr_ability_high',
    'nearestCities': 'pr_nearest_cities',
    'passAffiliation': 'pr_pass_affiliation',
}

# All pr_ column names (for setting defaults when data is missing).
PR_COLUMNS = list(FIELD_MAP.values())

logger = logging.getLogger(__name__)


def fetch_peak_rankings_csv(
    read_mode: str = 'live',
    cache_path: str = DEFAULT_CACHE_PATH,
) -> pd.DataFrame:
    """Fetch Peak Rankings CSV from Google Sheets or load from cache."""
    if read_mode == 'cache' and os.path.exists(cache_path):
        logger.info('Loading Peak Rankings from cached CSV: %s', cache_path)
        return pd.read_csv(cache_path)

    logger.info('Fetching Peak Rankings from Google Sheets...')
    df = pd.read_csv(PEAK_RANKINGS_GSHEET_URL)
    os.makedirs(os.path.dirname(cache_path) or '.', exist_ok=True)
    df.to_csv(cache_path, index=False)
    logger.info('Cached Peak Rankings CSV to %s (%d rows).', cache_path, len(df))
    return df


def build_peak_rankings_map(df: pd.DataFrame) -> Dict[str, Dict]:
    """Build a resort-name-keyed map of Peak Rankings data.

    Normalizes resort names via PEAK_RANKINGS_NAME_MAP and renames columns
    to use the pr_ prefix.
    """
    # The sheet uses 'name' as the resort name column
    name_col = 'name' if 'name' in df.columns else 'resort'
    if name_col not in df.columns:
        logger.warning(
            'Peak Rankings CSV missing resort name column. Available: %s', list(df.columns)
        )
        return {}

    rankings_map: Dict[str, Dict] = {}
    for _, row in df.iterrows():
        raw_name = str(row.get(name_col, '')).strip()
        if not raw_name:
            continue
        name = PEAK_RANKINGS_NAME_MAP.get(raw_name, raw_name)
        entry = {}
        for src_col, pr_col in FIELD_MAP.items():
            val = row.get(src_col)
            if pd.isna(val):
                entry[pr_col] = None
            else:
                entry[pr_col] = val
        rankings_map[name] = entry

    logger.info('Built Peak Rankings map for %d resorts.', len(rankings_map))
    return rankings_map


def merge_peak_rankings_into_resorts(
    resorts_df: pd.DataFrame,
    rankings_map: Dict[str, Dict],
) -> pd.DataFrame:
    """Left-join Peak Rankings data into resorts_df by name column."""

    def _map_for_name(name: str) -> Dict:
        return rankings_map.get(name, {})

    mapped = resorts_df['name'].apply(_map_for_name)
    for col in PR_COLUMNS:
        resorts_df[col] = mapped.apply(lambda d, c=col: d.get(c))

    matched = sum(1 for name in resorts_df['name'] if name in rankings_map)
    logger.info(
        'Merged Peak Rankings: %d/%d Indy resorts matched.',
        matched,
        len(resorts_df),
    )

    missing_in_resorts = sorted(set(rankings_map.keys()) - set(resorts_df['name']))
    if missing_in_resorts:
        logger.warning('Peak Rankings resorts not in Indy data:')
        for name in missing_in_resorts:
            logger.warning('- %s', name)

    missing_in_rankings = sorted(set(resorts_df['name']) - set(rankings_map.keys()))
    if missing_in_rankings:
        logger.debug('Indy resorts without Peak Rankings data:')
        for name in missing_in_rankings:
            logger.debug('- %s', name)

    return resorts_df


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    parser = argparse.ArgumentParser(description='Fetch and cache Peak Rankings data.')
    parser.add_argument(
        '--read-mode',
        choices=['cache', 'live'],
        default='cache',
        help='Use cached CSV or fetch live from Google Sheets (default: cache).',
    )
    parser.add_argument(
        '--cache-path',
        default=DEFAULT_CACHE_PATH,
        help='Path to cached Peak Rankings CSV.',
    )
    args = parser.parse_args()

    df = fetch_peak_rankings_csv(read_mode=args.read_mode, cache_path=args.cache_path)
    rankings_map = build_peak_rankings_map(df)
    logger.info('Peak Rankings map contains %d resorts.', len(rankings_map))


if __name__ == '__main__':
    main()

"""
One-time migration: generate stable UUIDs for all existing resorts.

Creates data/resort_id_map.csv and adds resort_id as the first column of
data/resorts.csv. Safe to re-run — existing UUIDs are preserved.
"""

import uuid
import pandas as pd


ID_MAP_PATH = 'data/resort_id_map.csv'
RESORTS_PATH = 'data/resorts.csv'


def get_slug(indy_page: str) -> str:
    """Extract the Indy Pass slug from the resort's indy_page URL."""
    return str(indy_page).rstrip('/').split('/')[-1]


def load_or_create_id_map() -> pd.DataFrame:
    try:
        return pd.read_csv(ID_MAP_PATH)
    except FileNotFoundError:
        return pd.DataFrame(columns=['resort_id', 'source', 'source_id'])


def main():
    resorts = pd.read_csv(RESORTS_PATH, na_values=[''], keep_default_na=False)

    # Drop legacy index column if present
    if 'index' in resorts.columns:
        resorts = resorts.drop(columns=['index'])

    # Skip if resort_id already exists and is fully populated
    if 'resort_id' in resorts.columns and resorts['resort_id'].notna().all():
        print('resort_id column already fully populated — nothing to do.')
        return

    id_map = load_or_create_id_map()
    existing = dict(zip(zip(id_map['source'], id_map['source_id']), id_map['resort_id']))

    new_rows = []
    resort_ids = []

    for _, row in resorts.iterrows():
        slug = get_slug(row.get('indy_page', ''))
        key = ('indy', slug)
        if key in existing:
            resort_ids.append(existing[key])
        else:
            new_id = str(uuid.uuid4())
            resort_ids.append(new_id)
            new_rows.append({'resort_id': new_id, 'source': 'indy', 'source_id': slug})

    resorts.insert(0, 'resort_id', resort_ids)

    if new_rows:
        id_map = pd.concat([id_map, pd.DataFrame(new_rows)], ignore_index=True)
        id_map.to_csv(ID_MAP_PATH, index=False)
        print(f'Added {len(new_rows)} new UUIDs to {ID_MAP_PATH}')
    else:
        print(f'All UUIDs already exist in {ID_MAP_PATH}')

    resorts.to_csv(RESORTS_PATH, index=False)
    print(f'Updated {RESORTS_PATH} with resort_id column')


if __name__ == '__main__':
    main()

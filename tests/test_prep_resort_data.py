import pandas as pd

import prep_resort_data


def test_assign_resort_ids_reuses_id_for_duplicate_slug_within_batch(tmp_path, monkeypatch):
    """Two rows sharing the same indy_page slug in one batch (e.g. the fan-out produced
    by a name-collision merge bug) must get the SAME newly-generated resort_id, not two
    different ones written to the id map."""
    id_map_path = tmp_path / 'resort_id_map.csv'
    monkeypatch.setattr(prep_resort_data, 'ID_MAP_PATH', str(id_map_path))

    resorts = pd.DataFrame(
        [
            {
                'name': 'Powder Ridge',
                'indy_page': 'https://www.indyskipass.com/our-resorts/powder-ridge-0',
            },
            {
                'name': 'Powder Ridge',
                'indy_page': 'https://www.indyskipass.com/our-resorts/powder-ridge-0',
            },
        ]
    )

    out = prep_resort_data.assign_resort_ids(resorts)

    assert out['resort_id'].nunique() == 1

    id_map = pd.read_csv(id_map_path)
    assert len(id_map) == 1


def test_merge_locations_does_not_fan_out_on_shared_name():
    """Two distinct resorts sharing a name (different location_name) must each match
    only their own location row, not the cartesian product of both — reproduces the bug
    surfaced by the two "Powder Ridge" resorts added to Indy Pass in 2026-09."""
    resorts = pd.DataFrame(
        [
            {'name': 'Powder Ridge', 'location_name': 'Kimball, MN, USA'},
            {'name': 'Powder Ridge', 'location_name': 'Middlefield, Connecticut'},
        ]
    )
    locations = pd.DataFrame(
        [
            {
                'name': 'Powder Ridge',
                'location_name': 'Kimball, MN, USA',
                'city': 'Kimball',
                'state': 'Minnesota',
                'country': 'United States',
            },
            {
                'name': 'Powder Ridge',
                'location_name': 'Middlefield, Connecticut',
                'city': 'Middlefield',
                'state': 'Connecticut',
                'country': 'United States',
            },
        ]
    )

    merged = prep_resort_data.merge_locations(resorts, locations)

    assert len(merged) == 2
    by_location = merged.set_index('location_name')
    assert by_location.loc['Kimball, MN, USA', 'city'] == 'Kimball'
    assert by_location.loc['Middlefield, Connecticut', 'city'] == 'Middlefield'


def test_merge_locations_legacy_cache_without_location_name_falls_back_to_name():
    """Old-format resort_locations.csv (no location_name column yet) should still merge
    by name alone, matching pre-fix behavior, rather than erroring."""
    resorts = pd.DataFrame([{'name': 'Resort A', 'location_name': 'Townsville, ST'}])
    locations = pd.DataFrame(
        [{'name': 'Resort A', 'city': 'Townsville', 'state': 'StateName', 'country': 'CountryName'}]
    )

    merged = prep_resort_data.merge_locations(resorts, locations)

    assert len(merged) == 1
    assert merged.iloc[0]['city'] == 'Townsville'

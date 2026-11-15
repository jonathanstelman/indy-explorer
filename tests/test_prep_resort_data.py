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


_COORD_COLS = [
    'name',
    'country',
    'latitude',
    'longitude',
    'geo_latitude',
    'geo_longitude',
    'indy_point_country',
    'indy_checked_latitude',
    'indy_checked_longitude',
]


def _coords_frame(rows):
    return pd.DataFrame(rows, columns=_COORD_COLS)


def test_apply_coordinate_fallback_replaces_indy_point_in_wrong_country():
    """Indy's roster put Hafjell (Øyer, Norway) at 44.14, -71.19 — New Hampshire."""
    resorts = _coords_frame(
        [
            [
                'Hafjell',
                'Norway',
                44.1417,
                -71.1880,
                61.342,
                10.500,
                'United States',
                44.1417,
                -71.1880,
            ]
        ]
    )

    out = prep_resort_data.apply_coordinate_fallback(resorts)

    assert out.iloc[0]['latitude'] == 61.342
    assert out.iloc[0]['longitude'] == 10.500


def test_apply_coordinate_fallback_keeps_far_indy_point_in_right_country():
    """A vague location_name ("NL, Canada") geocodes to a province centroid hundreds of km
    from the real resort. Indy's point is in the right country, so keep it."""
    resorts = _coords_frame(
        [['Marble Mountain', 'Canada', 48.948, -57.831, 54.273, -61.739, 'Canada', 48.948, -57.831]]
    )

    out = prep_resort_data.apply_coordinate_fallback(resorts)

    assert out.iloc[0]['latitude'] == 48.948


def test_apply_coordinate_fallback_ignores_stale_country_check():
    """If Indy's coordinates changed since the country check ran, the check no longer
    applies to them — keep Indy's current point."""
    resorts = _coords_frame(
        [['Hafjell', 'Norway', 61.30, 10.45, 61.342, 10.500, 'United States', 44.1417, -71.1880]]
    )

    out = prep_resort_data.apply_coordinate_fallback(resorts)

    assert out.iloc[0]['latitude'] == 61.30


def test_apply_coordinate_fallback_fills_missing_indy_coordinates():
    resorts = _coords_frame(
        [
            ['No Geocode', 'US', 44.0, -72.0, None, None, None, None, None],
            ['No Indy Coords', 'Austria', None, None, 46.9, 10.8, None, None, None],
        ]
    )

    out = prep_resort_data.apply_coordinate_fallback(resorts).set_index('name')

    assert out.loc['No Geocode', 'latitude'] == 44.0
    assert out.loc['No Indy Coords', 'latitude'] == 46.9
    assert out.loc['No Indy Coords', 'longitude'] == 10.8


_OVERRIDE_HEADER = 'source_id,field,indy_value,override_value,reason,source_url,added\n'


def _write_overrides(path, rows):
    path.write_text(_OVERRIDE_HEADER + ''.join(r + '\n' for r in rows), encoding='utf-8')


def _hochzeiger(acres=19136.0):
    return pd.DataFrame(
        [
            {
                'name': 'Hochzeiger Bergbahnen Pitztal AG',
                'indy_page': 'https://www.indyskipass.com/our-resorts/hochzeiger',
                'acres': acres,
            },
            {
                'name': 'Other',
                'indy_page': 'https://www.indyskipass.com/our-resorts/other',
                'acres': 500.0,
            },
        ]
    )


def test_apply_manual_overrides_replaces_value_when_indy_value_matches(tmp_path):
    path = tmp_path / 'manual_overrides.csv'
    _write_overrides(path, ['hochzeiger,acres,19136,271,~70x too large,https://x,2026-11-15'])

    out = prep_resort_data.apply_manual_overrides(_hochzeiger(), str(path)).set_index('name')

    assert out.loc['Hochzeiger Bergbahnen Pitztal AG', 'acres'] == 271
    assert out.loc['Other', 'acres'] == 500.0


def test_apply_manual_overrides_skips_stale_override(tmp_path, caplog):
    """If Indy has since changed the value, the override no longer applies — keep Indy's
    new value and warn so the stale row gets cleaned up."""
    path = tmp_path / 'manual_overrides.csv'
    _write_overrides(path, ['hochzeiger,acres,19136,271,~70x too large,https://x,2026-11-15'])

    with caplog.at_level('WARNING'):
        out = prep_resort_data.apply_manual_overrides(_hochzeiger(acres=280.0), str(path))

    assert out.set_index('name').loc['Hochzeiger Bergbahnen Pitztal AG', 'acres'] == 280.0
    assert any('hochzeiger' in r.message and 'stale' in r.message for r in caplog.records)


def test_apply_manual_overrides_warns_on_unknown_resort(tmp_path, caplog):
    path = tmp_path / 'manual_overrides.csv'
    _write_overrides(path, ['gone-resort,acres,100,10,test,https://x,2026-11-15'])

    with caplog.at_level('WARNING'):
        out = prep_resort_data.apply_manual_overrides(_hochzeiger(), str(path))

    assert out.set_index('name').loc['Hochzeiger Bergbahnen Pitztal AG', 'acres'] == 19136.0
    assert any('gone-resort' in r.message for r in caplog.records)


def test_apply_manual_overrides_blank_override_value_nulls_field(tmp_path):
    path = tmp_path / 'manual_overrides.csv'
    _write_overrides(path, ['hochzeiger,acres,19136,,no reliable figure,https://x,2026-11-15'])

    out = prep_resort_data.apply_manual_overrides(_hochzeiger(), str(path)).set_index('name')

    assert pd.isna(out.loc['Hochzeiger Bergbahnen Pitztal AG', 'acres'])


def test_apply_manual_overrides_missing_file_is_noop(tmp_path):
    out = prep_resort_data.apply_manual_overrides(_hochzeiger(), str(tmp_path / 'nope.csv'))

    assert out.set_index('name').loc['Hochzeiger Bergbahnen Pitztal AG', 'acres'] == 19136.0


def test_fill_xc_only_num_trails_from_xc_count():
    """Indy's roster page stopped publishing trail counts for some XC-only resorts
    (Bethel Village Trails, Woodstock Nordic Center) but their resort pages still list
    XC trails. For XC-only resorts num_trails == num_trails_xc by convention."""
    resorts = pd.DataFrame(
        [
            {
                'name': 'Bethel',
                'has_alpine': False,
                'has_cross_country': True,
                'num_trails': None,
                'num_trails_xc': 33.0,
            },
            {
                'name': 'Alpine+XC',
                'has_alpine': True,
                'has_cross_country': True,
                'num_trails': None,
                'num_trails_xc': 7.0,
            },
            {
                'name': 'Has Count',
                'has_alpine': False,
                'has_cross_country': True,
                'num_trails': 18.0,
                'num_trails_xc': 20.0,
            },
        ]
    )

    out = prep_resort_data.fill_xc_only_num_trails(resorts).set_index('name')

    assert out.loc['Bethel', 'num_trails'] == 33.0
    assert pd.isna(out.loc['Alpine+XC', 'num_trails'])
    assert out.loc['Has Count', 'num_trails'] == 18.0

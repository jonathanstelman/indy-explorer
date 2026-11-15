import json

import pandas as pd

import utils as location_utils


class _MockGMClient:
    def __init__(self, response):
        self._response = response

    def geocode(self, location_name):
        return self._response


class _CountingGMClient:
    """Like _MockGMClient, but records every location it was asked to geocode."""

    def __init__(self, response, reverse_country=None):
        self._response = response
        self._reverse_country = reverse_country
        self.calls = []
        self.reverse_calls = []

    def geocode(self, location_name):
        self.calls.append(location_name)
        return self._response

    def reverse_geocode(self, latlng, **kwargs):
        self.reverse_calls.append(latlng)
        if self._reverse_country is None:
            return []
        return [
            {
                "address_components": [
                    {"long_name": self._reverse_country, "types": ["country", "political"]}
                ]
            }
        ]


_GEOCODE_RESPONSE = [
    {
        "address_components": [
            {"long_name": "Townsville", "types": ["locality"]},
            {"long_name": "StateName", "types": ["administrative_area_level_1"]},
            {"long_name": "CountryName", "types": ["country"]},
        ]
    }
]


def _write_resorts_json(path, entries):
    data = {str(i): {"name": name, "location_name": loc} for i, (name, loc) in enumerate(entries)}
    path.write_text(json.dumps(data))


def test_get_normalized_location_success(monkeypatch):
    response = [
        {
            "address_components": [
                {"long_name": "Townsville", "types": ["locality"]},
                {"long_name": "StateName", "types": ["administrative_area_level_1"]},
                {"long_name": "CountryName", "types": ["country"]},
            ]
        }
    ]

    monkeypatch.setattr(location_utils, "gmaps", _MockGMClient(response))

    out = location_utils.get_normalized_location("Townsville, StateName")

    assert out["city"] == "Townsville"
    assert out["state"] == "StateName"
    assert out["country"] == "CountryName"


def test_get_normalized_location_empty_and_error(monkeypatch):
    # Empty result
    monkeypatch.setattr(location_utils, "gmaps", _MockGMClient([]))
    out = location_utils.get_normalized_location("Nowhere")
    assert out["city"] is None
    assert out["state"] is None
    assert out["country"] is None

    # geocode raises exception -> should be handled and return None fields
    class ExplodingClient:
        def geocode(self, _):
            raise Exception("api failure")

    monkeypatch.setattr(location_utils, "gmaps", ExplodingClient())
    out2 = location_utils.get_normalized_location("BadAPI")
    assert out2["city"] is None
    assert out2["state"] is None
    assert out2["country"] is None


def test_generate_resort_locations_csv_first_run_geocodes_all(tmp_path, monkeypatch):
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json(
        resorts_json, [("Resort A", "Townsville, ST"), ("Resort B", "Cityville, ST")]
    )

    client = _CountingGMClient(_GEOCODE_RESPONSE)
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert sorted(client.calls) == ["Cityville, ST", "Townsville, ST"]
    df = pd.read_csv(output_csv)
    assert set(df["name"]) == {"Resort A", "Resort B"}


def test_generate_resort_locations_csv_incremental_skips_cached(tmp_path, monkeypatch):
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json(
        resorts_json, [("Resort A", "Townsville, ST"), ("Resort B", "Cityville, ST")]
    )

    # Resort A is already cached from a prior run — should not be re-geocoded.
    pd.DataFrame(
        [{"name": "Resort A", "city": "Townsville", "state": "StateName", "country": "CountryName"}]
    ).to_csv(output_csv, index=False)

    client = _CountingGMClient(_GEOCODE_RESPONSE)
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert client.calls == ["Cityville, ST"]
    df = pd.read_csv(output_csv)
    assert set(df["name"]) == {"Resort A", "Resort B"}
    assert df.set_index("name").loc["Resort A", "city"] == "Townsville"


def test_generate_resort_locations_csv_geocodes_both_when_names_collide(tmp_path, monkeypatch):
    """Two different resorts can share a name (e.g. two "Powder Ridge" resorts on the
    2026-09 roster) — both must be geocoded and stay distinguishable by location_name,
    not collapsed into one cache entry keyed by name alone."""
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json(
        resorts_json,
        [("Powder Ridge", "Kimball, MN, USA"), ("Powder Ridge", "Middlefield, Connecticut")],
    )

    client = _CountingGMClient(_GEOCODE_RESPONSE)
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert sorted(client.calls) == ["Kimball, MN, USA", "Middlefield, Connecticut"]
    df = pd.read_csv(output_csv)
    assert len(df) == 2
    assert set(df["location_name"]) == {"Kimball, MN, USA", "Middlefield, Connecticut"}


def test_generate_resort_locations_csv_incremental_skips_cached_pair_not_just_name(
    tmp_path, monkeypatch
):
    """A cached (name, location_name) pair is skipped, but a new location_name sharing
    an already-cached name must still be geocoded — not skipped just because the name
    matches some other resort's cached row."""
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json(
        resorts_json,
        [("Powder Ridge", "Kimball, MN, USA"), ("Powder Ridge", "Middlefield, Connecticut")],
    )

    # Kimball, MN entry already cached from a prior run.
    pd.DataFrame(
        [
            {
                "name": "Powder Ridge",
                "location_name": "Kimball, MN, USA",
                "city": "Kimball",
                "state": "Minnesota",
                "country": "United States",
                "geo_latitude": 45.31,
                "geo_longitude": -94.30,
            }
        ]
    ).to_csv(output_csv, index=False)

    client = _CountingGMClient(_GEOCODE_RESPONSE)
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert client.calls == ["Middlefield, Connecticut"]
    df = pd.read_csv(output_csv)
    assert len(df) == 2


def test_generate_resort_locations_csv_full_regenerates_all(tmp_path, monkeypatch):
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json(resorts_json, [("Resort A", "Townsville, ST")])

    # Stale/incorrect cached entry — full=True should overwrite it, not skip it.
    pd.DataFrame(
        [
            {
                "name": "Resort A",
                "city": "WrongCity",
                "state": "WrongState",
                "country": "WrongCountry",
            }
        ]
    ).to_csv(output_csv, index=False)

    client = _CountingGMClient(_GEOCODE_RESPONSE)
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv), full=True)

    assert client.calls == ["Townsville, ST"]
    df = pd.read_csv(output_csv)
    assert df.set_index("name").loc["Resort A", "city"] == "Townsville"


_GEOCODE_RESPONSE_WITH_GEOMETRY = [
    {
        "address_components": _GEOCODE_RESPONSE[0]["address_components"],
        "geometry": {"location": {"lat": 61.2, "lng": 10.4}},
    }
]


def test_get_normalized_location_returns_coordinates(monkeypatch):
    monkeypatch.setattr(location_utils, "gmaps", _MockGMClient(_GEOCODE_RESPONSE_WITH_GEOMETRY))

    out = location_utils.get_normalized_location("Øyer, Norway")

    assert out["geo_latitude"] == 61.2
    assert out["geo_longitude"] == 10.4


def test_generate_resort_locations_csv_backfills_missing_coordinates(tmp_path, monkeypatch):
    """Cached rows that predate the geo_latitude/geo_longitude columns get one lookup to
    fill in coordinates; their city/state/country must be left untouched."""
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json(resorts_json, [("Resort A", "Townsville, ST")])
    pd.DataFrame(
        [
            {
                "name": "Resort A",
                "location_name": "Townsville, ST",
                "city": "CachedCity",
                "state": "CachedState",
                "country": "CachedCountry",
            }
        ]
    ).to_csv(output_csv, index=False)

    client = _CountingGMClient(_GEOCODE_RESPONSE_WITH_GEOMETRY)
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert client.calls == ["Townsville, ST"]
    row = pd.read_csv(output_csv).iloc[0]
    assert row["city"] == "CachedCity"
    assert row["geo_latitude"] == 61.2
    assert row["geo_longitude"] == 10.4


def test_generate_resort_locations_csv_skips_rows_with_coordinates(tmp_path, monkeypatch):
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json(resorts_json, [("Resort A", "Townsville, ST")])
    pd.DataFrame(
        [
            {
                "name": "Resort A",
                "location_name": "Townsville, ST",
                "city": "Townsville",
                "state": "StateName",
                "country": "CountryName",
                "geo_latitude": 1.0,
                "geo_longitude": 2.0,
            }
        ]
    ).to_csv(output_csv, index=False)

    client = _CountingGMClient(_GEOCODE_RESPONSE_WITH_GEOMETRY)
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert client.calls == []


def _write_resorts_json_with_coords(path, entries):
    data = {
        str(i): {
            "name": name,
            "location_name": loc,
            "coordinates": {"latitude": lat, "longitude": lng},
        }
        for i, (name, loc, lat, lng) in enumerate(entries)
    }
    path.write_text(json.dumps(data))


def test_generate_resort_locations_csv_country_checks_far_off_indy_point(tmp_path, monkeypatch):
    """Indy's point 5000+ km from the geocoded one gets a reverse lookup of its country,
    stored with the coordinates it was checked for."""
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json_with_coords(resorts_json, [("Hafjell", "Øyer, Norway", 44.14, -71.19)])

    client = _CountingGMClient(_GEOCODE_RESPONSE_WITH_GEOMETRY, reverse_country="United States")
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert client.reverse_calls == [(44.14, -71.19)]
    row = pd.read_csv(output_csv).iloc[0]
    assert row["indy_point_country"] == "United States"
    assert row["indy_checked_latitude"] == 44.14
    assert row["indy_checked_longitude"] == -71.19


def test_generate_resort_locations_csv_skips_country_check_when_close_or_already_checked(
    tmp_path, monkeypatch
):
    resorts_json = tmp_path / "resorts_raw.json"
    output_csv = tmp_path / "resort_locations.csv"
    _write_resorts_json_with_coords(
        resorts_json,
        [
            ("Near", "Near, NO", 61.25, 10.45),  # ~10 km from the geocoded 61.2, 10.4
            ("Checked", "Checked, NO", 44.14, -71.19),  # far, but already checked
        ],
    )
    pd.DataFrame(
        [
            {
                "name": "Checked",
                "location_name": "Checked, NO",
                "city": "C",
                "state": "S",
                "country": "Norway",
                "geo_latitude": 61.2,
                "geo_longitude": 10.4,
                "indy_point_country": "United States",
                "indy_checked_latitude": 44.14,
                "indy_checked_longitude": -71.19,
            }
        ]
    ).to_csv(output_csv, index=False)

    client = _CountingGMClient(_GEOCODE_RESPONSE_WITH_GEOMETRY, reverse_country="United States")
    monkeypatch.setattr(location_utils, "gmaps", client)

    location_utils.generate_resort_locations_csv(str(resorts_json), str(output_csv))

    assert client.reverse_calls == []

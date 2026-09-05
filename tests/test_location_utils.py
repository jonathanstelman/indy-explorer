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

    def __init__(self, response):
        self._response = response
        self.calls = []

    def geocode(self, location_name):
        self.calls.append(location_name)
        return self._response


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

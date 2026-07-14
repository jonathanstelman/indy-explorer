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

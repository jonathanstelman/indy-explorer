import types
from src import location_utils


class _MockGMClient:
    def __init__(self, response):
        self._response = response

    def geocode(self, location_name):
        return self._response


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

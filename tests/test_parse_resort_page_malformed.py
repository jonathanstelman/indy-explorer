import os
from src.page_scraper import parse_resort_page


def load_fixture(name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "fixtures", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_parse_resort_page_malformed_numbers():
    html = load_fixture("powder_ridge_malformed.html")
    result = parse_resort_page(html, resort_id="malformed-id", resort_slug="powder_ridge_malformed")

    # Basic identification
    assert result["id"] == "malformed-id"
    assert result["slug"] == "powder_ridge_malformed"
    assert result["website"] == "https://powderridge.example.com"

    # Malformed numeric fields should not raise and should be None when digits are missing
    assert result["trails"] is None
    assert result["lifts"] is None
    assert result["acres"] is None

    # Trail length missing -> None
    assert result["trail_length_km"] is None
    assert result["trail_length_mi"] is None

    # Elevation tags present but no numbers -> None values
    assert result["vertical_base_ft"] is None
    assert result["vertical_summit_ft"] is None
    assert result["vertical_elevation_ft"] is None

    # Snowfall fields should remain unset (None)
    assert result["snowfall_average_in"] is None
    assert result["snowfall_high_in"] is None

import os
from page_scraper import parse_resort_page


def load_fixture(name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "fixtures", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_parse_resort_page_basic_fields():
    html = load_fixture("powder_ridge_fixture.html")
    result = parse_resort_page(html, resort_id="test-id", resort_slug="powder_ridge")

    assert result["id"] == "test-id"
    assert result["slug"] == "powder_ridge"
    assert result["name"] == "Powder Ridge"
    assert "description" in result and "Test description" in result["description"]

    # Numeric fields
    assert result["trails"] == 15
    assert result["lifts"] == 3
    assert result["acres"] == 85
    assert result["trail_length_km"] == 20

    # Booleans
    assert result["is_cross_country"] is True
    assert result["is_dog_friendly"] is True
    assert result["has_snowshoeing"] is False
    assert result["terrain_parks"] is True
    assert result["night_skiing"] is False

    # Elevation
    assert result["vertical_base_ft"] == 800
    assert result["vertical_summit_ft"] == 1200
    assert result["vertical_elevation_ft"] == 400

    # Difficulty
    assert result["difficulty_beginner"] == 30
    assert result["difficulty_intermediate"] == 50
    assert result["difficulty_advanced"] == 20

    # Snowfall
    assert result["snowfall_average_in"] == 80
    assert result["snowfall_high_in"] == 120


def test_parse_resort_page_xc_fields():
    """Alpine + XC resorts expose separate -xc suffixed stats (issue #11)."""
    html = load_fixture("powder_ridge_fixture.html")
    result = parse_resort_page(html, resort_id="test-id", resort_slug="powder_ridge")

    # XC stats come from the -xc suffixed elements, alpine stats stay untouched
    assert result["trails_xc"] == 30
    assert result["difficulty_beginner_xc"] == 35
    assert result["difficulty_intermediate_xc"] == 30
    assert result["difficulty_advanced_xc"] == 35

    assert result["trails"] == 15
    assert result["difficulty_beginner"] == 30
    assert result["difficulty_intermediate"] == 50
    assert result["difficulty_advanced"] == 20


def test_parse_resort_page_xc_only():
    """XC-only resorts have no unsuffixed (alpine) elements — only -xc values."""
    html = load_fixture("nordic_hollow_fixture.html")
    result = parse_resort_page(html, resort_id="xc-id", resort_slug="nordic_hollow")

    assert result["trails_xc"] == 30
    assert result["difficulty_beginner_xc"] == 20
    assert result["difficulty_intermediate_xc"] == 60
    assert result["difficulty_advanced_xc"] == 20

    # Alpine fields fall back to their existing defaults
    assert result["trails"] == 0
    assert result["difficulty_beginner"] is None
    assert result["difficulty_intermediate"] is None
    assert result["difficulty_advanced"] is None

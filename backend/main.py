import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from typing import Optional

from data import load_resorts
from models import Resort, ResortSummary

_resorts: list[Resort] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _resorts
    _resorts = load_resorts()
    yield


app = FastAPI(title="Indy Explorer API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


def _parse_date_list(value: Optional[str]) -> set[str]:
    """Parse a JSON-encoded date array from the CSV into a set of date strings."""
    if not value:
        return set()
    try:
        return set(json.loads(value))
    except (json.JSONDecodeError, TypeError):
        return set()


@app.get("/resorts", response_model=list[ResortSummary])
def get_resorts(
    search: Optional[str] = Query(default=None),
    region: list[str] = Query(default=[]),
    country: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    # Boolean feature flags
    has_alpine: Optional[bool] = Query(default=None),
    has_cross_country: Optional[bool] = Query(default=None),
    has_night_skiing: Optional[bool] = Query(default=None),
    has_terrain_parks: Optional[bool] = Query(default=None),
    is_dog_friendly: Optional[bool] = Query(default=None),
    has_snowshoeing: Optional[bool] = Query(default=None),
    is_allied: Optional[bool] = Query(default=None),
    ltt_available: Optional[bool] = Query(default=None),
    has_peak_rankings: Optional[bool] = Query(default=None),
    reservation_required: Optional[bool] = Query(default=None),
    # Numeric range filters (inclusive; resorts with null values are excluded)
    min_vertical: Optional[float] = Query(default=None),
    max_vertical: Optional[float] = Query(default=None),
    min_trails: Optional[float] = Query(default=None),
    max_trails: Optional[float] = Query(default=None),
    min_lifts: Optional[float] = Query(default=None),
    max_lifts: Optional[float] = Query(default=None),
    min_trail_length: Optional[float] = Query(default=None),
    max_trail_length: Optional[float] = Query(default=None),
    # Peak Rankings score range filters (inclusive; resorts with null values are excluded)
    pr_total_min: Optional[float] = Query(default=None),
    pr_total_max: Optional[float] = Query(default=None),
    pr_snow_min: Optional[float] = Query(default=None),
    pr_snow_max: Optional[float] = Query(default=None),
    pr_resiliency_min: Optional[float] = Query(default=None),
    pr_resiliency_max: Optional[float] = Query(default=None),
    pr_size_min: Optional[float] = Query(default=None),
    pr_size_max: Optional[float] = Query(default=None),
    pr_terrain_diversity_min: Optional[float] = Query(default=None),
    pr_terrain_diversity_max: Optional[float] = Query(default=None),
    pr_challenge_min: Optional[float] = Query(default=None),
    pr_challenge_max: Optional[float] = Query(default=None),
    pr_lifts_min: Optional[float] = Query(default=None),
    pr_lifts_max: Optional[float] = Query(default=None),
    pr_crowd_flow_min: Optional[float] = Query(default=None),
    pr_crowd_flow_max: Optional[float] = Query(default=None),
    pr_facilities_min: Optional[float] = Query(default=None),
    pr_facilities_max: Optional[float] = Query(default=None),
    pr_navigation_min: Optional[float] = Query(default=None),
    pr_navigation_max: Optional[float] = Query(default=None),
    pr_mountain_aesthetic_min: Optional[float] = Query(default=None),
    pr_mountain_aesthetic_max: Optional[float] = Query(default=None),
    # Peak Rankings categorical multi-value filters
    pr_lodging: list[str] = Query(default=[]),
    pr_apres_ski: list[str] = Query(default=[]),
    pr_access_road: list[str] = Query(default=[]),
    pr_ability_low: list[str] = Query(default=[]),
    pr_ability_high: list[str] = Query(default=[]),
    # Blackout date filters (comma-separated YYYY-MM-DD dates)
    blackout_dates: Optional[str] = Query(default=None),
    ltt_dates: Optional[str] = Query(default=None),
):
    results = _resorts

    if search:
        term = search.lower()
        results = [
            r
            for r in results
            if term in (r.name or '').lower()
            or term in (r.city or '').lower()
            or term in (r.state or '').lower()
            or term in (r.country or '').lower()
        ]

    if region:
        region_set = {v.lower() for v in region}
        results = [r for r in results if (r.region or '').lower() in region_set]

    if country:
        c = country.lower()
        results = [r for r in results if (r.country or '').lower() == c]

    if state:
        s = state.lower()
        results = [r for r in results if (r.state or '').lower() == s]

    # Boolean feature flags
    bool_filters = [
        ('has_alpine', has_alpine),
        ('has_cross_country', has_cross_country),
        ('has_night_skiing', has_night_skiing),
        ('has_terrain_parks', has_terrain_parks),
        ('is_dog_friendly', is_dog_friendly),
        ('has_snowshoeing', has_snowshoeing),
        ('is_allied', is_allied),
        ('ltt_available', ltt_available),
    ]
    for field, value in bool_filters:
        if value is not None:
            results = [r for r in results if getattr(r, field) == value]

    if has_peak_rankings is not None:
        if has_peak_rankings:
            results = [r for r in results if r.pr_total is not None]
        else:
            results = [r for r in results if r.pr_total is None]

    if reservation_required is not None:
        if reservation_required:
            results = [r for r in results if r.reservation_status == 'Required']
        else:
            results = [r for r in results if r.reservation_status != 'Required']

    # Numeric range filters (resorts with null values are excluded)
    range_filters = [
        ('vertical', min_vertical, max_vertical),
        ('num_trails', min_trails, max_trails),
        ('num_lifts', min_lifts, max_lifts),
        ('trail_length_mi', min_trail_length, max_trail_length),
        ('pr_total', pr_total_min, pr_total_max),
        ('pr_snow', pr_snow_min, pr_snow_max),
        ('pr_resiliency', pr_resiliency_min, pr_resiliency_max),
        ('pr_size', pr_size_min, pr_size_max),
        ('pr_terrain_diversity', pr_terrain_diversity_min, pr_terrain_diversity_max),
        ('pr_challenge', pr_challenge_min, pr_challenge_max),
        ('pr_lifts', pr_lifts_min, pr_lifts_max),
        ('pr_crowd_flow', pr_crowd_flow_min, pr_crowd_flow_max),
        ('pr_facilities', pr_facilities_min, pr_facilities_max),
        ('pr_navigation', pr_navigation_min, pr_navigation_max),
        ('pr_mountain_aesthetic', pr_mountain_aesthetic_min, pr_mountain_aesthetic_max),
    ]
    for field, lo, hi in range_filters:
        if lo is not None:
            results = [
                r for r in results if getattr(r, field) is not None and getattr(r, field) >= lo
            ]
        if hi is not None:
            results = [
                r for r in results if getattr(r, field) is not None and getattr(r, field) <= hi
            ]

    # Peak Rankings categorical multi-value filters
    categorical_filters = [
        ('pr_lodging', pr_lodging),
        ('pr_apres_ski', pr_apres_ski),
        ('pr_access_road', pr_access_road),
        ('pr_ability_low', pr_ability_low),
        ('pr_ability_high', pr_ability_high),
    ]
    for field, values in categorical_filters:
        if values:
            value_set = {v.lower() for v in values}
            results = [r for r in results if (getattr(r, field) or '').lower() in value_set]

    # Blackout date filters — exclude resorts blacked out on any of the given dates
    if blackout_dates:
        selected = {d.strip() for d in blackout_dates.split(',')}
        results = [
            r for r in results if selected.isdisjoint(_parse_date_list(r.blackout_all_dates))
        ]

    if ltt_dates:
        selected = {d.strip() for d in ltt_dates.split(',')}
        results = [
            r for r in results if selected.isdisjoint(_parse_date_list(r.ltt_blackout_all_dates))
        ]

    return [ResortSummary(**r.model_dump()) for r in results]

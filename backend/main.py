from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from typing import Optional

from data import load_resorts
from models import ResortSummary

_resorts: list[ResortSummary] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _resorts
    _resorts = [ResortSummary(**r.model_dump()) for r in load_resorts()]
    yield


app = FastAPI(title="Indy Explorer API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


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
    reservation_required: Optional[bool] = Query(default=None),
    # Numeric range filters (inclusive)
    min_vertical: Optional[float] = Query(default=None),
    max_vertical: Optional[float] = Query(default=None),
    min_trails: Optional[float] = Query(default=None),
    max_trails: Optional[float] = Query(default=None),
    min_lifts: Optional[float] = Query(default=None),
    max_lifts: Optional[float] = Query(default=None),
    min_trail_length: Optional[float] = Query(default=None),
    max_trail_length: Optional[float] = Query(default=None),
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

    # Boolean feature flags — only filter when explicitly set to True
    bool_filters = [
        ('has_alpine', has_alpine),
        ('has_cross_country', has_cross_country),
        ('has_night_skiing', has_night_skiing),
        ('has_terrain_parks', has_terrain_parks),
        ('is_dog_friendly', is_dog_friendly),
        ('has_snowshoeing', has_snowshoeing),
        ('is_allied', is_allied),
    ]
    for field, value in bool_filters:
        if value is not None:
            results = [r for r in results if getattr(r, field) == value]

    if reservation_required is not None:
        if reservation_required:
            results = [r for r in results if r.reservation_status == 'Required']
        else:
            results = [r for r in results if r.reservation_status != 'Required']

    # Numeric range filters (skip resorts with no data for the field)
    range_filters = [
        ('vertical', min_vertical, max_vertical),
        ('num_trails', min_trails, max_trails),
        ('num_lifts', min_lifts, max_lifts),
        ('trail_length_mi', min_trail_length, max_trail_length),
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

    return results

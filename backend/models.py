import logging
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r'^https?://')

# (lo, hi) bounds for fields where an out-of-range value most likely means a scraping
# glitch (e.g. an extra digit) rather than a real resort. Ceilings are set well above the
# largest real value currently in data/resorts.csv, not at some theoretical world-record max.
_NONNEG_BOUNDS: dict[str, tuple[float, Optional[float]]] = {
    'acres': (0, 50_000),
    'num_trails': (0, 1_000),
    'num_trails_xc': (0, 500),
    'num_lifts': (0, 500),
    'vertical': (0, 15_000),
    'vertical_base_ft': (0, 20_000),
    'vertical_summit_ft': (0, 25_000),
    'vertical_elevation_ft': (0, 15_000),
    'snowfall_average_in': (0, 2_000),
    'snowfall_high_in': (0, 2_500),
    'trail_length_mi': (0, 200),
}

_DIFFICULTY_FIELDS = (
    'difficulty_beginner',
    'difficulty_intermediate',
    'difficulty_advanced',
    'difficulty_beginner_xc',
    'difficulty_intermediate_xc',
    'difficulty_advanced_xc',
)

# Peak Rankings has, at least once, scored a resort an 11 (Spinal Tap style) — the ceiling
# accommodates that rather than treating it as a data error.
_PR_SUBSCORE_FIELDS = (
    'pr_snow',
    'pr_resiliency',
    'pr_size',
    'pr_terrain_diversity',
    'pr_challenge',
    'pr_lifts',
    'pr_crowd_flow',
    'pr_facilities',
    'pr_navigation',
    'pr_mountain_aesthetic',
)


def _null_if_out_of_range(value, lo, hi, field_name, resort_id):
    if value is None:
        return None
    if (lo is not None and value < lo) or (hi is not None and value > hi):
        logger.warning(
            'resort=%s field=%s value=%r out of range [%s, %s] — nulling',
            resort_id,
            field_name,
            value,
            lo,
            hi,
        )
        return None
    return value


def _null_if_bad_url(value, field_name, resort_id):
    if value is None:
        return None
    if not URL_PATTERN.match(value):
        logger.warning(
            'resort=%s field=%s value=%r is not a valid http(s) URL — nulling',
            resort_id,
            field_name,
            value,
        )
        return None
    return value


class RangeField(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class DateRangeField(BaseModel):
    min: Optional[str] = None  # ISO date string YYYY-MM-DD
    max: Optional[str] = None


class MetaResponse(BaseModel):
    last_pipeline_run: Optional[str] = None  # ISO datetime from pipeline_metadata.json
    regions: list[str]
    countries: list[str]
    states: list[str]
    vertical: RangeField
    acres: RangeField
    num_trails: RangeField
    num_trails_xc: RangeField
    num_lifts: RangeField
    trail_length_mi: RangeField
    pr_total: RangeField
    pr_snow: RangeField
    pr_resiliency: RangeField
    pr_size: RangeField
    pr_terrain_diversity: RangeField
    pr_challenge: RangeField
    pr_lifts: RangeField
    pr_crowd_flow: RangeField
    pr_facilities: RangeField
    pr_navigation: RangeField
    pr_mountain_aesthetic: RangeField
    blackout_date_range: DateRangeField
    ltt_date_range: DateRangeField


class ResortSummary(BaseModel):
    """Full projection returned by GET /resorts — used by both the map and data table."""

    resort_id: str
    name: str
    region: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    reservation_status: str
    reservation_url: Optional[str] = None
    indy_page: str
    website: Optional[str] = None
    is_allied: Optional[bool] = None
    has_alpine: Optional[bool] = None
    has_cross_country: Optional[bool] = None
    has_night_skiing: Optional[bool] = None
    has_terrain_parks: Optional[bool] = None
    is_dog_friendly: Optional[bool] = None
    has_snowshoeing: Optional[bool] = None
    ltt_available: Optional[bool] = None
    vertical: Optional[float] = None
    vertical_base_ft: Optional[float] = None
    vertical_summit_ft: Optional[float] = None
    acres: Optional[float] = None
    num_trails: Optional[float] = None
    num_trails_xc: Optional[float] = None
    num_lifts: Optional[float] = None
    trail_length_mi: Optional[float] = None
    difficulty_beginner: Optional[float] = None
    difficulty_intermediate: Optional[float] = None
    difficulty_advanced: Optional[float] = None
    difficulty_beginner_xc: Optional[float] = None
    difficulty_intermediate_xc: Optional[float] = None
    difficulty_advanced_xc: Optional[float] = None
    snowfall_average_in: Optional[float] = None
    snowfall_high_in: Optional[float] = None
    blackout_count: Optional[int] = None
    ltt_blackout_count: Optional[int] = None
    pr_total: Optional[float] = None
    pr_overall_rank: Optional[float] = None
    pr_regional_rank: Optional[float] = None
    pr_region: Optional[str] = None
    pr_snow: Optional[float] = None
    pr_resiliency: Optional[float] = None
    pr_size: Optional[float] = None
    pr_terrain_diversity: Optional[float] = None
    pr_challenge: Optional[float] = None
    pr_lifts: Optional[float] = None
    pr_crowd_flow: Optional[float] = None
    pr_facilities: Optional[float] = None
    pr_navigation: Optional[float] = None
    pr_mountain_aesthetic: Optional[float] = None
    pr_lodging: Optional[str] = None
    pr_apres_ski: Optional[str] = None
    pr_access_road: Optional[str] = None
    pr_ability_low: Optional[str] = None
    pr_ability_high: Optional[str] = None
    pr_nearest_cities: Optional[str] = None
    pr_pass_affiliation: Optional[str] = None


class Resort(BaseModel):
    resort_id: str
    name: str
    location_name: Optional[str] = None
    description: Optional[str] = None
    region: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    indy_page: str = Field(pattern=URL_PATTERN)
    website: Optional[str] = None
    reservation_status: str
    reservation_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    vertical: Optional[float] = None
    has_alpine: Optional[bool] = None
    has_cross_country: Optional[bool] = None
    is_allied: Optional[bool] = None
    acres: Optional[float] = None
    num_trails: Optional[float] = None
    num_trails_xc: Optional[float] = None
    trail_length_mi: Optional[float] = None
    num_lifts: Optional[float] = None
    vertical_base_ft: Optional[float] = None
    vertical_summit_ft: Optional[float] = None
    vertical_elevation_ft: Optional[float] = None
    has_night_skiing: Optional[bool] = None
    has_terrain_parks: Optional[bool] = None
    is_dog_friendly: Optional[bool] = None
    has_snowshoeing: Optional[bool] = None
    difficulty_beginner: Optional[float] = None
    difficulty_intermediate: Optional[float] = None
    difficulty_advanced: Optional[float] = None
    difficulty_beginner_xc: Optional[float] = None
    difficulty_intermediate_xc: Optional[float] = None
    difficulty_advanced_xc: Optional[float] = None
    snowfall_average_in: Optional[float] = None
    snowfall_high_in: Optional[float] = None
    has_alpine_display: Optional[str] = None
    has_cross_country_display: Optional[str] = None
    is_dog_friendly_display: Optional[str] = None
    has_night_skiing_display: Optional[str] = None
    has_terrain_parks_display: Optional[str] = None
    is_allied_display: Optional[str] = None
    location_name_tt: Optional[str] = None
    num_trails_tt: Optional[str] = None
    num_lifts_tt: Optional[str] = None
    blackout_named_ranges: Optional[str] = None
    blackout_additional_dates: Optional[str] = None
    blackout_all_dates: Optional[str] = None
    blackout_count: Optional[int] = None
    ltt_available: Optional[bool] = None
    ltt_blackout_all_dates: Optional[str] = None
    ltt_blackout_count: Optional[int] = None
    pr_snow: Optional[float] = None
    pr_resiliency: Optional[float] = None
    pr_size: Optional[float] = None
    pr_terrain_diversity: Optional[float] = None
    pr_challenge: Optional[float] = None
    pr_lifts: Optional[float] = None
    pr_crowd_flow: Optional[float] = None
    pr_facilities: Optional[float] = None
    pr_navigation: Optional[float] = None
    pr_mountain_aesthetic: Optional[float] = None
    pr_total: Optional[float] = None
    pr_overall_rank: Optional[float] = None
    pr_regional_rank: Optional[float] = None
    pr_region: Optional[str] = None
    pr_lodging: Optional[str] = None
    pr_apres_ski: Optional[str] = None
    pr_access_road: Optional[str] = None
    pr_ability_low: Optional[str] = None
    pr_ability_high: Optional[str] = None
    pr_nearest_cities: Optional[str] = None
    pr_pass_affiliation: Optional[str] = None
    pr_total_tt: Optional[str] = None

    @field_validator(*_NONNEG_BOUNDS.keys(), mode='after')
    @classmethod
    def _validate_nonneg_bounded(cls, v, info):
        lo, hi = _NONNEG_BOUNDS[info.field_name]
        return _null_if_out_of_range(v, lo, hi, info.field_name, info.data.get('resort_id'))

    @field_validator(*_DIFFICULTY_FIELDS, mode='after')
    @classmethod
    def _validate_difficulty(cls, v, info):
        return _null_if_out_of_range(v, 0, 100, info.field_name, info.data.get('resort_id'))

    @field_validator(*_PR_SUBSCORE_FIELDS, mode='after')
    @classmethod
    def _validate_pr_subscore(cls, v, info):
        return _null_if_out_of_range(v, 0, 11, info.field_name, info.data.get('resort_id'))

    @field_validator('pr_total', mode='after')
    @classmethod
    def _validate_pr_total(cls, v, info):
        return _null_if_out_of_range(v, 0, None, info.field_name, info.data.get('resort_id'))

    @field_validator('pr_overall_rank', 'pr_regional_rank', mode='after')
    @classmethod
    def _validate_pr_rank(cls, v, info):
        return _null_if_out_of_range(v, 1, None, info.field_name, info.data.get('resort_id'))

    @field_validator('website', 'reservation_url', mode='after')
    @classmethod
    def _validate_optional_url(cls, v, info):
        return _null_if_bad_url(v, info.field_name, info.data.get('resort_id'))

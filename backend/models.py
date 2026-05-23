from typing import Optional
from pydantic import BaseModel


class RangeField(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class DateRangeField(BaseModel):
    min: Optional[str] = None  # ISO date string YYYY-MM-DD
    max: Optional[str] = None


class MetaResponse(BaseModel):
    regions: list[str]
    countries: list[str]
    states: list[str]
    vertical: RangeField
    num_trails: RangeField
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
    vertical_meters: Optional[float] = None
    vertical_base_ft: Optional[float] = None
    vertical_summit_ft: Optional[float] = None
    acres: Optional[float] = None
    num_trails: Optional[float] = None
    num_lifts: Optional[float] = None
    trail_length_mi: Optional[float] = None
    trail_length_km: Optional[float] = None
    difficulty_beginner: Optional[float] = None
    difficulty_intermediate: Optional[float] = None
    difficulty_advanced: Optional[float] = None
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
    indy_page: str
    website: Optional[str] = None
    reservation_status: str
    reservation_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    vertical: Optional[float] = None
    vertical_meters: Optional[float] = None
    has_alpine: Optional[bool] = None
    has_cross_country: Optional[bool] = None
    is_allied: Optional[bool] = None
    acres: Optional[float] = None
    num_trails: Optional[float] = None
    trail_length_mi: Optional[float] = None
    trail_length_km: Optional[float] = None
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
    snowfall_average_in: Optional[float] = None
    snowfall_high_in: Optional[float] = None
    has_alpine_display: Optional[str] = None
    has_cross_country_display: Optional[str] = None
    is_dog_friendly_display: Optional[str] = None
    has_night_skiing_display: Optional[str] = None
    has_terrain_parks_display: Optional[str] = None
    is_allied_display: Optional[str] = None
    location_name_tt: Optional[str] = None
    acres_tt: Optional[str] = None
    vertical_tt: Optional[str] = None
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

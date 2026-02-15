"""
Streamlit app to display Indy Pass resorts in an interactive map and table
"""

from datetime import date, datetime, timedelta
import json
from typing import List, Optional
import importlib
import os

import matplotlib.pyplot as plt
import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit_antd_components as sac

import map_config

if os.getenv("MAP_CONFIG_RELOAD", "").lower() in ("1", "true", "yes"):
    importlib.reload(map_config)

MAPBOX_TOKEN = st.secrets["MAPBOX_TOKEN"]

# Constants
COLORS = {
    'red': [197, 42, 28, 200],
    'blue': [0, 10, 200, 160],
    'pale-blue': [170, 220, 250, 255],
    'purple': [128, 0, 128, 160],
    'grey': [30, 30, 30, 160],
    'pale-grey': [240, 240, 240, 255],
}
MIN_POINT_RADIUS = 5_000
MAX_POINT_RADIUS = 50_000
MAP_HEIGHT = 800
REGION_ORDER = [
    'Midwest',
    'East',
    'Japan',
    'Mid-Atlantic',
    'Europe',
    'Canada',
    'West',
    'Rockies',
]
REGION_ZOOM = {
    'Midwest': 4.8,
    'East': 5.7,
    'Japan': 4.4,
    'Mid-Atlantic': 5.2,
    'Europe': 3.6,
    'Canada': 3.7,
    'West': 4.3,
    'Rockies': 4.4,
}
MAX_AUTO_ZOOM = 8.0


# Functions for plotting and search
def get_color(resort):
    """
    Returns the color that a resort should appear on the map
    """
    if resort.is_allied:
        return COLORS['grey']
    if resort.has_cross_country and not resort.has_alpine:
        return COLORS['blue']
    if resort.has_alpine and resort.has_cross_country:
        return COLORS['purple']
    return COLORS['red']


def get_radius(resort):
    """
    Returns the radius that a resort should display on the map
    """
    if resort.has_cross_country and not resort.has_alpine:
        return MIN_POINT_RADIUS

    if resort.acres:
        radius = resort.acres * 30
    else:
        # use this weird formula I made up to set display radius based on other data
        num_trails = resort.num_trails if resort.num_trails else 5
        vertical = resort.vertical if resort.vertical else 300
        num_lifts = resort.num_lifts if resort.num_lifts else 0
        radius = 2 * (50 * num_trails + 1.5 * vertical + 5 * num_lifts)

    # set min and max radius
    return min(MAX_POINT_RADIUS, max(MIN_POINT_RADIUS, radius))


def get_search_terms(resort):
    """
    Concatenates relevant fields for search
    """
    search_fields = [
        resort['name'],
        resort.get('region'),
        resort['city'],
        resort['state'],
        resort['country'],
    ]
    search_terms = [f for f in search_fields if isinstance(f, str)]
    return ' '.join(search_terms).lower()


def rgba_to_hex(rgba):
    r, g, b, a = rgba
    return f'#{r:02x}{g:02x}{b:02x}{a:02x}'


def format_blackout_dates(value: str) -> str:
    if not value:
        return ''
    try:
        dates = json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError:
        return ''
    if not dates:
        return ''
    return ', '.join(dates)


def parse_blackout_dates(value: str) -> List[str]:
    if not value:
        return []
    try:
        return json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError:
        return []


def date_range_strings(start: date, end: date) -> List[str]:
    days = (end - start).days
    return [(start + timedelta(days=offset)).strftime('%Y-%m-%d') for offset in range(days + 1)]


def parse_iso_date(value: str) -> Optional[date]:
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def create_elevation_plot(base, summit, vertical):
    """Make a plot to display the resort elevation"""
    SEA_LEVEL = 0
    BASE_HEIGHT = 0.6
    SUMMIT_HEIGHT = 3
    VERTICAL_HEIGHT = SUMMIT_HEIGHT - BASE_HEIGHT

    mountain_coords = [
        [0, BASE_HEIGHT],
        [2, BASE_HEIGHT + VERTICAL_HEIGHT * 0.8],
        [3, BASE_HEIGHT + VERTICAL_HEIGHT * 0.6],
        [4, SUMMIT_HEIGHT],
        [6, BASE_HEIGHT],
    ]
    fig, ax = plt.subplots(figsize=(3, 3))
    mountain = plt.Polygon(
        mountain_coords,
        closed=True,
        edgecolor='black',
        facecolor=rgba_to_hex(COLORS['pale-grey']),
    )
    ax.add_patch(mountain)

    # Sea-level indicator
    ax.plot((-1, 8), (SEA_LEVEL, SEA_LEVEL), marker=None, linestyle='-', color='lightblue')

    # text / annotations
    ax.text(
        -0.5,
        BASE_HEIGHT,
        f'{int(base)} ft',
        verticalalignment='baseline',
        horizontalalignment='right',
        color=rgba_to_hex(COLORS['grey']),
        fontsize='x-small',
    )
    ax.text(
        -0.5,
        SUMMIT_HEIGHT,
        f'{int(summit)} ft',
        verticalalignment='top',
        horizontalalignment='right',
        color='grey',
        fontsize='x-small',
    )
    ax.annotate(
        '',
        xy=(0, 3),
        xytext=(0, BASE_HEIGHT),
        arrowprops=dict(arrowstyle='<->', color=rgba_to_hex(COLORS['red'])),
    )
    ax.text(
        -0.3,
        VERTICAL_HEIGHT / 2 + BASE_HEIGHT,
        f'{int(vertical)} ft',
        verticalalignment='center',
        horizontalalignment='right',
        color=rgba_to_hex(COLORS['red']),
        fontsize='x-small',
    )

    ax.set_xlim(-2, 7)
    ax.set_ylim(-0.5, 3)
    ax.set_aspect('equal')
    ax.axis('off')

    return fig


def create_difficulty_chart(beginner, intermediate, advanced):
    levels = [beginner, intermediate, advanced]
    labels = [
        f'Beginner – {beginner}%',
        f'Intermediate - {intermediate}%',
        f'Advanced - {advanced}%',
    ]
    colors = [rgba_to_hex(c) for c in [COLORS['pale-blue'], COLORS['blue'], COLORS['purple']]]

    fig, ax = plt.subplots(figsize=(2, 2))
    ax.pie(
        levels,
        radius=1,
        colors=colors,
        wedgeprops={"linewidth": 2, "edgecolor": "white"},
        labels=labels,
        labeldistance=0.3,
        textprops={'fontsize': 6},
    )

    ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig


def create_snowfall_barplot(snowfall_avg, snowfall_max):
    """
    Create a barplot to display the average and maximum annual snowfall.
    """
    fig, ax = plt.subplots(figsize=(3, 2))
    categories = ['Average Snowfall', 'Maximum Snowfall']
    values = [snowfall_avg, snowfall_max]
    colors = [rgba_to_hex(COLORS['pale-blue']), rgba_to_hex(COLORS['pale-blue'])]

    ax.bar(categories, values, color=colors)

    for i, v in enumerate(values):
        ax.text(i, v + 5, f'{int(v)} in', ha='center', color='black', fontsize=6)

    # Horizontal gridlines
    ax.yaxis.grid(True, linestyle='-', linewidth=0.5, alpha=0.3)
    ax.set_axisbelow(True)

    # Hide border except bottom baseline
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_linewidth(1)
    ax.spines['bottom'].set_color('grey')
    ax.tick_params(axis='x', which='both', bottom=False, top=False, labelsize=6)
    ax.tick_params(axis='y', which='both', left=False, right=False, labelsize=6)

    return fig


# Load resort data
resorts = pd.read_csv('data/resorts.csv', index_col='index', na_values=[''], keep_default_na=False)

# Drop resorts that don't have coordinate data (cannot be mapped)
resorts = resorts[resorts.latitude.notnull()]

# Blackout display helpers
if 'blackout_all_dates' in resorts.columns:
    resorts['blackout_dates_display'] = resorts['blackout_all_dates'].apply(format_blackout_dates)
    resorts['blackout_dates_list'] = resorts['blackout_all_dates'].apply(parse_blackout_dates)
else:
    resorts['blackout_dates_display'] = ''
    resorts['blackout_dates_list'] = [[] for _ in range(len(resorts))]
if 'blackout_count' not in resorts.columns:
    resorts['blackout_count'] = 0
resorts['blackout_has_display'] = resorts['blackout_count'].apply(
    lambda c: 'Yes' if c and int(c) > 0 else 'No'
)

if 'pr_total_tt' not in resorts.columns:
    resorts['pr_total_tt'] = '---'
if 'pr_total' in resorts.columns:
    resorts['has_peak_rankings'] = resorts['pr_total'].notnull()
else:
    resorts['has_peak_rankings'] = False

if 'reservation_status' not in resorts.columns:
    resorts['reservation_status'] = 'Not Required'
resorts['reservation_status'] = resorts['reservation_status'].replace('', 'Not Required')
if 'reservation_url' not in resorts.columns:
    resorts['reservation_url'] = ''
resorts['reservation_url_display'] = resorts['reservation_url'].apply(
    lambda v: v if isinstance(v, str) and v else 'n/a'
)

all_blackout_dates = sorted(
    {d for dates in resorts['blackout_dates_list'] for d in dates if isinstance(d, str)}
)
if all_blackout_dates:
    min_blackout_date = parse_iso_date(all_blackout_dates[0]) or date.today()
    max_blackout_date = parse_iso_date(all_blackout_dates[-1]) or date.today()
else:
    min_blackout_date = date.today()
    max_blackout_date = date.today()

# Display and search
resorts["radius"] = resorts.apply(get_radius, axis=1)
resorts["color"] = resorts.apply(get_color, axis=1)
resorts["search_terms"] = resorts.apply(get_search_terms, axis=1)


# Configure Streamlit page
st.set_page_config(page_title="Indy Explorer", layout="wide")
# st.image('img/indy-pass-logo.png', width=200)
st.title("Indy Explorer")

# Sidebar filters
st.sidebar.header("Filter Resorts")

search_query = st.sidebar.text_input(
    label='Search for a resort:',
    help='Enter the name of a resort, city, state/region, or country.',
)

if 'region' in resorts.columns:
    available_regions = sorted({r for r in resorts.region.dropna().unique() if r})
    ordered_regions = [r for r in REGION_ORDER if r in available_regions]
    ordered_regions.extend(sorted(set(available_regions) - set(REGION_ORDER)))
    region_items = [{'label': r, 'value': r} for r in ordered_regions]
    with st.sidebar:
        region_selection = sac.cascader(
            items=region_items,
            label="Region",
            multiple=True,
            search=True,
            clear=True,
        )
    if region_selection:
        if isinstance(region_selection[0], list):
            selected_regions = [path[-1] for path in region_selection]
        else:
            selected_regions = region_selection
    else:
        selected_regions = []
    region_filter = True if not selected_regions else resorts.region.isin(selected_regions)
    region_subset = (
        resorts if not selected_regions else resorts[resorts.region.isin(selected_regions)]
    )
else:
    selected_regions = []
    region_filter = True
    region_subset = resorts
country_options = sorted(region_subset.country.dropna().unique())
country_items = [{'label': c, 'value': c} for c in country_options]
with st.sidebar:
    country_selection = sac.cascader(
        items=country_items,
        label="Country",
        multiple=True,
        search=True,
        clear=True,
    )
if country_selection:
    if isinstance(country_selection[0], list):
        selected_countries = [path[-1] for path in country_selection]
    else:
        selected_countries = country_selection
else:
    selected_countries = country_options
if selected_countries:
    selected_countries = [c for c in selected_countries if c in country_options]
    country_subset = region_subset[region_subset.country.isin(selected_countries)]
else:
    country_subset = region_subset
states_regions = country_subset['state'].dropna().unique()
state_region_options = sorted(states_regions)
state_items = [{'label': s, 'value': s} for s in state_region_options]
with st.sidebar:
    state_selection = sac.cascader(
        items=state_items,
        label="State / Territory",
        multiple=True,
        search=True,
        clear=True,
    )
if state_selection:
    if isinstance(state_selection[0], list):
        selected_states_regions = [path[-1] for path in state_selection]
    else:
        selected_states_regions = state_selection
    state_selection_active = True
else:
    selected_states_regions = []
    state_selection_active = False
if selected_states_regions:
    selected_states_regions = [s for s in selected_states_regions if s in state_region_options]
if not selected_countries:
    selected_countries = country_options
if not selected_states_regions:
    selected_states_regions = state_region_options

min_vertical, max_vertical = st.sidebar.slider(
    ":mountain: Vertical (ft)",
    0,
    int(resorts.vertical.max()),
    (0, int(resorts.vertical.max())),
)
min_trails, max_trails = st.sidebar.slider(
    ":wavy_dash: Number of Trails",
    0,
    int(resorts.num_trails.max()),
    (0, int(resorts.num_trails.max())),
)
min_trail_length, max_trail_length = st.sidebar.slider(
    ":straight_ruler: Trail Length (mi)",
    0,
    int(resorts.trail_length_mi.max()),
    (0, int(resorts.trail_length_mi.max())),
)
min_lifts, max_lifts = st.sidebar.slider(
    ":aerial_tramway: Number of Lifts",
    0,
    int(resorts.num_lifts.max()),
    (0, int(resorts.num_lifts.max())),
)


boolean_map = {'Yes': True, 'No': False}
has_alpine = st.sidebar.segmented_control(
    key='alpine',
    label=':mountain_snow: Alpine',
    options=boolean_map.keys(),
    default=boolean_map.keys(),
    selection_mode="multi",
)
has_cross_country = st.sidebar.segmented_control(
    key='xc',
    label=':turtle: Cross-Country',
    options=boolean_map.keys(),
    default=boolean_map.keys(),
    selection_mode="multi",
)
has_night_skiing = st.sidebar.segmented_control(
    key='night',
    label=':last_quarter_moon_with_face: Nights',
    options=boolean_map.keys(),
    default=boolean_map.keys(),
    selection_mode="multi",
)
has_terrain_parks = st.sidebar.segmented_control(
    key='park',
    label=':snowboarder: Terrain Parks',
    options=boolean_map.keys(),
    default=boolean_map.keys(),
    selection_mode="multi",
)
is_dog_friendly = st.sidebar.segmented_control(
    key='dog',
    label=":dog: Dog Friendly",
    options=boolean_map.keys(),
    default=boolean_map.keys(),
    selection_mode="multi",
)
has_snowshoeing = st.sidebar.segmented_control(
    key='snowshoe',
    label=":hiking_boot: Snowshoeing",
    options=boolean_map.keys(),
    default=boolean_map.keys(),
    selection_mode="multi",
)
is_allied = st.sidebar.segmented_control(
    key='allied',
    label=':handshake: Allied Resorts',
    options=boolean_map.keys(),
    default=boolean_map.keys(),
    selection_mode="multi",
)
reservation_required = st.sidebar.segmented_control(
    key='reservation_required',
    label=':ticket: Reservations Required',
    options=['Yes', 'No'],
    default=['Yes', 'No'],
    selection_mode='multi',
)
reservation_required_selected = 'Yes' in reservation_required
reservation_not_required_selected = 'No' in reservation_required

blackout_presence = st.sidebar.segmented_control(
    key='blackout_presence',
    label=':heavy_multiplication_x: Blackout Dates',
    options=['Yes', 'No'],
    default=['Yes', 'No'],
    selection_mode='multi',
)
selected_presence = [option for option in blackout_presence]
has_blackout_selected = 'Yes' in selected_presence
no_blackout_selected = 'No' in selected_presence

has_peak_rankings_filter = st.sidebar.segmented_control(
    key='has_peak_rankings',
    label=':trophy: Has Peak Rankings Data',
    options=['Yes', 'No'],
    default=['Yes', 'No'],
    selection_mode='multi',
)
has_pr_yes_selected = 'Yes' in has_peak_rankings_filter
has_pr_no_selected = 'No' in has_peak_rankings_filter

with st.sidebar.expander(':bar_chart: Peak Rankings Filters', expanded=False):
    pr_score_min, pr_score_max = st.slider(
        'Total Score',
        0,
        100,
        (0, 100),
        key='pr_total_slider',
    )
    pr_score_filters = {}
    for label, col in [
        ('Snow', 'pr_snow'),
        ('Resiliency', 'pr_resiliency'),
        ('Size', 'pr_size'),
        ('Terrain Diversity', 'pr_terrain_diversity'),
        ('Challenge', 'pr_challenge'),
        ('Lifts', 'pr_lifts'),
        ('Crowd Flow', 'pr_crowd_flow'),
        ('Facilities', 'pr_facilities'),
        ('Navigation', 'pr_navigation'),
        ('Mountain Aesthetic', 'pr_mountain_aesthetic'),
    ]:
        lo, hi = st.slider(label, 0, 10, (0, 10), key=f'{col}_slider')
        pr_score_filters[col] = (lo, hi)

    pr_lodging_options = ['yes', 'limited', 'no']
    pr_lodging_selected = st.multiselect(
        'Lodging', pr_lodging_options, default=pr_lodging_options, key='pr_lodging_filter'
    )
    pr_apres_options = ['extensive', 'moderate', 'limited']
    pr_apres_selected = st.multiselect(
        'Apres Ski', pr_apres_options, default=pr_apres_options, key='pr_apres_filter'
    )
    pr_access_options = ['good', 'acceptable', 'fair', 'poor']
    pr_access_selected = st.multiselect(
        'Access Road', pr_access_options, default=pr_access_options, key='pr_access_filter'
    )
    pr_ability_low_options = ['beginner', 'intermediate', 'advanced']
    pr_ability_low_selected = st.multiselect(
        'Ability Range Low',
        pr_ability_low_options,
        default=pr_ability_low_options,
        key='pr_ability_low_filter',
    )
    pr_ability_high_options = ['beginner', 'intermediate', 'advanced', 'expert', 'extreme']
    pr_ability_high_selected = st.multiselect(
        'Ability Range High',
        pr_ability_high_options,
        default=pr_ability_high_options,
        key='pr_ability_high_filter',
    )

filter_blackout_date = st.sidebar.checkbox(
    'Filter by date range',
    value=False,
    help=(
        'When enabled, only resorts with NO blackout dates in the selected range are '
        'shown. This filters out any resort blacked out on ANY day in the range.'
    ),
)
today = date.today()
default_start = max(min_blackout_date, min(today, max_blackout_date))
blackout_date_range = st.sidebar.date_input(
    'Date range',
    value=(default_start, default_start),
    min_value=min_blackout_date,
    max_value=max_blackout_date,
    disabled=not filter_blackout_date,
    help='Select a start and end date for the blackout filter.',
)

filter_blackout_date_active = (
    filter_blackout_date
    and isinstance(blackout_date_range, tuple)
    and len(blackout_date_range) == 2
)
if filter_blackout_date_active:
    start_date, end_date = blackout_date_range
    range_dates = set(date_range_strings(start_date, end_date))
else:
    range_dates = set()


# Apply filters
filtered_data = resorts[
    (resorts.search_terms.str.contains(search_query.lower()))
    & (region_filter)
    & (resorts.country.isin(selected_countries))
    & (resorts.state.isin(selected_states_regions))
    & (resorts.vertical.between(min_vertical, max_vertical) | resorts.vertical.isnull())
    & (resorts.num_trails.between(min_trails, max_trails) | resorts.num_trails.isnull())
    & (
        resorts.trail_length_mi.between(min_trail_length, max_trail_length)
        | resorts.trail_length_mi.isnull()
    )
    & (resorts.num_lifts.between(min_lifts, max_lifts) | resorts.num_lifts.isnull())
    & (resorts.has_alpine.isin([boolean_map.get(s) for s in has_alpine]))
    & (resorts.has_cross_country.isin([boolean_map.get(s) for s in has_cross_country]))
    & (resorts.has_night_skiing.isin([boolean_map.get(s) for s in has_night_skiing]))
    & (resorts.has_terrain_parks.isin([boolean_map.get(s) for s in has_terrain_parks]))
    & (resorts.is_allied.isin([boolean_map.get(s) for s in is_allied]))
    & (resorts.is_dog_friendly.isin([boolean_map.get(s) for s in is_dog_friendly]))
    & (resorts.has_snowshoeing.isin([boolean_map.get(s) for s in has_snowshoeing]))
    & (
        (has_blackout_selected and no_blackout_selected)
        | (has_blackout_selected and (resorts.blackout_count > 0))
        | (no_blackout_selected and (resorts.blackout_count == 0))
    )
    & (
        (
            reservation_required_selected
            and reservation_not_required_selected
            and resorts.reservation_status.isin(['Required', 'Optional', 'Not Required'])
        )
        | (
            reservation_required_selected
            and resorts.reservation_status.isin(['Required', 'Optional'])
        )
        | (
            reservation_not_required_selected
            and resorts.reservation_status.isin(['Not Required', 'Optional'])
        )
    )
    & (
        (not filter_blackout_date_active)
        | (resorts.blackout_dates_list.apply(lambda dates: range_dates.isdisjoint(dates)))
    )
    & (
        (has_pr_yes_selected and has_pr_no_selected)
        | (has_pr_yes_selected and resorts.has_peak_rankings)
        | (has_pr_no_selected and ~resorts.has_peak_rankings)
    )
    & (
        ~resorts.has_peak_rankings
        | (resorts.pr_total.between(pr_score_min, pr_score_max) | resorts.pr_total.isnull())
    )
    & (
        ~resorts.has_peak_rankings
        | pd.concat(
            [
                resorts[col].between(lo, hi) | resorts[col].isnull()
                for col, (lo, hi) in pr_score_filters.items()
            ],
            axis=1,
        ).all(axis=1)
    )
    & (
        ~resorts.has_peak_rankings
        | resorts.pr_lodging.isin(pr_lodging_selected)
        | resorts.pr_lodging.isnull()
    )
    & (
        ~resorts.has_peak_rankings
        | resorts.pr_apres_ski.isin(pr_apres_selected)
        | resorts.pr_apres_ski.isnull()
    )
    & (
        ~resorts.has_peak_rankings
        | resorts.pr_access_road.isin(pr_access_selected)
        | resorts.pr_access_road.isnull()
    )
    & (
        ~resorts.has_peak_rankings
        | resorts.pr_ability_low.isin(pr_ability_low_selected)
        | resorts.pr_ability_low.isnull()
    )
    & (
        ~resorts.has_peak_rankings
        | resorts.pr_ability_high.isin(pr_ability_high_selected)
        | resorts.pr_ability_high.isnull()
    )
].sort_values('radius', ascending=False)

##### Main Page Content #####
# Prep resorts table
col_names_map = {
    'name': 'Resort',
    'location_name': 'Location Name',
    'city': 'City',
    'region': 'Region',
    'state': 'State / Territory',
    'country': 'Country',
    'latitude': 'Latitude',
    'longitude': 'Longitude',
    'acres': 'Area (acres)',
    'vertical': 'Vertical (ft)',
    'vertical_meters': 'Vertical (m)',
    'has_alpine': 'Alpine',
    'has_cross_country': 'Cross-Country',
    'is_allied': 'Allied',
    'num_trails': 'Trails',
    'trail_length_mi': 'Trail Length (mi)',
    'trail_length_km': 'Trail Length (km)',
    'num_lifts': 'Lifts',
    'has_night_skiing': 'Nights',
    'has_terrain_parks': 'Terrain Parks',
    'is_dog_friendly': 'Dog Friendly',
    'has_snowshoeing': 'Snowshoeing',
    'radius': 'Radius',
    'color': 'Color',
    'indy_page': 'Indy Page',
    'website': 'Website',
    'reservation_status': 'Reservation Status',
    'reservation_url': 'Reservation Page',
    'blackout_dates_display': 'Blackout Dates',
    'pr_total': 'Peak Score',
    'pr_overall_rank': 'Peak Rank',
    'pr_regional_rank': 'Peak Regional Rank',
    'pr_region': 'Peak Region',
    'pr_snow': 'PR Snow',
    'pr_resiliency': 'PR Resiliency',
    'pr_size': 'PR Size',
    'pr_terrain_diversity': 'PR Terrain Diversity',
    'pr_challenge': 'PR Challenge',
    'pr_lifts': 'PR Lifts',
    'pr_crowd_flow': 'PR Crowd Flow',
    'pr_facilities': 'PR Facilities',
    'pr_navigation': 'PR Navigation',
    'pr_mountain_aesthetic': 'PR Mountain Aesthetic',
    'pr_lodging': 'PR Lodging',
    'pr_apres_ski': 'PR Apres Ski',
    'pr_access_road': 'PR Access Road',
    'pr_ability_low': 'PR Ability Low',
    'pr_ability_high': 'PR Ability High',
    'pr_nearest_cities': 'PR Nearest Cities',
    'pr_pass_affiliation': 'PR Pass Affiliation',
}
display_cols = [
    'Resort',
    'City',
    'State / Territory',
    'Country',
    'Region',
    'Latitude',
    'Longitude',
    'Area (acres)',
    'Vertical (ft)',
    'Vertical (m)',
    'Alpine',
    'Cross-Country',
    'Trails',
    'Trail Length (mi)',
    'Trail Length (km)',
    'Lifts',
    'Nights',
    'Terrain Parks',
    'Dog Friendly',
    'Snowshoeing',
    'Allied',
    'Peak Score',
    'Peak Rank',
    'Peak Regional Rank',
    'Peak Region',
    'PR Snow',
    'PR Resiliency',
    'PR Size',
    'PR Terrain Diversity',
    'PR Challenge',
    'PR Lifts',
    'PR Crowd Flow',
    'PR Facilities',
    'PR Navigation',
    'PR Mountain Aesthetic',
    'PR Lodging',
    'PR Apres Ski',
    'PR Access Road',
    'PR Ability Low',
    'PR Ability High',
    'PR Nearest Cities',
    'PR Pass Affiliation',
    'Blackout Dates',
    'Reservation Status',
    'Reservation Page',
    'Indy Page',
    'Website',
]
if 'region' not in resorts.columns:
    display_cols = [col for col in display_cols if col != 'Region']
display_df = filtered_data.rename(columns=col_names_map)[display_cols].sort_values('Resort')

st.markdown('## Resorts')
st.markdown(f'Found {len(display_df)} {'resort' if len(display_df) == 1 else 'resorts'}...')


# PyDeck Map
layer = pdk.Layer(
    "ScatterplotLayer",
    filtered_data,
    pickable=True,
    auto_highlight=True,
    get_position="[longitude, latitude]",
    get_radius='radius',
    get_fill_color='color',
    highlight_color=[255, 255, 255, 100],
)

tooltip = {
    "html": """
        <b>Resort:</b> {name}<br>
        <b>City:</b> {location_name_tt}<br>
        <b>Area:</b> {acres_tt}<br>
        <b>Vertical:</b> {vertical_tt}<br>
        <b>Trails:</b> {num_trails_tt}<br>
        <b>Lifts:</b> {num_lifts_tt}<br>
        <b>Alpine:</b> {has_alpine_display}<br>
        <b>Cross-Country:</b> {has_cross_country_display}<br>
        <b>Nights:</b> {has_night_skiing_display}<br>
        <b>Terrain Park:</b> {has_terrain_parks_display}<br>
        <b>Dog Friendly:</b> {is_dog_friendly_display}<br>
        <b>Indy Allied:</b> {is_allied_display}<br>
        <b>Reservations:</b> {reservation_status}<br>
        <b>Has Blackout Dates:</b> {blackout_has_display}<br>
        <b>Peak Ranking:</b> {pr_total_tt}<br>
        <!-- <b>Indy Resort Page:</b> {indy_page}<br> -->
        <!-- <b>Website:</b> {website}<br> -->
    """,
    "style": {
        "backgroundColor": "white",
        "color": "black",
        "border": "2px solid black",
        "padding": "10px",
        "borderRadius": "8px",
    },
}

# Create the Pydeck map view with initial zoom centered on the US
if 'map_view_state' not in st.session_state:
    st.session_state.map_view_state = pdk.ViewState(latitude=44, longitude=-95, zoom=3, pitch=0)
if 'map_view_region' not in st.session_state:
    st.session_state.map_view_region = None
if 'map_view_country' not in st.session_state:
    st.session_state.map_view_country = None
if 'map_view_state_region' not in st.session_state:
    st.session_state.map_view_state_region = None

region_selection = tuple(sorted(selected_regions))
country_selection = tuple(sorted(selected_countries))
state_selection = tuple(sorted(selected_states_regions))
region_changed = region_selection != st.session_state.map_view_region
country_changed = country_selection != st.session_state.map_view_country
state_changed = state_selection != st.session_state.map_view_state_region
view_changed = region_changed or country_changed or state_changed
if view_changed:
    view_subset = resorts
    if ('region' in resorts.columns) and selected_regions:
        view_subset = view_subset[view_subset.region.isin(selected_regions)]
    if selected_countries:
        view_subset = view_subset[view_subset.country.isin(selected_countries)]
    if selected_states_regions:
        view_subset = view_subset[view_subset.state.isin(selected_states_regions)]
    if view_subset.empty:
        view_state = pdk.ViewState(latitude=44, longitude=-95, zoom=3, pitch=0)
    else:
        view_state = pdk.data_utils.compute_view(view_subset[['longitude', 'latitude']])
        if view_state.zoom > MAX_AUTO_ZOOM:
            view_state.zoom = MAX_AUTO_ZOOM
        if len(view_subset) == 1:
            state_zoom = (
                map_config.STATE_ZOOM.get(selected_states_regions[0])
                if state_selection_active and len(selected_states_regions) == 1
                else None
            )
            if state_zoom is not None:
                view_state.zoom = state_zoom
            elif len(selected_countries) == 1:
                view_state.zoom = map_config.COUNTRY_ZOOM.get(
                    selected_countries[0], view_state.zoom
                )
        if (
            len(selected_regions) == 1
            and len(selected_countries) == len(country_options)
            and len(selected_states_regions) == len(state_region_options)
        ):
            view_state.zoom = REGION_ZOOM.get(selected_regions[0], view_state.zoom)
        view_state.pitch = 0
    st.session_state.map_view_state = view_state
    st.session_state.map_view_region = region_selection
    st.session_state.map_view_country = country_selection
    st.session_state.map_view_state_region = state_selection

view_state = st.session_state.map_view_state


# Render the map
deck = pdk.Deck(
    layers=layer,
    initial_view_state=view_state,
    tooltip=tooltip,
    api_keys={"mapbox": MAPBOX_TOKEN},
    map_style="mapbox://styles/mapbox/light-v11",
)

# Map legend overlay
st.markdown(
    f"""
    <style>
        .map-legend-wrap {{
            position: relative;
            height: 0;
            --map-height: {MAP_HEIGHT}px;
        }}
        .map-legend {{
            position: absolute;
            top: calc(-1 * var(--map-height) + 16px);
            left: 16px;
            z-index: 2;
            background: rgba(255, 255, 255, 0.92);
            padding: 10px 12px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
            pointer-events: none;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 6px;
        }}
        .legend-item:last-child {{
            margin-bottom: 0;
        }}
        .legend-color {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .red {{ background: rgba(197, 42, 28, 200); }}
        .blue {{ background: rgba(0, 10, 200, 160); }}
        .purple {{ background: rgba(128, 0, 128, 160); }}
        .grey {{ background: rgba(30, 30, 30, 160); }}
    </style>
    """,
    unsafe_allow_html=True,
)
st.pydeck_chart(deck, height=MAP_HEIGHT)
st.markdown(
    """
    <div class="map-legend-wrap">
    <div class="map-legend">
        <div class="legend-item">
            <div class="legend-color red"></div>
            Alpine
        </div>
        <div class="legend-item">
            <div class="legend-color blue"></div>
            Cross-Country
        </div>
        <div class="legend-item">
            <div class="legend-color purple"></div>
            Alpine & Cross-Country
        </div>
        <div class="legend-item">
            <div class="legend-color grey"></div>
            Allied Resort
        </div>
    </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('Click the checkbox next to a resort to see more details.')
resorts_table = st.dataframe(
    display_df,
    column_config={
        "Reservation Page": st.column_config.LinkColumn("Reservation Page"),
        "Indy Page": st.column_config.LinkColumn("Indy Page"),
        "Website": st.column_config.LinkColumn("Website"),
    },
    hide_index=True,
    selection_mode='single-row',
    on_select='rerun',
)


if 'selected_resort' not in st.session_state:
    st.session_state.selected_resort = None
if resorts_table.selection:
    st.session_state.selected_resort = resorts_table.selection['rows']
else:
    st.session_state.selected_resort = None


def get_resort_header_markdown(resort: dict) -> str:
    reservation_url = resort.get('reservation_url')
    reservation_status = resort.get('reservation_status')
    if reservation_status == 'Required' and reservation_url:
        reservation_link = f" → [Make a reservation]({reservation_url})"
    elif reservation_status == 'Optional' and reservation_url:
        reservation_link = f" → [Make a reservation]({reservation_url}) _(optional)_"
    else:
        reservation_link = " → No reservation required"
    return f"""
        # {resort['name']}
        **{resort['city']}, {resort['state']} {resort['country']}**  
        [Indy Page]({resort['indy_page']}) | [Resort Website]({resort['website']})  
        {reservation_link}  

        *{resort['description']}*
    """


def get_resort_features_markdown(resort: dict) -> str:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            **Alpine:** {resort['has_alpine_display']}  
            **Cross Country:** {resort['has_cross_country_display']}
        """
        )
    with col2:
        st.markdown(
            f"""
            **Terrain Park:** {resort['has_terrain_parks_display']}  
            **Night Skiing:** {resort['has_night_skiing_display']}
        """
        )
    with col3:
        st.markdown(
            f"""
            **Snow Shoeing:** {resort['has_snowshoeing']}  
            **Dog Friendly:** {resort['is_dog_friendly_display']}
        """
        )
    return ''


def get_resort_size_markdown(resort: dict) -> str:
    acres = int(resort["acres"]) if pd.notnull(resort["acres"]) else '--'
    lifts = int(resort["num_lifts"]) if pd.notnull(resort["num_lifts"]) else '--'
    trails = int(resort["num_trails"]) if pd.notnull(resort["num_trails"]) else '--'
    trail_len_mi = int(resort["trail_length_mi"]) if pd.notnull(resort["trail_length_mi"]) else '--'
    trail_len_km = int(resort["trail_length_km"]) if pd.notnull(resort["trail_length_km"]) else '--'

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            **Acreage:** {acres} acres  
            **Lifts:** {lifts}  
            **Trails:** {trails}  
        """
        )

    with col2:
        st.markdown(
            f"""
            **Trail Length:** {trail_len_mi} miles / {trail_len_km} km 
        """
        )
    return ''


def get_resort_elevation_markdown(resort: dict) -> str:
    base = resort['vertical_base_ft']
    summit = resort['vertical_summit_ft']
    vertical = resort['vertical_elevation_ft']
    if not (pd.notnull(base) and pd.notnull(summit) and pd.notnull(vertical)):
        return ''
    elevation_plot = create_elevation_plot(base, summit, vertical)
    st.pyplot(elevation_plot, width='content')
    return ''


def get_resort_snowfall_markdown(resort: dict) -> str:
    snow_avg = resort['snowfall_average_in']
    snow_max = resort['snowfall_high_in']
    if not (pd.notnull(snow_avg) and pd.notnull(snow_max)):
        return ''
    snowfall_barplot = create_snowfall_barplot(snow_avg, snow_max)
    st.pyplot(snowfall_barplot, width='content')
    return ''


def get_resort_difficulty_markdown(resort: dict) -> str:
    beginner = (
        int(resort["difficulty_beginner"]) if pd.notnull(resort["difficulty_beginner"]) else None
    )
    intermediate = (
        int(resort["difficulty_intermediate"])
        if pd.notnull(resort["difficulty_intermediate"])
        else None
    )
    advanced = (
        int(resort["difficulty_advanced"]) if pd.notnull(resort["difficulty_advanced"]) else None
    )
    if not (beginner and intermediate and advanced):
        return 'Not available'
    difficulty_pie_chart = create_difficulty_chart(beginner, intermediate, advanced)
    st.pyplot(difficulty_pie_chart, width='content')
    return ''


def get_resort_peak_rankings_markdown(resort: dict) -> str:
    """Render Peak Rankings scores and extras in the modal."""
    total = resort.get('pr_total')
    if pd.isnull(total):
        st.markdown('_No Peak Rankings data available for this resort._')
        return ''

    overall_rank = resort.get('pr_overall_rank')
    regional_rank = resort.get('pr_regional_rank')
    region = resort.get('pr_region', '')

    rank_str = f"#{int(overall_rank)}" if pd.notnull(overall_rank) else '--'
    regional_str = (
        f"#{int(regional_rank)} ({region})" if pd.notnull(regional_rank) and region else '--'
    )

    st.markdown(
        f"""
        **Total Score:** {int(total)} | **Overall Rank:** {rank_str} | **Regional Rank:** {regional_str}
    """
    )

    # Category scores in columns
    score_fields = [
        ('Snow', 'pr_snow'),
        ('Resiliency', 'pr_resiliency'),
        ('Size', 'pr_size'),
        ('Terrain Diversity', 'pr_terrain_diversity'),
        ('Challenge', 'pr_challenge'),
        ('Lifts', 'pr_lifts'),
        ('Crowd Flow', 'pr_crowd_flow'),
        ('Facilities', 'pr_facilities'),
        ('Navigation', 'pr_navigation'),
        ('Mountain Aesthetic', 'pr_mountain_aesthetic'),
    ]
    col1, col2 = st.columns(2)
    for i, (label, key) in enumerate(score_fields):
        val = resort.get(key)
        display_val = int(val) if pd.notnull(val) else '--'
        target = col1 if i % 2 == 0 else col2
        target.markdown(f'**{label}:** {display_val}/10')

    # Extras
    extras = []
    for label, key in [
        ('Lodging', 'pr_lodging'),
        ('Apres Ski', 'pr_apres_ski'),
        ('Access Road', 'pr_access_road'),
        ('Nearest Cities', 'pr_nearest_cities'),
        ('Pass Affiliation', 'pr_pass_affiliation'),
    ]:
        val = resort.get(key)
        if pd.notnull(val) and str(val).strip():
            extras.append(f'**{label}:** {val}')

    ability_low = resort.get('pr_ability_low')
    ability_high = resort.get('pr_ability_high')
    if pd.notnull(ability_low) and pd.notnull(ability_high):
        extras.append(f'**Ability Range:** {ability_low} – {ability_high}')

    if extras:
        st.markdown('  \n'.join(extras))

    return ''


@st.dialog('Resort Details', width='large')
def display_resort_modal():
    """
    Show a modal with resort details
    """
    display_index = st.session_state.selected_resort[0]
    resort_name = display_df.iloc[display_index]['Resort']
    resort = resorts[resorts['name'] == resort_name].squeeze().to_dict()

    st.markdown(get_resort_header_markdown(resort))
    with st.expander("## Features", expanded=True, icon='🎿'):
        st.markdown(get_resort_features_markdown(resort))
    with st.expander('Resort Size', expanded=False, icon='🚠'):
        st.markdown(get_resort_size_markdown(resort))
    with st.expander('Elevation', expanded=False, icon='🏔️'):
        st.markdown(get_resort_elevation_markdown(resort))
    with st.expander('Annual Snowfall', expanded=False, icon='❄️'):
        st.markdown(get_resort_snowfall_markdown(resort))
    with st.expander('Difficulty', expanded=False, icon='😰'):
        st.markdown(get_resort_difficulty_markdown(resort))
    with st.expander('Peak Rankings', expanded=False, icon='🏆'):
        st.markdown(get_resort_peak_rankings_markdown(resort))


if st.session_state.selected_resort:
    display_resort_modal()

# Footer
_metadata_path = 'data/pipeline_metadata.json'
if os.path.exists(_metadata_path):
    with open(_metadata_path, 'r', encoding='utf-8') as _f:
        _pipeline_metadata = json.load(_f)
    _last_run_dt = datetime.fromisoformat(_pipeline_metadata['last_run'])
    _last_run_str = _last_run_dt.strftime('%B %-d, %Y')
else:
    _last_run_str = 'unknown'

st.markdown(
    f"""
    Data sourced from [indyskipass.com](https://www.indyskipass.com/our-resorts),
    [peakrankings.com](https://peakrankings.com), and the
    [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding).
    Last updated {_last_run_str}.

    ---
    Help improve this app:
    - [Report a Bug](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=%5BBUG%5D+%3CShort+description%3E)
    - [Suggest a Feature](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.md&title=%5BFEATURE%5D+%3CShort+description%3E)
    - [Kanban Board](https://github.com/users/jonathanstelman/projects/2/views/1)
    """
)

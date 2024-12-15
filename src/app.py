import json

import pandas as pd
import pydeck as pdk
import streamlit as st

with open('data/resorts_data.json', 'r', encoding='utf-8') as json_file:
    resorts = json.load(json_file)
resorts_df = pd.DataFrame(resorts).transpose()

# need to remove locations that don't have location
resorts_df = resorts_df[resorts_df.location.notnull()]
resorts_df['web_page'] = resorts_df['href'].apply(lambda x: 'https://www.indyskipass.com' + x if x else 'n/a')

# Prep data for visualization
def get_color(resort):
    """
    Returns the color that a resort should appear on the map
    """
    if resort['is_allied']:
        return [0, 0, 0, 255]  # White for allied resorts
    if resort['is_alpine_xc']:
        return [255, 165, 0, 160]  # Orange for Cross Country resorts
    return [197, 42, 28, 200]  # Default to Red -- should be alpine?

def get_radius(resort):
    """
    Returns the radius that a resort should appear on the map
    """
    num_trails = resort.num_trails if resort.num_trails else 5
    vertical = resort.vertical if resort.vertical else 300
    num_lifts = resort.num_lifts if resort.num_lifts else 0

    return 2 * (50 * num_trails + 1.5 * vertical + 5 * num_lifts)

resorts_df["radius"] = resorts_df.apply(get_radius, axis=1)
resorts_df["color"] = resorts_df.apply(get_color, axis=1)

tt_bool_map = {False: 'No', True: 'Yes'}
resorts_df['is_alpine_xc_display'] = resorts_df.is_alpine_xc.map(tt_bool_map)
resorts_df['is_open_nights_display'] = resorts_df.is_open_nights.map(tt_bool_map)
resorts_df['has_terrain_parks_display'] = resorts_df.has_terrain_parks.map(tt_bool_map)
resorts_df['is_allied_display'] = resorts_df.is_allied.map(tt_bool_map)


st.set_page_config(page_title="Indy Pass Resorts Map", layout="wide")
st.image('img/indy-pass-logo.png', width=200)
st.title("Indy Pass Resorts Map")

# Filters in Sidebar
st.sidebar.header("Filter Resorts")
min_vertical, max_vertical = st.sidebar.slider(":mountain: Vertical (ft)", 0, resorts_df.vertical.max(), (0, resorts_df.vertical.max()))
min_trails, max_trails = st.sidebar.slider(":wavy_dash: Trails", 0, resorts_df.num_trails.max(), (0, resorts_df.num_trails.max()))
min_lifts, max_lifts = st.sidebar.slider(":aerial_tramway: Lifts", 0, resorts_df.num_lifts.max(), (0, resorts_df.num_lifts.max()))

boolean_map = {'Yes': True, 'No': False}
is_alpine_xc = st.sidebar.segmented_control(key='alpine', label=':evergreen_tree: Alpine / Cross-Country', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_open_nights = st.sidebar.segmented_control(key='night', label=':last_quarter_moon_with_face: Open Nights', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_terrain_parks = st.sidebar.segmented_control(key='park', label=':snowboarder: Terrain Parks', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_allied = st.sidebar.segmented_control(key='allied', label=':handshake: Allied Resorts', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")


filtered_data = resorts_df[
    (resorts_df.vertical.between(min_vertical, max_vertical) | resorts_df.vertical.isnull()) &
    (resorts_df.num_trails.between(min_trails, max_trails) | resorts_df.num_trails.isnull()) &
    (resorts_df.num_lifts.between(min_lifts, max_lifts) | resorts_df.num_lifts.isnull()) &
    (resorts_df.is_alpine_xc.isin([boolean_map.get(s) for s in is_alpine_xc])) &
    (resorts_df.is_open_nights.isin([boolean_map.get(s) for s in is_open_nights])) &
    (resorts_df.has_terrain_parks.isin([boolean_map.get(s) for s in has_terrain_parks])) &
    (resorts_df.is_allied.isin([boolean_map.get(s) for s in is_allied]))
]

# PyDeck Map
layer = pdk.Layer(
    "ScatterplotLayer",
    filtered_data,
    pickable=True,
    auto_highlight=True,
    get_position="[longitude, latitude]",
    get_radius="radius",
    get_fill_color='color'
)


tooltip = {
    "html": """
        <b>Resort:</b> {name}<br>
        <b>City:</b> {city}<br>
        <b>Vertical:</b> {vertical} ft<br>
        <b>Trails:</b> {num_trails}<br>
        <b>Lifts:</b> {num_lifts}<br>
        <b>Alpine / Cross-Counry:</b> {is_alpine_xc_display}<br>
        <b>Nights:</b> {is_open_nights_display}<br>
        <b>Terrain Park:</b> {has_terrain_parks_display}<br>
        <b>Indy Allied:</b> {is_allied_display}<br>
        <!-- <b>Web Page:</b> {web_page}<br> -->
    """,
    "style": {
        "backgroundColor": "white",
        "color": "black",
        "border": "2px solid black",
        "padding": "10px",
        "borderRadius": "8px",
    }
}

# Create the Pydeck map view
map_style = "mapbox://styles/mapbox/light-v11"
view_state = pdk.ViewState(
    latitude=44,
    longitude=-95,
    zoom=3,
    pitch=0
)

# Render the map in Streamlit
st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=map_style
    ),
    use_container_width=True,
    height=800
)

def display_results():

    col_names_map = {
        'name' : 'Resort',
        'city' : 'City',
        'location' : 'Coordinates',
        'latitude' : 'Latitude',
        'longitude' : 'Longitude',
        'vertical' : 'Vertical',
        'is_nordic' : 'Nordic',
        'is_alpine_xc' : 'Alpine / Cross-Country',
        'is_xc_only' : 'Cross-Country Only',
        'is_allied' : 'Allied',
        'num_trails' : 'Trails',
        'num_lifts' : 'Lifts',
        'is_open_nights' : 'Nights',
        'has_terrain_parks' : 'Terrain Parks',
        'radius' : 'Radius',
        'color' : 'Color',
        'web_page': 'Web Page'
    }
    display_cols = [
        'Resort',
        'City',
        'Latitude',
        'Longitude',
        'Vertical',
        'Alpine / Cross-Country',
        'Trails',
        'Lifts',
        'Nights',
        'Terrain Parks',
        'Allied',
        'Web Page'
    ]
    display_df = filtered_data.rename(columns=col_names_map)[display_cols]

    res = 'resort' if len(display_df) == 1 else 'resorts'
    st.markdown(f'Displaying {len(display_df)} {res}...')
    st.dataframe(display_df, hide_index=True)

st.markdown('## Resorts')
display_results()
st.markdown('Data from [indyskipass.com](https://www.indyskipass.com/our-resorts)')

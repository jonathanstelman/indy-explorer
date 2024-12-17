"""
Streamlit app to display Indy Pass resorts in an interactive map and table
"""
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st


def get_color(resort):
    """
    Returns the color that a resort should appear on the map
    """
    if resort['is_allied']:
        return [0, 0, 0, 255]     # White for allied resorts
    if resort['is_alpine_xc']:
        return [255, 165, 0, 160] # Orange for Cross Country resorts
    return [197, 42, 28, 200]     # Default to Red -- should be alpine?

def get_radius(resort):
    """
    Returns the radius that a resort should appear on the map
    """
    num_trails = resort.num_trails if resort.num_trails else 5
    vertical = resort.vertical if resort.vertical else 300
    num_lifts = resort.num_lifts if resort.num_lifts else 0

    return 2 * (50 * num_trails + 1.5 * vertical + 5 * num_lifts)

def get_search_terms(resort):
    """
    Concatenates relevant fields for search
    """
    search_fields = [resort['name'], resort['city'], resort['state'], resort['country']]
    search_terms = [f for f in search_fields if isinstance(f, str)]
    return ' '.join(search_terms).lower()

resorts = pd.read_csv('data/resorts.csv')

# Drop locations that don't have location
resorts = resorts[resorts.latitude.notnull()]


# Display and search
resorts["radius"] = resorts.apply(get_radius, axis=1)
resorts["color"] = resorts.apply(get_color, axis=1)
resorts['search_terms'] = resorts.apply(get_search_terms, axis=1)


# Configure Streamlit page
st.set_page_config(page_title="Indy Pass Resorts Map", layout="wide")
st.image('img/indy-pass-logo.png', width=200)
st.title("Indy Pass Resorts Map")

# Filters in Sidebar
st.sidebar.header("Filter Resorts")

search_query = st.sidebar.text_input('Search for a resort:')
min_vertical, max_vertical = st.sidebar.slider(":mountain: Vertical (ft)", 0, int(resorts.vertical.max()), (0, int(resorts.vertical.max())))
min_trails, max_trails = st.sidebar.slider(":wavy_dash: Trails", 0, int(resorts.num_trails.max()), (0, int(resorts.num_trails.max())))
min_lifts, max_lifts = st.sidebar.slider(":aerial_tramway: Lifts", 0, int(resorts.num_lifts.max()), (0, int(resorts.num_lifts.max())))

boolean_map = {'Yes': True, 'No': False}
is_alpine_xc = st.sidebar.segmented_control(key='alpine', label=':evergreen_tree: Alpine / Cross-Country', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_open_nights = st.sidebar.segmented_control(key='night', label=':last_quarter_moon_with_face: Open Nights', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_terrain_parks = st.sidebar.segmented_control(key='park', label=':snowboarder: Terrain Parks', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_allied = st.sidebar.segmented_control(key='allied', label=':handshake: Allied Resorts', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")


filtered_data = resorts[
    (resorts.search_terms.str.contains(search_query.lower())) &
    (resorts.vertical.between(min_vertical, max_vertical) | resorts.vertical.isnull()) &
    (resorts.num_trails.between(min_trails, max_trails) | resorts.num_trails.isnull()) &
    (resorts.num_lifts.between(min_lifts, max_lifts) | resorts.num_lifts.isnull()) &
    (resorts.is_alpine_xc.isin([boolean_map.get(s) for s in is_alpine_xc])) &
    (resorts.is_open_nights.isin([boolean_map.get(s) for s in is_open_nights])) &
    (resorts.has_terrain_parks.isin([boolean_map.get(s) for s in has_terrain_parks])) &
    (resorts.is_allied.isin([boolean_map.get(s) for s in is_allied]))
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
        <b>City:</b> {location_name}<br>
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
        map_style="mapbox://styles/mapbox/light-v11"
    ),
    use_container_width=True,
    height=800
)

def display_resorts_table():
    """
    Clean resorts dataframe for cleaner output
    """

    col_names_map = {
        'name' : 'Resort',
        'location_name': 'Location Name',
        'city' : 'City',
        'state': 'State',
        'country': 'Country',
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
        'State',
        'Country',
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

    st.markdown('## Resorts')
    st.markdown(f'Displaying {len(display_df)} {'resort' if len(display_df) == 1 else 'resorts'}...')
    st.dataframe(
        display_df,
        column_config={"Web Page": st.column_config.LinkColumn()},
        hide_index=True
    )

def display_footer():
    """
    Display the footer text
    """
    st.markdown(
    """
    To suggest features, report bugs, or contribute, see 
    [Indy Explorer Project](https://github.com/users/jonathanstelman/projects/2/views/1) on GitHub.  
    Data from [indyskipass.com](https://www.indyskipass.com/our-resorts), as of December 14, 2024.  
    """
    )

display_resorts_table()
display_footer()

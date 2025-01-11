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
    if resort.is_allied:
        return [30, 30, 30, 160]     # Grey for allied resorts
    if resort.is_alpine_xc: # Alpine AND Cross Country
        return [128, 0, 128, 160] # Purple for Alpine AND Cross Country resorts
    if resort.is_nordic or resort.is_xc_only:
        return [0, 10, 200, 160]     # Blue
    return [197, 42, 28, 200]     # Default to Red -- should be alpine?


def get_radius(resort):
    """
    Returns the radius that a resort should display on the map
    """
    if resort.is_nordic or resort.is_xc_only or resort.is_alpine_xc:
        return 3000

    if not resort.acres:
        # use this weird formula I made up to set display radius based on other data
        num_trails = resort.num_trails if resort.num_trails else 5
        vertical = resort.vertical if resort.vertical else 300
        num_lifts = resort.num_lifts if resort.num_lifts else 0
        radius =  2 * (50 * num_trails + 1.5 * vertical + 5 * num_lifts)
    else:
        radius = resort.acres * 30

    # set min and max radius
    return min(50_000, max(3000, radius))


def get_search_terms(resort):
    """
    Concatenates relevant fields for search
    """
    search_fields = [resort['name'], resort['city'], resort['state'], resort['country']]
    search_terms = [f for f in search_fields if isinstance(f, str)]
    return ' '.join(search_terms).lower()

def feet_to_meters(feet):
    """
    Convert feet to meters, safely handling missing values
    """
    return int(feet * 0.30479999) if pd.notnull(feet) else np.nan


# Load resort data
resorts = pd.read_csv('data/resorts.csv')

# Drop resorts that don't have coordinate data (cannot be mapped)
resorts = resorts[resorts.latitude.notnull()]

# Display and search
resorts["radius"] = resorts.apply(get_radius, axis=1)
resorts["color"] = resorts.apply(get_color, axis=1)
resorts["search_terms"] = resorts.apply(get_search_terms, axis=1)

# Units
resorts["vertical_meters"] = resorts.vertical.apply(feet_to_meters)

# Configure Streamlit page
st.set_page_config(page_title="Indy Pass Resorts Map", layout="wide")
# st.image('img/indy-pass-logo.png', width=200)
st.title("Indy Pass Resorts Map")

# Filters in Sidebar
st.sidebar.header("Filter Resorts")

search_query = st.sidebar.text_input(
    label='Search for a resort:',
    help='Enter the name of a resort, city, state/region, or country.'
)
country = st.sidebar.selectbox(
    'Country',
    options=['All'] + sorted(resorts.country.dropna().unique()),
)
selected_countries = resorts.country.unique() if country == 'All' else [country]
min_vertical, max_vertical = st.sidebar.slider(":mountain: Vertical (ft)", 0, int(resorts.vertical.max()), (0, int(resorts.vertical.max())))
min_trails, max_trails = st.sidebar.slider(":wavy_dash: Number of Trails", 0, int(resorts.num_trails.max()), (0, int(resorts.num_trails.max())))
# min_trail_length, max_trail_length = st.sidebar.slider(":straight_ruler: Trail Length (mi)", 0, int(resorts.trail_length_mi.max()), (0, int(resorts.trail_length_mi.max())))
min_lifts, max_lifts = st.sidebar.slider(":aerial_tramway: Number of Lifts", 0, int(resorts.num_lifts.max()), (0, int(resorts.num_lifts.max())))

boolean_map = {'Yes': True, 'No': False}
is_alpine_xc = st.sidebar.segmented_control(key='alpine', label=':evergreen_tree: Alpine / Cross-Country', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_night_skiing = st.sidebar.segmented_control(key='night', label=':last_quarter_moon_with_face: Open Nights', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_terrain_parks = st.sidebar.segmented_control(key='park', label=':snowboarder: Terrain Parks', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_dog_friendly = st.sidebar.segmented_control(key='dog', label=":dog: Dog Friendly", options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_snowshoeing = st.sidebar.segmented_control(key='snowshoe', label=":hiking_boot: Snowshoeing", options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_allied = st.sidebar.segmented_control(key='allied', label=':handshake: Allied Resorts', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")



filtered_data = resorts[
    (resorts.search_terms.str.contains(search_query.lower())) &
    (resorts.country.isin(selected_countries)) &
    (resorts.vertical.between(min_vertical, max_vertical) | resorts.vertical.isnull()) &
    (resorts.num_trails.between(min_trails, max_trails) | resorts.num_trails.isnull()) &
    # (resorts.trail_length_mi.between(min_trail_length, max_trail_length) | resorts.trail_length_mi.isnull()) &
    (resorts.num_lifts.between(min_lifts, max_lifts) | resorts.num_lifts.isnull()) &
    (resorts.is_alpine_xc.isin([boolean_map.get(s) for s in is_alpine_xc])) &
    (resorts.has_night_skiing.isin([boolean_map.get(s) for s in has_night_skiing])) &
    (resorts.has_terrain_parks.isin([boolean_map.get(s) for s in has_terrain_parks])) &
    (resorts.is_allied.isin([boolean_map.get(s) for s in is_allied])) &
    (resorts.is_dog_friendly.isin([boolean_map.get(s) for s in is_dog_friendly])) &
    (resorts.has_snowshoeing.isin([boolean_map.get(s) for s in has_snowshoeing]))
]


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
        <b>City:</b> {location_name}<br>
        <b>Area:</b> {acres} acres<br>
        <b>Vertical:</b> {vertical} ft / {vertical_meters} m<br>
        <b>Trails:</b> {num_trails}<br>
        <b>Lifts:</b> {num_lifts}<br>
        <b>Alpine & Cross-Country:</b> {is_alpine_xc_display}<br>
        <b>Nights:</b> {night_skiing_display}<br>
        <b>Terrain Park:</b> {has_terrain_parks_display}<br>
        <b>Dog Friendly:</b> {is_dog_friendly_display}<br>
        <b>Indy Allied:</b> {is_allied_display}<br>
        <!-- <b>Indy Resort Page:</b> {indy_page}<br> -->
        <!-- <b>Website:</b> {website}<br> -->
    """,
    "style": {
        "backgroundColor": "white",
        "color": "black",
        "border": "2px solid black",
        "padding": "10px",
        "borderRadius": "8px",
    }
}

# Create the Pydeck map view with initial zoom
view_state = pdk.ViewState(
    latitude=44,
    longitude=-95,
    zoom=3,
    pitch=0
)

# Render the map
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

# Add a legend
st.markdown(
    """
    <style>
        .legend {
            position: relative;
            background: white;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            box-shadow: 0 2px 3px rgba(0, 0, 0, 0.2);
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-color {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .red { background: rgba(197, 42, 28, 200); }
        .blue { background: rgba(0, 10, 200, 160); }
        .purple { background: rgba(128, 0, 128, 160); }
        .grey { background: rgba(30, 30, 30, 160); }
    </style>
    <div class="legend">
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
    """,
    unsafe_allow_html=True,
)



def display_resorts_table():
    """
    Clean resorts dataframe for cleaner output
    """

    col_names_map = {
        'name' : 'Resort',
        'location_name': 'Location Name',
        'city' : 'City',
        'state': 'State / Region',
        'country': 'Country',
        'latitude' : 'Latitude',
        'longitude' : 'Longitude',
        'acres': 'Area (acres)',
        'vertical' : 'Vertical (ft)',
        'vertical_meters' : 'Vertical (m)',
        'is_nordic' : 'Nordic',
        'is_cross_country' : 'Cross-Country',
        'is_alpine_xc' : 'Alpine & Cross-Country',
        'is_xc_only' : 'Cross-Country Only',
        'is_allied' : 'Allied',
        'num_trails' : 'Num. Trails',
        'trail_length_mi' : 'Trail Length (mi)',
        'trail_length_km' : 'Trail Length (km)',
        'num_lifts' : 'Lifts',
        'has_night_skiing' : 'Nights',
        'has_terrain_parks' : 'Terrain Parks',
        'is_dog_friendly' : 'Dog Friendly',
        'has_snowshoeing' : 'Snowshoeing',
        'radius' : 'Radius',
        'color' : 'Color',
        'indy_page': 'Indy Page',
        'website' : 'Website',
    }
    display_cols = [
        'Resort',
        'City',
        'State / Region',
        'Country',
        'Latitude',
        'Longitude',
        'Area (acres)',
        'Vertical (ft)',
        'Vertical (m)',
        'Nordic',
        'Cross-Country',
        'Alpine & Cross-Country',
        'Num. Trails',
        'Trail Length (mi)',
        'Trail Length (km)',
        'Lifts',
        'Nights',
        'Terrain Parks',
        'Dog Friendly',
        'Snowshoeing',
        'Allied',
        'Indy Page',
        'Website',
    ]
    display_df = filtered_data.rename(columns=col_names_map)[display_cols].sort_values('Resort')

    st.markdown('## Resorts')
    st.markdown(f'Displaying {len(display_df)} {'resort' if len(display_df) == 1 else 'resorts'}...')
    st.dataframe(
        display_df,
        column_config={"Web Page": st.column_config.LinkColumn()},
        hide_index=True,
        # on_select='rerun',
        # selection_mode='multi-row'
    )

def display_footer():
    """
    Display the footer text
    """
    st.markdown(
        """
        Data from [indyskipass.com](https://www.indyskipass.com/our-resorts) as of January 5, 2025.  
        
        ---
        Help improve this app:
        - [Report a Bug](https://github.com/jonathanstelman/indy-explorer/issues/new?template=bug_report.md)
        - [Suggest a Feature](https://github.com/jonathanstelman/indy-explorer/issues/new?template=feature_request.md)
        - [Kanban Board](https://github.com/users/jonathanstelman/projects/2/views/1)  
        """
    )

display_resorts_table()
display_footer()

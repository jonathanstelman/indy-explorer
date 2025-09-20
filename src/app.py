"""
Streamlit app to display Indy Pass resorts in an interactive map and table
"""
import matplotlib.pyplot as plt
import pandas as pd
import pydeck as pdk
import streamlit as st

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
        radius =  2 * (50 * num_trails + 1.5 * vertical + 5 * num_lifts)
        
    # set min and max radius
    return min(MAX_POINT_RADIUS, max(MIN_POINT_RADIUS, radius))


def get_search_terms(resort):
    """
    Concatenates relevant fields for search
    """
    search_fields = [resort['name'], resort['city'], resort['state'], resort['country']]
    search_terms = [f for f in search_fields if isinstance(f, str)]
    return ' '.join(search_terms).lower()

def rgba_to_hex(rgba):
    r, g, b, a = rgba
    return f'#{r:02x}{g:02x}{b:02x}{a:02x}'

def create_elevation_plot(base, summit, vertical):
    """Make a plot to display the resort elevation
    """
    SEA_LEVEL = 0
    BASE_HEIGHT = 0.6
    SUMMIT_HEIGHT = 3
    VERTICAL_HEIGHT = SUMMIT_HEIGHT - BASE_HEIGHT

    mountain_coords = [
        [0, BASE_HEIGHT],
        [2, BASE_HEIGHT + VERTICAL_HEIGHT * 0.8],
        [3, BASE_HEIGHT + VERTICAL_HEIGHT * 0.6],
        [4, SUMMIT_HEIGHT],
        [6, BASE_HEIGHT]
    ]
    fig, ax = plt.subplots()
    mountain = plt.Polygon(mountain_coords, closed=True, edgecolor='black', facecolor=rgba_to_hex(COLORS['pale-grey']))
    ax.add_patch(mountain)

    # Sea-level indicator
    ax.plot((-1, 8), (SEA_LEVEL, SEA_LEVEL), marker=None, linestyle='-', color='lightblue')

    # text / annotations
    ax.text(-0.5, BASE_HEIGHT, f'{int(base)} ft', verticalalignment='baseline', horizontalalignment='right', color=rgba_to_hex(COLORS['grey']), fontsize='x-small')
    ax.text(-0.5, SUMMIT_HEIGHT, f'{int(summit)} ft', verticalalignment='top', horizontalalignment='right', color='grey', fontsize='x-small')
    ax.annotate('', xy=(0, 3), xytext=(0, BASE_HEIGHT), arrowprops=dict(arrowstyle='<->', color=rgba_to_hex(COLORS['red'])))
    ax.text(-0.3, VERTICAL_HEIGHT/2+BASE_HEIGHT, f'{int(vertical)} ft', verticalalignment='center', horizontalalignment='right', color=rgba_to_hex(COLORS['red']), fontsize='x-small')

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
        f'Advanced - {advanced}%'
    ]
    colors = [rgba_to_hex(c) for c in [COLORS['pale-blue'], COLORS['blue'], COLORS['purple']]]

    fig, ax = plt.subplots(figsize=(1,1))
    ax.pie(
        levels, radius=7, colors=colors,
        wedgeprops={"linewidth": 2, "edgecolor": "white"},
        labels=labels, labeldistance=0.3
    )

    ax.axis('off')
    return fig


def create_snowfall_barplot(snowfall_avg, snowfall_max):
    """
    Create a barplot to display the average and maximum annual snowfall.
    """
    fig, ax = plt.subplots()
    categories = ['Average Snowfall', 'Maximum Snowfall']
    values = [snowfall_avg, snowfall_max]
    colors = [rgba_to_hex(COLORS['pale-blue']), rgba_to_hex(COLORS['pale-blue'])]

    ax.bar(categories, values, color=colors)
    # ax.set_ylabel('Snowfall (inches)')

    for i, v in enumerate(values):
        ax.text(i, v + 5, f'{int(v)} in', ha='center', color='black')

    # Hide the border and horizontal ticks
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='x', which='both', bottom=False, top=False)
    ax.tick_params(axis='y', which='both', left=True, right=False)

    return fig


# Load resort data
resorts = pd.read_csv('data/resorts.csv', index_col='index', na_values=[''], keep_default_na=False)

# Drop resorts that don't have coordinate data (cannot be mapped)
resorts = resorts[resorts.latitude.notnull()]

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
    help='Enter the name of a resort, city, state/region, or country.'
)
country = st.sidebar.selectbox('Country', options=['All'] + sorted(resorts.country.dropna().unique()))
selected_countries = resorts.country.unique() if country == 'All' else [country]
states_regions = resorts['state'].dropna().unique() if country == 'All' else resorts[resorts.country == country]['state'].dropna().unique()
state_region = st.sidebar.selectbox('State / Region', options=['All'] + sorted(states_regions))
selected_states_regions = resorts.state.unique() if state_region == 'All' else [state_region]

min_vertical, max_vertical = st.sidebar.slider(":mountain: Vertical (ft)", 0, int(resorts.vertical.max()), (0, int(resorts.vertical.max())))
min_trails, max_trails = st.sidebar.slider(":wavy_dash: Number of Trails", 0, int(resorts.num_trails.max()), (0, int(resorts.num_trails.max())))
min_trail_length, max_trail_length = st.sidebar.slider(":straight_ruler: Trail Length (mi)", 0, int(resorts.trail_length_mi.max()), (0, int(resorts.trail_length_mi.max())))
min_lifts, max_lifts = st.sidebar.slider(":aerial_tramway: Number of Lifts", 0, int(resorts.num_lifts.max()), (0, int(resorts.num_lifts.max())))


boolean_map = {'Yes': True, 'No': False}
has_alpine = st.sidebar.segmented_control(key='alpine', label=':mountain_snow: Alpine', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_cross_country = st.sidebar.segmented_control(key='xc', label=':turtle: Cross-Country', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_night_skiing = st.sidebar.segmented_control(key='night', label=':last_quarter_moon_with_face: Nights', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_terrain_parks = st.sidebar.segmented_control(key='park', label=':snowboarder: Terrain Parks', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_dog_friendly = st.sidebar.segmented_control(key='dog', label=":dog: Dog Friendly", options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
has_snowshoeing = st.sidebar.segmented_control(key='snowshoe', label=":hiking_boot: Snowshoeing", options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")
is_allied = st.sidebar.segmented_control(key='allied', label=':handshake: Allied Resorts', options=boolean_map.keys(), default=boolean_map.keys(), selection_mode="multi")

filtered_data = resorts[
    (resorts.search_terms.str.contains(search_query.lower())) &
    (resorts.country.isin(selected_countries)) &
    (resorts.state.isin(selected_states_regions)) &
    (resorts.vertical.between(min_vertical, max_vertical) | resorts.vertical.isnull()) &
    (resorts.num_trails.between(min_trails, max_trails) | resorts.num_trails.isnull()) &
    (resorts.trail_length_mi.between(min_trail_length, max_trail_length) | resorts.trail_length_mi.isnull()) &
    (resorts.num_lifts.between(min_lifts, max_lifts) | resorts.num_lifts.isnull()) &
    (resorts.has_alpine.isin([boolean_map.get(s) for s in has_alpine])) &
    (resorts.has_cross_country.isin([boolean_map.get(s) for s in has_cross_country])) &
    (resorts.has_night_skiing.isin([boolean_map.get(s) for s in has_night_skiing])) &
    (resorts.has_terrain_parks.isin([boolean_map.get(s) for s in has_terrain_parks])) &
    (resorts.is_allied.isin([boolean_map.get(s) for s in is_allied])) &
    (resorts.is_dog_friendly.isin([boolean_map.get(s) for s in is_dog_friendly])) &
    (resorts.has_snowshoeing.isin([boolean_map.get(s) for s in has_snowshoeing]))
].sort_values('radius', ascending=False)


# PyDeck Map
layer = pdk.Layer(
    "ScatterplotLayer",
    filtered_data,
    pickable=True,
    auto_highlight=True,
    get_position="[longitude, latitude]",
    get_radius='radius',
    get_fill_color='color',
    highlight_color=[255, 255, 255, 100]
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

# Create the Pydeck map view with initial zoom centered on the US
view_state = pdk.ViewState(
    latitude=44,
    longitude=-95,
    zoom=3,
    pitch=0
)


# Render the map
deck = pdk.Deck(
    layers=layer,
    initial_view_state=view_state,
    tooltip=tooltip,
    api_keys={"mapbox": MAPBOX_TOKEN},
    map_style="mapbox://styles/mapbox/light-v11",
)
st.pydeck_chart(deck, height=800)

# Add a legend
# TODO: parameterize the markdown to map colors and other values from constants
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

# Display resorts table
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
    'has_alpine' : 'Alpine',
    'has_cross_country' : 'Cross-Country',
    'is_allied' : 'Allied',
    'num_trails' : 'Trails',
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
    'Indy Page',
    'Website',
]
display_df = filtered_data.rename(columns=col_names_map)[display_cols].sort_values('Resort')


st.markdown('## Resorts')
st.markdown(f'Found {len(display_df)} {'resort' if len(display_df) == 1 else 'resorts'}...')
st.markdown('Click the checkbox next to a resort to see more details.')
resorts_table = st.dataframe(
    display_df,
    column_config={
        "Indy Page": st.column_config.LinkColumn("Indy Page"),
        "Website": st.column_config.LinkColumn("Website"),
    },
    hide_index=True,
    selection_mode='single-row',
    on_select='rerun'
)


if 'selected_resort' not in st.session_state:
    st.session_state.selected_resort = None
if resorts_table.selection:
    st.session_state.selected_resort = resorts_table.selection['rows']
else:
    st.session_state.selected_resort = None


def get_resort_header_markdown(resort: dict) -> str:
    return f"""
        # {resort['name']}
        **{resort['city']}, {resort['state']} {resort['country']}**  
        [Indy Page]({resort['indy_page']}) | [Resort Website]({resort['website']})  

        *{resort['description']}*
    """

def get_resort_features_markdown(resort: dict) -> str:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            **Alpine:** {resort['has_alpine_display']}  
            **Cross Country:** {resort['has_cross_country_display']}
        """)
    with col2:
        st.markdown(f"""
            **Terrain Park:** {resort['has_terrain_parks_display']}  
            **Night Skiing:** {resort['has_night_skiing_display']}
        """)
    with col3:
        st.markdown(f"""
            **Snow Shoeing:** {resort['has_snowshoeing']}  
            **Dog Friendly:** {resort['is_dog_friendly_display']}
        """)
    return ''

def get_resort_size_markdown(resort: dict) -> str:
    acres = int(resort["acres"]) if pd.notnull(resort["acres"]) else '--'
    lifts = int(resort["num_lifts"]) if pd.notnull(resort["num_lifts"]) else '--'
    trails = int(resort["num_trails"]) if pd.notnull(resort["num_trails"]) else '--'
    trail_len_mi = int(resort["trail_length_mi"]) if pd.notnull(resort["trail_length_mi"]) else '--'
    trail_len_km = int(resort["trail_length_km"]) if pd.notnull(resort["trail_length_km"]) else '--'

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            **Acreage:** {acres} acres  
            **Lifts:** {lifts}  
            **Trails:** {trails}  
        """)
    
    with col2:
        st.markdown(f"""
            **Trail Length:** {trail_len_mi} miles / {trail_len_km} km 
        """)
    return ''

def get_resort_elevation_markdown(resort: dict) -> str:
    base = resort['vertical_base_ft']
    summit = resort['vertical_summit_ft']
    vertical = resort['vertical_elevation_ft']
    if not (pd.notnull(base) and pd.notnull(summit) and pd.notnull(vertical)):
        return ''
    elevation_plot = create_elevation_plot(base, summit, vertical)
    st.pyplot(elevation_plot)
    return ''

def get_resort_snowfall_markdown(resort: dict) -> str:
    snow_avg = resort['snowfall_average_in']
    snow_max = resort['snowfall_high_in']
    if not(pd.notnull(snow_avg) and pd.notnull(snow_max)):
        return ''
    snowfall_barplot = create_snowfall_barplot(snow_avg, snow_max)
    st.pyplot(snowfall_barplot)

def get_resort_difficulty_markdown(resort: dict) -> str:
    beginner = int(resort["difficulty_beginner"]) if pd.notnull(resort["difficulty_beginner"]) else None
    intermediate = int(resort["difficulty_intermediate"]) if pd.notnull(resort["difficulty_intermediate"]) else None
    advanced = int(resort["difficulty_advanced"]) if pd.notnull(resort["difficulty_advanced"]) else None
    if not (beginner and intermediate and advanced):
        return 'Not available'
    difficulty_pie_chart = create_difficulty_chart(beginner, intermediate, advanced)
    st.pyplot(difficulty_pie_chart)
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
    
if st.session_state.selected_resort:
    display_resort_modal()

# Footer
st.markdown(
    """
    Data from [indyskipass.com](https://www.indyskipass.com/our-resorts) as of September 20, 2025.  
    
    ---
    Help improve this app:
    - [Report a Bug](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=%5BBUG%5D+%3CShort+description%3E)
    - [Suggest a Feature](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.md&title=%5BFEATURE%5D+%3CShort+description%3E)
    - [Kanban Board](https://github.com/users/jonathanstelman/projects/2/views/1)  
    """
)

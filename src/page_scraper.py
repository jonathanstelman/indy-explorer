"""
Scrapes data from resorts from general resorts page and resort-specific pages
"""

import json
import re
import requests
from bs4 import BeautifulSoup


CACHE_DIRECTORY = 'cache/'


def get_page_html(page_url: str, read_mode: str, cache_page=True) -> str:
    """
    Gets the html of a web page. Allows caching pages and writing to a cache
    """
    cache_file = CACHE_DIRECTORY + page_url.split('/')[-1] + '.html'
    assert(read_mode in ['cache', 'live'])


    if read_mode == 'live':
        # Load page from URL
        print(f'Fetching contents from web page: "{page_url}"')
        page = requests.get(page_url, timeout=5)
        page_html = page.text

        if cache_page:
            print(f'Caching web page to file: "{cache_file}"')
            try:
                with open(cache_file, 'x', encoding='utf-8') as f:
                    f.write(page_html)
            except FileExistsError:
                print(f'Cache file already exists: "{cache_file}"')

    else: # read_mode == 'cache'
        print(f'Fetching contents from cached file: "{cache_file}"')
        with open(cache_file, 'r', encoding='utf-8') as f:
            page_html: str = f.read()

    return page_html


def get_numbers(text: str) -> int:
    """
    Uses regex to extract digits (0-9) from a string. Returns the digits as an integer.

    TODO: We might want to generalize this to work for decimal values.
          Would just need to extract decimal points, then cast as float.
    """
    numbers = re.findall(r'\d+', text)
    if len(numbers) == 1:
        return int(numbers[0])
    else:
        return None


def parse_lat_long(point_string: str):
    """
    Extracts latitude and longitude from a string in the format: 'POINT (longitude latitude)'.
    """
    coords = point_string.replace("POINT (", "").replace(")", "").split()
    longitude, latitude = map(float, coords)
    return {
        'latitude': latitude,
        'longitude': longitude
    }


def parse_vertical(vertical_str: str):
    """
    Extracts the vertical height in feet
    """
    if vertical_str.endswith('ft'):
        return int(vertical_str[:-2])
    return None


def to_boolean(data_string: str) -> bool:
    """
    Converts specified string values to boolean
    """
    return data_string.lower() in ('true', 'yes')


def get_class_value(page_body, class_name: str) -> str:
    """
    Gets the value of a class
    Use only if there is only one instance of the class in the page
    """
    try:
        return page_body.find(class_=class_name)[0]
    except Exception:
        print(f'Could not get value for class: "{class_name}"')


def parse_our_resorts_page(page_html: str) -> dict:
    """
    gets resorts data from 'our-resorts.html'
    """

    soup = BeautifulSoup(page_html, 'html.parser')
    print(f'Page title: "{soup.title}"')

    page_body = soup.find(id='main-content')
    resort_node_class = 'node--type-resort'
    resort_nodes = page_body.find_all(class_=resort_node_class)
    print(f'{len(resort_nodes)} Resort Card ({resort_node_class}) objects found', end='\n\n')

    resort_node_list = list(resort_nodes)
    resorts = {}
    success_count = 0
    failed_count = 0
    for resort_node in resort_node_list:
        _id = None
        try:
            _id = resort_node['data-history-node-id']
        except KeyError:
            print('Resort missing ID! Skipping')
            failed_count += 1

        name = None
        location_name = None
        coordinates = None
        is_nordic = None
        is_alpine_xc = None
        is_xc_only = None
        is_allied = None
        vertical = None
        num_trails = None
        num_lifts = None
        is_open_nights = None
        has_terrain_parks = None
        href = None

        name = resort_node.select_one("span.label").get_text(strip=True)
        location_name = resort_node.select_one("span.location").get_text(strip=True)
        is_open_nights = to_boolean(resort_node.select_one("li:nth-child(4) .value").get_text(strip=True))
        has_terrain_parks = to_boolean(resort_node.select_one("li:nth-child(5) .value").get_text(strip=True))

        try:
            vert_str = resort_node.select_one("li:nth-child(1) .value").get_text(strip=True)
            vertical = parse_vertical(vert_str)
        except KeyError:
            print(f'Could not get vertical for resort ID: {_id}')
        except ValueError:
            print(f'Could not parse vertical "{vert_str}" for resort ID {_id}')

        try:
            trails = resort_node.select_one("li:nth-child(2) .value").get_text(strip=True)
            num_trails = int(trails)
        except KeyError:
            print(f'Could not get trails for resort ID: {_id}')
        except ValueError:
            print(f'Could not parse trail number "{trails}" for resort ID {_id}')

        try:
            lifts = resort_node.select_one("li:nth-child(3) .value").get_text(strip=True)
            num_lifts = int(lifts)
        except KeyError:
            print(f'Could not get lifts for resort ID: {_id}')
        except ValueError:
            print(f'Could not parse lift number "{lifts}" for resort ID {_id}')

        try:
            coordinates = parse_lat_long(resort_node['data-location'])
        except KeyError:
            print(f'Could not get coordinate location for resort ID: {_id}')

        try:
            is_nordic = to_boolean(resort_node['data-isnordic'])
        except KeyError:
            print(f'Could not get is_nordic for resort ID: {_id}')

        try:
            is_alpine_xc = to_boolean(resort_node['data-isalpinexc'])
        except KeyError:
            print(f'Could not get is_alpine_xc for resort ID: {_id}')

        try:
            is_xc_only = to_boolean(resort_node['data-isxconly'])
        except KeyError:
            print(f'Could not get is_xc_only for resort ID: {_id}')

        try:
            is_allied = to_boolean(resort_node['data-isallied'])
        except KeyError:
            print(f'Could not get is_allied for resort ID: {_id}')


        try:
            href = resort_node['href']
        except KeyError:
            print(f'Could not get href for resort ID: {_id}')

        resorts[_id] = {
            'name': name,
            'coordinates': coordinates,
            "location_name": location_name,
            'vertical': vertical,
            'is_nordic': is_nordic,
            'is_alpine_xc': is_alpine_xc,
            'is_xc_only': is_xc_only,
            'is_allied': is_allied,
            "num_trails": num_trails,
            "num_lifts": num_lifts,
            "is_open_nights": is_open_nights,
            "has_terrain_parks": has_terrain_parks,
            "href": href
        }
        success_count += 1

    # pprint(resorts, indent=4)
    print(f'Parsed {success_count} resorts')
    print(f'Failed to parse {failed_count} resorts')

    with open('data/resorts_raw.json', 'w', encoding='utf-8') as json_file:
        json.dump(resorts, json_file, indent=4)

    return resorts



def parse_resort_page(html_content: str, resort_id: str, resort_slug: str) -> dict:
    """
    Parses the resort page and extracts the following data:
    - name
    - description
    - trails
    - acres
    - terrain parks
    - night skiing
    - vertical (elevation, summit, and base)
    - terrain difficulty coverage
    - snowfall
    - lifts
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    resort_data = {}

    resort_data['id'] = resort_id
    resort_data['slug'] = resort_slug
    resort_data['name'] = soup.find('title').text.split('|')[0].strip()
    description_meta = soup.find('meta', {'name': 'description'})
    resort_data['description'] = description_meta['content'] if description_meta else ''
    button_div = soup.find('div', class_='grid-inner-full d-flex jc-center buttons')
    url_button = button_div.find('a', class_='button-inverted')
    resort_data['website'] = url_button['href'] if url_button else None

    # Trails
    trails_field = soup.find('div', class_='field--name-field-trails')
    resort_data['trails'] = int(trails_field.text.strip()) if trails_field else 0

    # Lifts
    lifts_field = soup.find('div', class_='field--name-field-lifts')
    resort_data['lifts'] = int(lifts_field.text.strip()) if lifts_field else 0

    # Acres
    acres_field = soup.find('div', class_='field--name-field-acres')
    resort_data['acres'] = int(acres_field.text.strip()) if acres_field else None

    # Trail Length
    trail_length_field = soup.find('div', class_='field--name-field-trail-length')
    resort_data['trail_length_km'] = get_numbers(trail_length_field.text.strip()) if trail_length_field else None
    resort_data['trail_length_mi'] = int(resort_data['trail_length_km'] * 0.621371) if resort_data['trail_length_km'] else None

    # Is Cross Country
    grid_field = soup.find('div', class_='fade-in grid-area-main')
    type_field = grid_field.find('h2') if grid_field else None
    type_text = type_field.text.strip().lower() if type_field else ''
    resort_data['is_cross_country'] = 'cross country' in type_text

    # Dog friendly
    dog_field = soup.find('div', class_='field--name-field-dog-friendly')
    resort_data['is_dog_friendly'] = 'Yes' in dog_field.text.strip() if dog_field else False

    # Snowshoeing
    snowshoe_field = soup.find('div', class_='field--name-field-snowshoeing')
    resort_data['has_snowshoeing'] = 'Yes' in snowshoe_field.text.strip() if snowshoe_field else False

    # Terrain parks
    terrain_parks_field = soup.find('div', class_='field--name-field-terrain-parks')
    if terrain_parks_field:
        resort_data['terrain_parks'] = 'Yes' in terrain_parks_field.text.strip()

    # Night skiing
    night_skiing_field = soup.find('div', class_='field--name-field-night-skiing')
    if night_skiing_field:
        resort_data['night_skiing'] = 'Yes' in night_skiing_field.text.strip()

    # Vertical (elevation, summit, and base)
    resort_data['vertical_base_ft'] = None
    resort_data['vertical_summit_ft'] = None
    resort_data['vertical_elevation_ft'] = None

    base_div = soup.find('div', class_='elevation__tag--base')
    if base_div:
        resort_data['vertical_base_ft'] = get_numbers(base_div.text.strip())

    summit_div = soup.find('div', class_='elevation__tag--summit')
    if summit_div:
        resort_data['vertical_summit_ft'] = get_numbers(summit_div.text.strip())

    elevation_div = soup.find('div', class_='elevation__tag--vertical')
    if elevation_div:
        resort_data['vertical_elevation_ft'] = get_numbers(elevation_div.text.strip())


    # Terrain difficulty coverage
    resort_data['difficulty_beginner'] = None
    resort_data['difficulty_intermediate'] = None
    resort_data['difficulty_advanced'] = None

    for level in ['beginner', 'intermediate', 'advanced']:
        diff_class = soup.find('div', class_=f'field--name-field-{level}')
        if diff_class:
            resort_data[f'difficulty_{level}'] = get_numbers(diff_class.text.strip())

    # Snowfall
    resort_data['snowfall_average_in'] = None
    resort_data['snowfall_high_in'] = None
    snowfall_field = soup.find('div', class_='snowfall--content')
    if snowfall_field:
        for snow_type in ['average', 'high']:
            snowfall_div = snowfall_field.find('div', class_=f'label {snow_type}')
            if snowfall_div:
                snowfall_raw = snowfall_div.find('span', class_='f-w-700 d-block').text.strip()
                resort_data[f'snowfall_{snow_type}_in'] = int(snowfall_raw.split('in')[0].strip())

    return resort_data

OUR_RESORTS_URL = 'https://www.indyskipass.com/our-resorts'

def cache_our_resorts_page(read_mode='live') -> str:
    """
    Fetches and caches the 'our resorts' page HTML.
    Returns the HTML string.
    """
    return get_page_html(OUR_RESORTS_URL, read_mode=read_mode)

def parse_and_save_our_resorts(page_html: str, output_path='data/resorts_raw.json') -> dict:
    """
    Parses the 'our resorts' HTML and saves the parsed data to JSON.
    Returns the parsed resorts dict.
    """
    resorts = parse_our_resorts_page(page_html)
    with open(output_path, 'w', encoding='utf-8') as json_file:
        json.dump(resorts, json_file, indent=4)
    return resorts

def cache_and_parse_resort(resort_id, resort_href, read_mode='live', output_dir='data'):
    """
    Fetches, caches, parses, and saves a single resort's page.
    """
    url = f'https://www.indyskipass.com{resort_href}'
    slug = resort_href.replace('/our-resorts/', '').replace('/', '')
    page_html = get_page_html(url, read_mode=read_mode)
    resort_dict = parse_resort_page(page_html, resort_id=resort_id, resort_slug=slug)
    with open(f'{output_dir}/{slug}.json', 'w', encoding='utf-8') as f:
        json.dump(resort_dict, f, indent=4)
    print(f'Parsed resort: "{resort_dict["name"]}"')
    return resort_dict

def main():
    # 1. Cache and parse the "our resorts" page
    our_resorts_html = cache_our_resorts_page(read_mode='live')
    resorts = parse_and_save_our_resorts(our_resorts_html)

    # 2. Iterate over all resorts and retrieve resort details
    for _id, resort in resorts.items():
        cache_and_parse_resort(_id, resort["href"], read_mode='live')

if __name__ == '__main__':
    main()

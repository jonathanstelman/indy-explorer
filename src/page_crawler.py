import json
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

#
from pprint import pprint

url = 'https://www.indyskipass.com/our-resorts'

read_mode = 'static'
# read_mode = 'live'

cache_page = True
cache_file_name = 'our-resorts.html'


assert(read_mode in ['static', 'live'])
if read_mode == 'live':
    # Load page from URL
    print(f'Fetching contents from web page: "{url}"')
    page = requests.get(url, timeout=5)
    page_html = page.text

    if cache_page:
        print(f'Caching web page to file: "{cache_file_name}"')
        with open(cache_file_name, 'x', encoding='utf-8') as f:
            f.write(page_html)

else: #read_mode == 'static':
    print(f'Fetching contents from cached file: "{cache_file_name}"')
    with open(cache_file_name, 'r', encoding='utf-8') as f:
        page_html = f.read()




# parse HTML document as BeautifulSoup object
print()
soup = BeautifulSoup(page_html, 'html.parser')
print(f'Page title: "{soup.title}"')
page_body = soup.find(id='main-content')


# Once we understand the data structure, we'll iterate over it and add to resorts dictionary below
resorts = {}


resort_node_class = 'node--type-resort' # all cards on the page are instances of type "copy"
resort_nodes = page_body.find_all(class_=resort_node_class)
print(f'{len(resort_nodes)} Resort Card ({resort_node_class}) objects found')

print()
resort_node_list = [resort_node for resort_node in resort_nodes]


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
        return int(vert_str[:-2])
    return None


def to_boolean(data_string):
    """
    Converts specified string values to boolean
    """
    return True if data_string.lower() in ('true', 'yes') else False


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
    city = None
    location = None
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

    # TODO: add try/except statements
    name = resort_node.select_one("span.label").get_text(strip=True)
    city = resort_node.select_one("span.location").get_text(strip=True)
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
        location = parse_lat_long(resort_node['data-location'])
    except KeyError:
        print(f'Could not get location for resort ID: {_id}')

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
        'location': location,
        'latitude': location['latitude'] if location else None,
        'longitude': location['longitude'] if location else None,
        'vertical': vertical,
        'is_nordic': is_nordic,
        'is_alpine_xc': is_alpine_xc,
        'is_xc_only': is_xc_only,
        'is_allied': is_allied,
        "city": city,
        "num_trails": num_trails,
        "num_lifts": num_lifts,
        "is_open_nights": is_open_nights,
        "has_terrain_parks": has_terrain_parks,
        "href": href
    }
    success_count += 1    


pprint(resorts, indent=4)
print(f'Parsed {success_count} resorts')
print(f'Failed to parse {failed_count} resorts')

with open('data/resorts_data.json', 'w', encoding='utf-8') as json_file:
    json.dump(resorts, json_file, indent=4)
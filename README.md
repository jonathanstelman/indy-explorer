# Indy Explorer

Indy Explorer is a [Streamlit](https://streamlit.io/) app designed to help you navigate resorts in the [Indy Pass](https://www.indyskipass.com/) product with ease.

## Features

- **Resort Data Extraction**: Uses [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) to scrape data from the Indy Pass resort pages.
- **Location Normalization**: Utilizes the [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding) to normalize location data.
- **Interactive UI**: Built with Streamlit for greater interactivity with resort information.

## Data Source

Data is sourced from [indyskipass.com](https://www.indyskipass.com/our-resorts) as of December 14, 2024.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/jonathanstelman/indy-explorer.git
    cd indy-explorer
    ```

2. Install [Poetry](https://python-poetry.org/docs/#installation):
    ```sh
    pipx install poetry
    ```

3. Install the required dependencies:
    ```sh
    poetry install
    ```

4. **Set up your Mapbox API token:**
    - Sign up for a free [Mapbox account](https://account.mapbox.com/auth/signup/).
    - Create an access token in your Mapbox account dashboard.
    - Add your token to `.streamlit/secrets.toml`:
        ```toml
        MAPBOX_TOKEN = "your_mapbox_token_here"
        ```
      Or set it as an environment variable:
        ```sh
        export MAPBOX_TOKEN=your_mapbox_token_here
        ```

5. Run the Streamlit app:
    ```sh
    poetry run streamlit run src/app.py
    ```

## Usage

1. **Fetch Resort Data**: Use the `get_page_html` function to fetch resort data from the web or cache.
2. **Parse Resort Data**: Use the `parse_resort_page` function to extract relevant resort data.
3. **View Data**: The data is displayed in an interactive Streamlit app.

## Refreshing Resort Data

To update all resort data (recommended about once per year), follow these steps:

1. **Backup your web cache and resort data (optional but recommended):**
    ```sh
    cp -r cache cache_backup_$(date +%Y%m%d_%H%M%S)
    cp -r data data_backup_$(date +%Y%m%d_%H%M%S)
    ```

2. **Remove the old cache and data folders:**
    ```sh
    rm -rf cache
    rm -rf data
    ```

3. **Fetch and cache the latest resort data:**
    ```sh
    poetry run python src/page_scraper.py
    ```
    This will:
    - Download and cache the latest "our resorts" page.
    - Parse and save `data/resorts_raw.json`.
    - Download, cache, and parse each individual resort page, saving to `data/<resort>.json`.


4. **Prepare the final CSV for the Streamlit app:**
    ```sh
    poetry run python src/prep_resort_data.py
    ```
    This will:
    - Use the Google Maps API to retrieve and save normalized location data if `data/resort_locations.csv` is missing.
    - Merge all resort data and location info.
    - Produce `data/resorts.csv` for the Streamlit app.


5. **Run the Streamlit app:**
    ```sh
    poetry run streamlit run src/app.py
    ```

**Note:**  
- If you encounter errors related to missing or outdated data files, re-run the above steps in order.
- The Google Maps API key must be set in your environment (see `.env.example`).
- **A Mapbox API token is required for map rendering in the Streamlit app.**
- **If you have a limited Google Maps API quota, be aware that regenerating `data/resort_locations.csv` will make API calls for each unique resort location.**  
- If you want to preserve previous location lookups, make sure to back up `data/resort_locations.csv` as well:
    ```sh
    cp data/resort_locations.csv data_backup_$(date +%Y%m%d_%H%M%S)_resort_locations.csv
    ```
- If you add new resorts or change location names, you may need to manually review or update `data/resort_locations.csv`.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a new Pull Request.

## Reporting Issues

Help improve this app:
- [Report a Bug](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=%5BBUG%5D+%3CShort+description%3E)
- [Suggest a Feature](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.md&title=%5BFEATURE%5D+%3CShort+description%3E)
- [Kanban Board](https://github.com/users/jonathanstelman/projects/2/views/1)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
- [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding)

---

Made by [Jonathan Stelman](https://github.com/jonathanstelman)
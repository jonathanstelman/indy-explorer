# Indy Explorer

Indy Explorer is a [Streamlit](https://streamlit.io/) app designed to help you navigate resorts in the [Indy Pass](https://www.indyskipass.com/) product with ease.

## Features

- **Resort Data Extraction**: Uses [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) to scrape data from the Indy Pass resort pages.
- **Location Normalization**: Utilizes the [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding) to normalize location data.
- **Peak Rankings Integration**: Includes resort quality scores from [peakrankings.com](https://peakrankings.com).
- **Interactive UI**: Built with Streamlit for greater interactivity with resort information.

## Data Sources

Resort data is aggregated from multiple sources:

| Source | What it provides |
|--------|-----------------|
| [indyskipass.com](https://www.indyskipass.com/our-resorts) | Resort details, stats, coordinates, blackout dates, reservation requirements |
| [peakrankings.com](https://peakrankings.com) | Resort quality scores and rankings |
| [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding) | Normalized city, state, and country for each resort |

## Quick Start

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

4. **Set up your Mapbox API token** (required for map rendering):
    - Sign up for a free [Mapbox account](https://account.mapbox.com/auth/signup/).
    - Create an access token in your Mapbox account dashboard.
    - Add your token to `.streamlit/secrets.toml`:
        ```toml
        MAPBOX_TOKEN = "your_mapbox_token_here"
        ```

5. Run the Streamlit app:
    ```sh
    poetry run streamlit run src/app.py
    ```

The app ships with pre-built data in `data/resorts.csv`, so you can run it immediately without refreshing data.

## Refreshing Resort Data

A single pipeline script handles the entire data refresh process. It scrapes resort pages, fetches blackout dates and rankings from Google Sheets, geocodes locations, and merges everything into `data/resorts.csv`.

### Incremental refresh (default)

```sh
poetry run python pipeline.py
```

This will:
- Fetch the main resorts page live (to detect added or dropped resorts)
- Use cached HTML for existing resort pages (only fetch new/missing ones)
- Always fetch fresh data from Google Sheets (blackout dates, Peak Rankings)
- Skip geocoding if `data/resort_locations.csv` already exists
- Merge everything into `data/resorts.csv`

### Full refresh

```sh
poetry run python pipeline.py --full
```

This will re-scrape all resort HTML pages (with a polite 0.5s delay between requests), regenerate geocoded locations, and rebuild everything from scratch.

### Running specific steps

```sh
poetry run python pipeline.py --steps fetch_peak_rankings,prep
```

Available steps (run in this order):

| Step | Description |
|------|-------------|
| `scrape_resorts` | Scrape Indy Pass resort pages |
| `scrape_reservations` | Scrape reservation requirements |
| `fetch_blackout_dates` | Fetch blackout dates from Google Sheets |
| `fetch_peak_rankings` | Fetch Peak Rankings from Google Sheets |
| `geocode` | Geocode resort locations via Google Maps |
| `prep` | Merge all data into `data/resorts.csv` |

### Backing up data

Before a full refresh, it's recommended to back up your current data:
```sh
cp -r cache backups/cache_backup_$(date +%Y%m%d_%H%M%S)
cp -r data backups/data_backup_$(date +%Y%m%d_%H%M%S)
```

### Environment variables

| Variable | Location | Required for |
|----------|----------|-------------|
| `MAPBOX_TOKEN` | `.streamlit/secrets.toml` | Map rendering in the Streamlit app |
| `GOOGLE_MAPS_API_KEY` | `.env` | Geocoding (only needed when regenerating `data/resort_locations.csv`) |

### Notes

- The Google Maps API key is only needed if `data/resort_locations.csv` is missing or you run with `--full`. Geocoding costs API quota, so the pipeline skips it by default.
- Individual pipeline scripts can still be run directly for debugging (e.g., `poetry run python src/page_scraper.py --read-mode cache`).
- If blackout resort names don't match `data/resorts.csv`, update `BLACKOUT_RESORT_NAME_MAP` in `src/blackout.py`.

---

## Testing & Continuous Integration

### Running tests locally

```sh
poetry install              # install dependencies
poetry run pytest            # run the full test suite
```

To generate JUnit + coverage reports (matches CI):
```sh
mkdir -p reports
poetry run pytest --junitxml=reports/junit.xml --cov=src --cov-report=xml:reports/coverage.xml -q
```

### Formatting

We use [Black](https://black.readthedocs.io/) for code formatting (configured in `pyproject.toml` with `skip-string-normalization = true`):

```sh
poetry run black --check .   # check
poetry run black .           # fix
```

### CI details

GitHub Actions runs tests and checks formatting on push/PRs:
- Runs `pytest` and generates `reports/junit.xml` and `reports/coverage.xml`
- Uploads a test artifact named `test-reports`
- Publishes a GitHub Check Run summary using `dorny/test-reporter@v2`
- Optionally uploads coverage to Codecov if `CODECOV_TOKEN` is set in repository secrets

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

- [Indy Pass](https://indyskipass.com)
- [Peak Rankings](https://peakrankings.com)
- [Streamlit](https://streamlit.io/)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
- [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding)

---

Made by [Jonathan Stelman](https://github.com/jonathanstelman)

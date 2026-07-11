# Indy Explorer

Indy Explorer helps you navigate resorts in the [Indy Pass](https://www.indyskipass.com/) with ease — filter by region, blackout dates, reservation requirements, Peak Rankings scores, and more.

**Live app: [indy-explorer.vercel.app](https://indy-explorer.vercel.app)**

## Architecture

```
/
├── backend/          # FastAPI app (Fly.io)
├── frontend/         # Vite + React app (Vercel)
├── pipeline/         # Data pipeline (scraping, geocoding, merging)
│   ├── pipeline.py   # Pipeline orchestrator
│   ├── page_scraper.py
│   ├── blackout.py
│   ├── reservations.py
│   ├── prep_resort_data.py
│   └── utils.py (+ others)
├── legacy/           # Legacy Streamlit redirect page (points to Vercel app)
├── data/             # Committed CSV data consumed by the backend
└── tests/            # Test suite
```

The pipeline in `pipeline/` feeds `data/resorts.csv`, which is committed to the repo and read at startup by the FastAPI backend.

## Features

- **Resort Data Extraction**: Scrapes resort pages from [indyskipass.com](https://www.indyskipass.com/our-resorts) with BeautifulSoup.
- **Location Normalization**: Google Maps Geocoding API normalizes city, state, and country.
- **Blackout Date Filtering**: Filter by blackout dates for both standard Indy Pass and Learn To Turn (LTT).
- **LTT Pass Support**: Filter for resorts in the Learn To Turn program with their own blackout calendar.
- **Peak Rankings Integration**: Resort quality scores from [peakrankings.com](https://peakrankings.com).
- **Interactive Map**: deck.gl/Mapbox map with clickable resort dots and auto-zoom.

## Data Sources

| Source | What it provides |
|--------|-----------------|
| [indyskipass.com](https://www.indyskipass.com/our-resorts) | Resort details, stats, coordinates, blackout dates, reservation requirements |
| [Indy Pass LTT Google Sheet](https://docs.google.com/spreadsheets/d/e/2PACX-1vTUXA5uhe2QwuQvCTpaSpIQmNNWIAp4gADGo5DIUeDwMOfgg9a8nEMU2K_4J9_24E2dGaLgbBnplpqg/pubhtml?gid=484077440&single=true) | Learn To Turn participating resorts and blackout dates |
| [peakrankings.com](https://peakrankings.com) | Resort quality scores and rankings |
| [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding) | Normalized city, state, and country |

## Refreshing Resort Data

The pipeline orchestrator handles scraping, geocoding, blackout dates, rankings, and merging.

The pipeline automatically backs up `data/resorts.csv`, `data/resort_id_map.csv`, and `data/pipeline_metadata.json` to a timestamped directory under `backups/` before any steps run. The 10 most recent backups are kept; older ones are deleted. To restore, copy the desired files back to `data/`.

```sh
# Incremental refresh (uses cached HTML, fetches new resorts only)
poetry run python pipeline/pipeline.py

# Full refresh (re-scrape all pages, regenerate geocoded locations)
poetry run python pipeline/pipeline.py --full

# Run specific steps only
poetry run python pipeline/pipeline.py --steps fetch_peak_rankings,prep
```

Available pipeline steps (run in order):

| Step | Description |
|------|-------------|
| `scrape_resorts` | Scrape Indy Pass resort pages |
| `scrape_reservations` | Scrape reservation requirements |
| `fetch_blackout_dates` | Fetch blackout dates from Google Sheets |
| `fetch_ltt_dates` | Fetch LTT blackout dates from Google Sheets |
| `fetch_peak_rankings` | Fetch Peak Rankings from Google Sheets |
| `geocode` | Geocode resort locations via Google Maps |
| `prep` | Merge all data into `data/resorts.csv` |

### Environment Variables

| Variable | Location | Required for |
|----------|----------|-------------|
| `GOOGLE_MAPS_API_KEY` | `.env` | Geocoding (only when regenerating `data/resort_locations.csv`) |
| `VITE_MAPBOX_TOKEN` | Vercel dashboard | Map rendering in the React frontend |

## Testing & CI

```sh
poetry run pytest            # run the full test suite
poetry run black --check .   # check formatting
poetry run black .           # fix formatting
```

GitHub Actions runs tests and Black checks on push/PRs. Coverage is optionally uploaded to Codecov.

## Deployment

- **Frontend:** [indy-explorer.vercel.app](https://indy-explorer.vercel.app) (Vercel, auto-deploys from `main`)
- **Backend:** [indy-explorer-backend.fly.dev](https://indy-explorer-backend.fly.dev) (Fly.io, deploy with `flyctl deploy --config backend/fly.toml`)

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/my-change`).
3. Make your changes and run tests.
4. Open a Pull Request.

- [Report a Bug](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=%5BBUG%5D+%3CShort+description%3E)
- [Suggest a Feature](https://github.com/jonathanstelman/indy-explorer/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.md&title=%5BFEATURE%5D+%3CShort+description%3E)
- [Project Board](https://github.com/users/jonathanstelman/projects/2/views/1)

## License

GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

## Acknowledgements

- [Indy Pass](https://indyskipass.com)
- [Peak Rankings](https://peakrankings.com)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
- [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding)

---

Made by [Jonathan Stelman](https://github.com/jonathanstelman)

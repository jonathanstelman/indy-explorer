# Copilot / AI Agent Instructions — Indy Explorer

Summary
- Purpose: Interactive Streamlit app that maps and presents Indy Pass resorts using scraped IndyPass pages + Google Maps geocoding + Mapbox for maps.
- Agent goal: make small, safe, discoverable changes (fix parsers, add fields, improve data prep, or update UI) while minimizing live web requests and preserving cached data.

Quick start (commands you'll use)
- Install: `pipx install poetry && poetry install`
- Fetch pages (live, will write `cache/`):
  - `poetry run python src/page_scraper.py`
- Regenerate prepared CSV for the app:
  - `poetry run python src/prep_resort_data.py`
- Run the app:
  - `poetry run streamlit run src/app.py`

Key files & responsibilities
- `src/page_scraper.py` — HTML fetch + parsing helpers. Use `get_page_html(page_url, read_mode)` with `read_mode` in `['live','cache']` to avoid unnecessary live requests.
- `src/prep_resort_data.py` — merges `data/resorts_raw.json`, per-resort JSON files (`data/<slug>.json`), and `data/resort_locations.csv` (cached geocoding), then writes `data/resorts.csv` used by the app.
- `src/location_utils.py` — wraps Google Maps geocoding (`GOOGLE_MAPS_API_KEY` via `.env` or env var). Use `generate_resort_locations_csv()` to cache geocoding results into `data/resort_locations.csv`.
- `src/app.py` — Streamlit UI + mapping (pydeck). Expects `data/resorts.csv` and `st.secrets['MAPBOX_TOKEN']`.

Data flow (canonical)
1. `page_scraper.cache_our_resorts_page()` -> `data/resorts_raw.json`
2. `page_scraper.cache_and_parse_resort()` -> `data/<resort_slug>.json`
3. `location_utils.generate_resort_locations_csv()` -> `data/resort_locations.csv` (cached geocode results)
4. `prep_resort_data.py` merges the above -> `data/resorts.csv`
5. `app.py` reads `data/resorts.csv` and renders map/table

Project-specific patterns & notes
- Caching: HTML pages are written to `cache/<slug>.html`. Prefer working from cached HTML for parser development and tests to avoid hammering upstream site.
- Naming conventions used in CSV/output:
  - boolean presentation fields end with `_display` (mapped to `Yes`/`No`)
  - tooltip-ready fields end with `_tt`
  - vertical converted units: `vertical` (ft) and `vertical_meters`
- When changing parsers, update `parse_resort_page()` (in `page_scraper.py`) and `prep_resort_data.py` to ensure the final column list (see the `cols = [...]` block) still matches `app.py` column expectations.
- `get_page_html` uses `open(..., 'x')` to write cache files (FileExistsError is caught). If you need to overwrite a cache, remove the file first.

Secrets & env vars
- Mapbox: `st.secrets['MAPBOX_TOKEN']` — add `.streamlit/secrets.toml` with:
  ```toml
  MAPBOX_TOKEN = "your_mapbox_token"
  ```
- Google Maps: `GOOGLE_MAPS_API_KEY` in `.env` or env var (used by `src/location_utils.py`). Geocoding calls can be expensive—always prefer `data/resort_locations.csv` if present.

Agent safety & helpful constraints
- Prefer: working with cached HTML (`cache/`) and `data/resorts_raw.json` for parser changes.
- Avoid: repeated live scraping runs; rate-limit/pace requests if live testing is necessary and respect `our-resorts` site.
- When adding scraper changes: add at least one sample HTML fixture (place under `tests/fixtures/` or a `dev/fixtures/` folder) and show how to regenerate CSV with `poetry run python src/prep_resort_data.py`.

Debugging tips & quick checks
- Validate CSV format expected by `app.py`: `data/resorts.csv` must have `index` label, `latitude`/`longitude` for mapping, and tooltip/display columns referenced in `src/app.py`.
- Quick local check of a parser function:
  - `python -c "from src.page_scraper import parse_resort_page, get_page_html; html=open('cache/<slug>.html').read(); print(parse_resort_page(html,'id','slug'))"`
- If location results are incorrect or blank, check `data/resort_locations.csv` and re-run `generate_resort_locations_csv()` (note API quota).

When to ask maintainers
- If a scraping change affects many resorts (large structural changes on indyskipass.com), open an issue before running a full scrape.
- Ask before committing or pushing large regenerate changes to `data/` — the repository includes cached/backup files; large diffs to data files can be noisy.

If you update this file
- Keep it short and example-focused. Add any new actionable commands or patterns that help the next agent be productive.

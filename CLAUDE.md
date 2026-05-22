# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Indy Explorer is a Python/Streamlit app that scrapes, geocodes, and visualizes Indy Pass ski resorts. Data flows through a pipeline: scrape HTML → parse resort pages → geocode locations → merge into CSV → render in Streamlit with pydeck/Mapbox maps.

**A React + FastAPI rewrite is in progress.** GitHub issues #51–#77 track the full planned work. Issues #51–#55 are complete (monorepo, FastAPI scaffold, React frontend scaffold, deployment config, resort data model). The Streamlit app at `app.py` remains live on Streamlit Community Cloud during the transition. Do not assume Streamlit is the long-term target.

## Architecture

### Data Pipeline

1. **`pipeline/page_scraper.py`** — Scrapes indyskipass.com, caches HTML in `cache/`, outputs `data/resorts_raw.json` and `data/resort_page_extracts/<slug>.json`
2. **`pipeline/utils.py`** — Google Maps geocoding wrapper. Caches results in `data/resort_locations.csv` to minimize API calls. Client is lazily initialized (safe without API key in CI).
3. **`pipeline/blackout.py`** / **`pipeline/reservations.py`** — Fetch blackout dates from Google Sheets and reservation requirements from the Indy Pass site
4. **`pipeline/prep_resort_data.py`** — Merges all data sources into `data/resorts.csv`. Calls `assign_resort_ids()` to stamp stable UUIDs using `data/resort_id_map.csv`.
5. **`app.py`** — Streamlit UI: interactive map (pydeck/Mapbox), filterable table, region-based zoom (map config inlined)
6. **`backend/models.py`** — Pydantic `Resort` model covering all columns in `data/resorts.csv`
7. **`backend/data.py`** — `load_resorts()` reads `data/resorts.csv` into `list[Resort]`

### Field Naming Conventions in CSV

- `_display` suffix: boolean fields formatted as "Yes"/"No"
- `_tt` suffix: tooltip-ready display fields
- `_meters` suffix: metric unit conversions (e.g., `vertical_meters`)

### Key Design Patterns

- **Cache-first scraping**: HTML pages written with `open(..., 'x')` to prevent overwrites. Delete `cache/*.html` to re-fetch.
- **Defensive parsing**: `get_numbers()` extracts integers safely, returns `None` on malformed input.
- **Lazy API client**: `googlemaps.Client` not created at import time — tests monkeypatch `utils.gmaps`.

## Key Decisions

Settled architectural and design decisions are documented in [`docs/decisions.md`](docs/decisions.md). Do not relitigate them without checking with the user. When completing any non-trivial task, append a new entry there — see the format specified in that file.

## Environment & Secrets

- `GOOGLE_MAPS_API_KEY` in `.env` — for geocoding (quota-sensitive; prefer cached `data/resort_locations.csv`). In production: `flyctl secrets set GOOGLE_MAPS_API_KEY=...`
- `MAPBOX_TOKEN` in `.streamlit/secrets.toml` — for map rendering in Streamlit
- `VITE_MAPBOX_TOKEN` — for map rendering in the React frontend. Set in Vercel dashboard (build-time env var; `VITE_` prefix required for browser exposure)

## Commands

```bash
# Install (pipeline/Streamlit)
pipx install poetry && poetry install

# Run Streamlit app (serves on localhost:8501)
poetry run streamlit run app.py

# Run FastAPI backend (serves on localhost:8000)
cd backend && poetry run uvicorn main:app --reload
# or via Docker:
# docker build -t indy-explorer-backend backend/ && docker run -p 8000:8000 indy-explorer-backend

# Tests — always use poetry run; pytest lives in the poetry-managed venv
poetry run pytest                    # run all tests (pytest.ini sets -q and testpaths=tests)
poetry run pytest tests/test_blackout.py -k "test_name"  # run a single test
poetry run pytest backend/tests/     # run backend tests

# Formatting (Black, pinned to 25.12.0)
poetry run black --check .          # check
poetry run black .                  # fix

# CI-matching test + coverage reports
mkdir -p reports
poetry run pytest --junitxml=reports/junit.xml --cov=pipeline --cov-report=xml:reports/coverage.xml -q

# Data refresh pipeline
poetry run python pipeline/pipeline.py              # incremental (use caches, fetch new resorts only)
poetry run python pipeline/pipeline.py --full       # full refresh (re-scrape everything)
poetry run python pipeline/pipeline.py --steps scrape_resorts,prep  # run specific steps only

# Individual pipeline scripts (for debugging)
poetry run python pipeline/page_scraper.py                          # scrape resort pages → cache/ and data/
poetry run python pipeline/cache_blackout_reservations.py --read-mode live
poetry run python pipeline/reservations.py --read-mode cache
poetry run python pipeline/prep_resort_data.py                      # merge all data → data/resorts.csv
```

## Development Process

- **State the plan before coding.** For any non-trivial task, briefly describe the approach and which files will be touched before writing code. Surface ambiguities then, not mid-implementation.
- **TDD by default.** Write the failing test before writing implementation. No exceptions for "small" changes.
  - New feature: write the test, confirm it fails, then implement until it passes.
  - Bug fix: write a test that reproduces the bug before touching source code.
  - Pipeline changes: add or update a fixture in `tests/fixtures/` as needed.
  - Backend changes: test goes in `backend/tests/` and runs under the backend suite.
- **One logical change per commit.** Don't bundle unrelated fixes.

## Testing Conventions

- Fixtures in `tests/fixtures/` (HTML pages, CSV samples)
- Mock `utils.gmaps` with `monkeypatch` — never call the real Google API in tests
- `tests/conftest.py` adds `pipeline/` to `sys.path` so test imports resolve to pipeline modules
- Python 3.12 required
- Backend tests live in `backend/tests/` and run separately: `cd backend && pytest tests/`
- CI runs three jobs: Format (Black), Test suite (pipeline), Backend test suite

## Code Style

- Black with `line-length = 100` and `skip-string-normalization = true` (preserves single quotes)
- Pre-commit hook runs Black automatically

## Branch Naming Convention

`feature/<issue-numbers>-<short-description>` — e.g. `feature/72-73-74-75-resort-table-and-detail`. Use kebab-case for the description. List all issue numbers covered by the branch.

## Working from GitHub Issues

When assigned a GitHub issue to implement, always fetch the full issue including comments before starting:

```bash
gh issue view <number> --repo jonathanstelman/indy-explorer --comments
```

**Why:** Open questions and clarifications are left as comments on issues, not in the issue body. Reading the body alone will miss them. If a comment contains an unresolved question, surface it to the user before writing code rather than making assumptions.

The project board is: https://github.com/users/jonathanstelman/projects/2

## Session Documentation

After completing any non-trivial task, append a summary to [`docs/decisions.md`](docs/decisions.md). If the file doesn't exist, create it. Keep entries terse — this is a trail, not a journal.

```
## YYYY-MM-DD — Short description
**Issue:** #number (if applicable)
**Decision:** What was decided or implemented.
**Rationale:** Why, and what alternatives were considered.
**Follow-up:** Open items or gotchas, if any.
```

## Important Constraints

- Prefer working from cached HTML (`cache/`) for parser development — avoid live scraping
- When changing parsers in `parse_resort_page()`, also update `prep_resort_data.py` column list and verify `app.py` column expectations match
- Avoid committing large diffs to `data/` files without coordinating with maintainers
- Check `data/resort_locations.csv` before regenerating — geocoding costs API quota
- **Never name a top-level directory after a Python package** (e.g., `streamlit/`, `fastapi/`). Python 3 treats any directory as a namespace package, which silently shadows the installed library on `sys.path`. This caused Streamlit Community Cloud boot failures when the app lived in `streamlit/`.
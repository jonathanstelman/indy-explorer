# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Indy Explorer scrapes, geocodes, and visualizes Indy Pass ski resorts. Data flows through a pipeline: scrape HTML → parse resort pages → geocode locations → merge into CSV → serve via FastAPI → render in React. The live app is at **https://indy-explorer.vercel.app**.

The Streamlit app (`legacy/app.py`) is retired — it now shows a redirect notice only. The React + FastAPI stack is the production target.

## Architecture

### Data Pipeline

1. **`pipeline/page_scraper.py`** — Scrapes indyskipass.com, caches HTML in `cache/`, outputs `data/resorts_raw.json` and `data/resort_page_extracts/<slug>.json`
2. **`pipeline/utils.py`** — Google Maps geocoding wrapper. Caches results in `data/resort_locations.csv` to minimize API calls. Client is lazily initialized (safe without API key in CI).
3. **`pipeline/blackout.py`** / **`pipeline/reservations.py`** — Fetch blackout dates from Google Sheets and reservation requirements from the Indy Pass site
4. **`pipeline/prep_resort_data.py`** — Merges all data sources into `data/resorts.csv`. Calls `assign_resort_ids()` to stamp stable UUIDs using `data/resort_id_map.csv`.
5. **`legacy/app.py`** — Retired Streamlit app (redirect notice only — do not develop against this)
6. **`backend/models.py`** — Pydantic `Resort` model covering all columns in `data/resorts.csv`
7. **`backend/data.py`** — `load_resorts()` reads `data/resorts.csv` into `list[Resort]`

### Field Naming Conventions in CSV

- `_display` suffix: boolean fields formatted as "Yes"/"No"
- `_tt` suffix: tooltip-ready display fields
- `_meters` suffix: metric unit conversions (e.g., `vertical_meters`)

### Frontend Architecture (React)

The aesthetic direction, dark mode token config, glow effects, and open design questions are documented in [`docs/design.md`](docs/design.md).

- **`src/theme.js`** — Single source of truth for all colors (`COLORS`), fonts (`FONTS`), map dot colors (`MAP_DOT_COLORS`), Ant Design theme config, and the `withAlpha(hex, alpha)` utility. **All color values in `.jsx` and `.css` files must reference named tokens from `COLORS` — no hardcoded hex or rgba strings anywhere in `src/`.**
- **`src/App.jsx`** — Top-level layout. Owns table state: `gridRef` (forwarded to AG Grid), `tablePanelRef` (fullscreen target), column visibility, and toolbar button handlers. The drag handle row contains the collapse toggle (left) and table controls (right): Select Columns popover, Download CSV, Full screen.
- **`src/components/ResortTable.jsx`** — AG Grid wrapper. A `forwardRef` component that forwards `ref` to `<AgGridReact>`. Exports `COLUMN_DEFS`, `HEADER_BY_FIELD`, `COL_GROUPS` for use by App.jsx's column-visibility popover. No internal toolbar — all controls live in App.jsx's drag handle.
- **`src/components/ResortTable.css`** — AG Grid header overrides only. Colors are set as CSS custom properties via `GRID_THEME_VARS` in ResortTable.jsx (e.g. `--indy-header-bg`) so the CSS file stays free of hardcoded values.

### Key Design Patterns (Pipeline)

- **Cache-first scraping**: HTML pages written with `open(..., 'x')` to prevent overwrites. Delete `cache/*.html` to re-fetch.
- **Defensive parsing**: `get_numbers()` extracts integers safely, returns `None` on malformed input.
- **Lazy API client**: `googlemaps.Client` not created at import time — tests monkeypatch `utils.gmaps`.

## Key Decisions

Settled architectural and design decisions are documented in [`docs/decisions.md`](docs/decisions.md). Do not relitigate them without checking with the user. When completing any non-trivial task, append a new entry there — see the format specified in that file.

## Ops Runbook

A personal ops runbook lives at `docs/ops-runbook.md` (git-ignored; the user keeps a copy outside the repo). It covers:

- Backend deploy commands (Fly.io) and how to verify a deploy
- Frontend deploy (Vercel) and required env vars
- Pipeline run commands and the backup/restore procedure
- Secrets and credentials inventory
- Common troubleshooting scenarios

**When ops practices change** (new deploy steps, new secrets, new services, architecture changes), update `docs/ops-runbook.md` to match. If the file is missing (user hasn't placed it yet), note the relevant change so the user can add it manually.

## Environment & Secrets

- `GOOGLE_MAPS_API_KEY` in `.env` — for geocoding (quota-sensitive; prefer cached `data/resort_locations.csv`). Not needed by the backend at runtime — pipeline only.
- `MAPBOX_TOKEN` in `.streamlit/secrets.toml` — for the legacy Streamlit redirect app (still deployed)
- `VITE_MAPBOX_TOKEN` — for map rendering in the React frontend. Set in Vercel dashboard (build-time env var; `VITE_` prefix required for browser exposure)

## Deployed Services

- **Backend:** `https://indy-explorer-backend.fly.dev` (Fly.io, region: ewr)
  - Deploy from repo root: `flyctl deploy --config backend/fly.toml`
  - Docker image bakes in `data/` at build time — redeploy after pipeline data updates
- **Frontend:** `https://indy-explorer.vercel.app` (Vercel, auto-deploys from `main`)

## Commands

```bash
# Install (pipeline)
pipx install poetry && poetry install

# Run FastAPI backend (serves on localhost:8000)
cd backend && poetry run uvicorn main:app --reload
# or via Docker:
# docker build -t indy-explorer-backend backend/ && docker run -p 8000:8000 indy-explorer-backend

# Run React frontend (serves on localhost:5173)
cd frontend && npm run dev

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
- **Always run `poetry run black --check .` before committing.** CI will fail if formatting is off. Fix with `poetry run black .`.

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

**At the start of every session**, read [`docs/planning.md`](docs/planning.md) to orient yourself — it records the current branch, what's done, what's next, and any open polish items.

**During and at the end of every session**, keep `docs/planning.md` up to date: mark completed items, add newly discovered tasks, and update "Up next" so the next session can pick up without re-deriving state from git history.

After completing any non-trivial task, add a summary to [`docs/decisions.md`](docs/decisions.md). Keep entries terse — this is a trail, not a journal. **Always insert entries in chronological order by date** — do not append blindly to the end if that would be out of order.

```
## YYYY-MM-DD — Short description
**Issue:** #number (if applicable)
**Decision:** What was decided or implemented.
**Rationale:** Why, and what alternatives were considered.
**Follow-up:** Open items or gotchas, if any.
```

## Important Constraints

- Prefer working from cached HTML (`cache/`) for parser development — avoid live scraping
- When changing parsers in `parse_resort_page()`, also update `prep_resort_data.py` column list
- Avoid committing large diffs to `data/` files without coordinating with maintainers
- Check `data/resort_locations.csv` before regenerating — geocoding costs API quota
- **Never name a top-level directory after a Python package** (e.g., `streamlit/`, `fastapi/`). Python 3 treats any directory as a namespace package, which silently shadows the installed library on `sys.path`. This caused Streamlit Community Cloud boot failures when the app lived in `streamlit/`.
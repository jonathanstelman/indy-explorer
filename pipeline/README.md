# Pipeline

Scripts that scrape, geocode, and merge Indy Pass resort data into `data/resorts.csv`.
The backend reads this file at startup; the scheduled GitHub Actions workflow (Issue #77)
commits updated CSVs back to the repo to trigger a fresh deploy.

## Quick start

Run from the **repo root** (not from inside `pipeline/`):

```bash
# Incremental — uses caches, only fetches new/missing resorts
poetry run python pipeline/pipeline.py

# Full refresh — re-scrapes everything
poetry run python pipeline/pipeline.py --full

# Run specific steps only
poetry run python pipeline/pipeline.py --steps scrape_resorts,prep
```

## Steps

| Step | Script | Notes |
|---|---|---|
| `scrape_resorts` | `page_scraper.py` | Fetches main Indy Pass page live; uses cached HTML for individual resorts unless `--full` |
| `scrape_reservations` | `reservations.py` | Parses reservation requirements from the Indy blackout/reservations page |
| `fetch_blackout_dates` | `blackout.py` | Reads standard blackout dates from Google Sheets (always live) |
| `fetch_ltt_dates` | `ltt_blackout.py` | Reads LTT blackout dates from Google Sheets (always live) |
| `fetch_peak_rankings` | `peak_rankings.py` | Reads Peak Rankings scores from Google Sheets (always live) |
| `geocode` | `utils.py` | Google Maps geocoding; incremental by default (geocodes only resorts missing from `data/resort_locations.csv`, a cheap no-op once nothing's missing); `--full` re-geocodes everything |
| `prep` | `prep_resort_data.py` | Merges all sources into `data/resorts.csv`; assigns stable UUIDs via `data/resort_id_map.csv` |

## Outputs

| File | Description |
|---|---|
| `data/resorts.csv` | Final merged dataset; committed to repo; read by the backend at startup |
| `data/resort_id_map.csv` | Stable UUID → source mapping; never delete — preserves IDs across runs |
| `data/pipeline_metadata.json` | Timestamp and mode of the last run; exposed by `GET /meta` as `last_pipeline_run` |
| `data/resort_locations.csv` | Geocoded coordinates cache; delete only if re-geocoding is needed |
| `cache/*.html` | Cached HTML pages; delete to force re-scrape on next run |

## Required environment variables

| Variable | Used by | Notes |
|---|---|---|
| `GOOGLE_MAPS_API_KEY` | `geocode` step | Only needed if `data/resort_locations.csv` is missing or `--full` is used |

Set in `.env` at the repo root for local runs. In GitHub Actions, set as a repository secret.
Google Sheets access uses a published CSV URL — no credentials required.

## Automatic backups

Before any steps run, the pipeline snapshots the critical data files into a timestamped directory:

```
backups/2026-05-24T16-50-57/
  resorts.csv
  resort_id_map.csv
  pipeline_metadata.json
```

The 10 most recent backups are kept; older ones are deleted automatically. To restore, copy the desired files back over `data/`.

The `backups/` directory is not tracked in git. Cache HTML files are not included in backups — they are large and regenerable.

## Cache behavior

- **HTML cache** (`cache/*.html`): Written with `open(..., 'x')` — never overwrites. Delete files manually to re-fetch. The `--full` flag deletes all resort HTML before running.
- **Geocoding cache** (`data/resort_locations.csv`): Incremental by default — only resorts missing from the cache (matched by name) are geocoded; existing rows are left as-is. A cheap no-op once nothing's missing, so the `geocode` step always runs rather than being skipped outright. Use `--full` to re-geocode every resort and overwrite the cache. Geocoding costs API quota — avoid unnecessary `--full` runs.
- **Resort IDs** (`data/resort_id_map.csv`): UUIDs are assigned once and preserved across all subsequent runs. Never delete this file.

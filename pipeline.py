"""
Data pipeline orchestrator for Indy Explorer.

Usage:
    poetry run python pipeline.py              # incremental (use caches where sensible)
    poetry run python pipeline.py --full       # full refresh (re-scrape everything)
    poetry run python pipeline.py --steps scrape_resorts,prep  # run specific steps only
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add src/ to sys.path so bare imports (e.g. "from page_scraper import ...") work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logger = logging.getLogger(__name__)

CACHE_DIR = Path('cache')
DATA_DIR = Path('data')


# ---- Step functions ----


def step_scrape_resorts(full: bool) -> None:
    """
    Scrape the main Indy Pass page and individual resort pages.
    - Incremental: always fetch main page live (detect roster changes),
      use cached HTML for individual resorts, fetch only new/missing ones.
    - Full: delete all cached resort HTML and re-scrape everything.
    """
    from page_scraper import (
        cache_our_resorts_page,
        parse_and_save_our_resorts,
        cache_and_parse_resort,
    )

    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(DATA_DIR / 'resort_page_extracts', exist_ok=True)

    if full:
        logger.info('Full mode: deleting cached resort HTML files...')
        deleted = 0
        for html_file in CACHE_DIR.glob('*.html'):
            if html_file.name != 'blackout-dates-reservations.html':
                html_file.unlink()
                deleted += 1
        logger.info('Deleted %d cached HTML files.', deleted)

    # Always fetch main page live to detect roster changes
    logger.info('Fetching main resorts page (live)...')
    our_resorts_html = cache_our_resorts_page(read_mode='live')
    resorts = parse_and_save_our_resorts(our_resorts_html)
    logger.info('Found %d resorts on main page.', len(resorts))

    # Scrape individual resort pages
    new_count = 0
    cached_count = 0
    for i, (_id, resort) in enumerate(resorts.items(), 1):
        slug = resort['href'].split('/')[-1]
        cache_file = CACHE_DIR / f'{slug}.html'

        if not full and cache_file.exists():
            # Use cached HTML — no HTTP request
            cache_and_parse_resort(_id, resort['href'], read_mode='cache')
            cached_count += 1
        else:
            # Fetch live (new resort or full refresh)
            logger.info('  [%d/%d] Fetching: %s', i, len(resorts), resort.get('name', slug))
            cache_and_parse_resort(_id, resort['href'], read_mode='live')
            new_count += 1
            time.sleep(0.5)  # be polite to Indy's servers

    logger.info(
        'Resort scraping complete: %d from cache, %d fetched live.', cached_count, new_count
    )


def step_scrape_reservations(full: bool) -> None:
    """
    Fetch the blackout/reservations HTML page and parse reservation requirements.
    - Incremental: use cached HTML if available.
    - Full: re-fetch the page.
    """
    from cache_blackout_reservations import fetch_blackout_reservations_html
    from reservations import parse_reservations_page, build_reservation_records

    read_mode = 'live' if full else 'cache'
    cache_file = CACHE_DIR / 'blackout-dates-reservations.html'

    # If cache doesn't exist, must fetch live regardless of mode
    if not cache_file.exists():
        read_mode = 'live'

    logger.info('Fetching blackout/reservations page (mode: %s)...', read_mode)
    html = fetch_blackout_reservations_html(read_mode=read_mode)

    parsed = parse_reservations_page(html)
    records = build_reservation_records(parsed)

    output_path = DATA_DIR / 'reservations_raw.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'resorts': records}, f, indent=2)
    logger.info('Wrote %s (%d records).', output_path, len(records))


def step_fetch_blackout_dates(full: bool) -> None:
    """
    Fetch blackout dates from Google Sheets. Always fetches fresh (no caching).
    """
    from blackout import get_blackout_dates_from_google_sheets

    output_path = DATA_DIR / 'blackout_dates_raw.csv'
    logger.info('Fetching blackout dates from Google Sheets (always live)...')
    df = get_blackout_dates_from_google_sheets(read_mode='live', cache_path=str(output_path))
    df.to_csv(output_path, index=False)
    logger.info('Wrote %s (%d rows).', output_path, len(df))


def step_fetch_ltt_dates(full: bool) -> None:
    """
    Fetch LTT blackout dates from Google Sheets. Always fetches fresh (no caching).
    """
    from ltt_blackout import get_ltt_dates_from_google_sheets

    output_path = DATA_DIR / 'ltt_dates_raw.csv'
    logger.info('Fetching LTT blackout dates from Google Sheets (always live)...')
    df = get_ltt_dates_from_google_sheets(read_mode='live', cache_path=str(output_path))
    df.to_csv(output_path, index=False)
    logger.info('Wrote %s (%d rows).', output_path, len(df))


def step_fetch_peak_rankings(full: bool) -> None:
    """
    Fetch Peak Rankings from Google Sheets. Always fetches fresh (no caching).
    """
    from peak_rankings import fetch_peak_rankings_csv

    logger.info('Fetching Peak Rankings from Google Sheets (always live)...')
    df = fetch_peak_rankings_csv(
        read_mode='live', cache_path=str(DATA_DIR / 'peak_rankings_raw.csv')
    )
    logger.info('Wrote %s (%d rows).', DATA_DIR / 'peak_rankings_raw.csv', len(df))


def step_geocode(full: bool) -> None:
    """
    Generate resort locations via Google Maps geocoding API.
    Skips if cache exists unless --full is used.
    """
    from utils import generate_resort_locations_csv

    output_path = DATA_DIR / 'resort_locations.csv'
    if not full and output_path.exists():
        logger.info('Skipping geocoding — %s exists. Use --full to regenerate.', output_path)
        return

    if full and output_path.exists():
        logger.info('Full mode: regenerating geocoded locations...')
    else:
        logger.info('Generating resort locations (first run)...')

    generate_resort_locations_csv()
    logger.info('Geocoding complete.')


def step_prep(full: bool) -> None:
    """
    Merge all data sources into data/resorts.csv.
    """
    import prep_resort_data

    prep_resort_data.main()
    logger.info('Merge complete — data/resorts.csv is ready.')


# ---- Step registry (execution order matters) ----

STEPS = [
    ('scrape_resorts', step_scrape_resorts, 'Scrape Indy Pass resort pages'),
    ('scrape_reservations', step_scrape_reservations, 'Scrape reservation requirements'),
    ('fetch_blackout_dates', step_fetch_blackout_dates, 'Fetch blackout dates from Google Sheets'),
    ('fetch_ltt_dates', step_fetch_ltt_dates, 'Fetch LTT blackout dates from Google Sheets'),
    ('fetch_peak_rankings', step_fetch_peak_rankings, 'Fetch Peak Rankings from Google Sheets'),
    ('geocode', step_geocode, 'Geocode resort locations via Google Maps'),
    ('prep', step_prep, 'Merge all data into resorts.csv'),
]


# ---- CLI ----


def main() -> None:
    step_names = [name for name, _, _ in STEPS]

    parser = argparse.ArgumentParser(
        description='Indy Explorer data pipeline.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Available steps:\n' + '\n'.join(f'  {n}: {d}' for n, _, d in STEPS),
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Full refresh: re-fetch all data sources, bypassing caches.',
    )
    parser.add_argument(
        '--steps',
        metavar='STEP,...',
        help=f'Comma-separated list of steps to run. Available: {", ".join(step_names)}',
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S',
    )

    # Determine which steps to run
    if args.steps:
        requested = [s.strip() for s in args.steps.split(',')]
        unknown = set(requested) - set(step_names)
        if unknown:
            parser.error(f'Unknown step(s): {", ".join(sorted(unknown))}')
        steps_to_run = [(n, f, d) for n, f, d in STEPS if n in requested]
    else:
        steps_to_run = STEPS

    mode = 'FULL REFRESH' if args.full else 'INCREMENTAL'
    logger.info('=== Indy Explorer Pipeline (%s) ===', mode)
    logger.info(
        'Running %d step(s): %s', len(steps_to_run), ', '.join(n for n, _, _ in steps_to_run)
    )

    for i, (name, func, description) in enumerate(steps_to_run, 1):
        logger.info('')
        logger.info('--- Step %d/%d: %s ---', i, len(steps_to_run), description)
        try:
            func(full=args.full)
        except Exception:
            logger.exception('Step "%s" failed. Aborting pipeline.', name)
            raise SystemExit(1)

    # Write pipeline metadata for the app to display
    metadata_path = DATA_DIR / 'pipeline_metadata.json'
    metadata = {
        'last_run': datetime.now(timezone.utc).isoformat(),
        'mode': 'full' if args.full else 'incremental',
        'steps_run': [n for n, _, _ in steps_to_run],
    }
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info('Wrote pipeline metadata to %s.', metadata_path)

    logger.info('')
    logger.info('=== Pipeline complete. ===')


if __name__ == '__main__':
    main()

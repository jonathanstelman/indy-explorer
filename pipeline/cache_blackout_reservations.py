"""
Fetch and cache the Indy Pass blackout/reservations page HTML.
"""

import argparse
import logging
from pathlib import Path

import requests

BLACKOUT_RESERVATIONS_URL = "https://www.indyskipass.com/blackout-dates-reservations"

logger = logging.getLogger(__name__)


def fetch_blackout_reservations_html(
    read_mode: str = "live",
    cache_path: str = "cache/blackout-dates-reservations.html",
) -> str:
    """
    Fetch the blackout/reservations page HTML.

    read_mode:
        - "live": fetch from the web and write to cache_path
        - "cache": read from cache_path
    """
    if read_mode not in ("live", "cache"):
        raise ValueError("read_mode must be 'live' or 'cache'")

    cache_file = Path(cache_path)
    if read_mode == "cache":
        return cache_file.read_text(encoding="utf-8")

    response = requests.get(BLACKOUT_RESERVATIONS_URL, timeout=10)
    response.raise_for_status()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(response.text, encoding="utf-8")
    return response.text


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="Fetch and cache the Indy Pass blackout/reservations page HTML."
    )
    parser.add_argument(
        "--read-mode",
        choices=["cache", "live"],
        default="live",
        help="Use cached HTML or fetch live page (default: live).",
    )
    parser.add_argument(
        "--cache-path",
        default="cache/blackout-dates-reservations.html",
        help="Path to cache HTML.",
    )
    args = parser.parse_args()

    html = fetch_blackout_reservations_html(
        read_mode=args.read_mode,
        cache_path=args.cache_path,
    )
    logger.info("Loaded %d bytes from blackout/reservations page.", len(html))


if __name__ == "__main__":
    main()

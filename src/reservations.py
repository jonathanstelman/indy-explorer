"""Reservation status parsing helpers."""

from __future__ import annotations

import argparse
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from cache_blackout_reservations import fetch_blackout_reservations_html

BASE_URL = "https://www.indyskipass.com"
DEFAULT_CACHE_PATH = "cache/blackout-dates-reservations.html"

RESERVATION_STATUS_REQUIRED = "Required"
RESERVATION_STATUS_OPTIONAL = "Optional"
RESERVATION_STATUS_NOT_REQUIRED = "Not Required"

RESERVATION_NAME_MAP = {
    "Berkshire East": "Berkshire East Mountain Resort",
    "Catamount": "Catamount Mountain Resort",
    "Detroit Mountain Recreation Area": "Detroit Mountain",
    "Greek Peak": "Greek Peak Mountain Resort",
    "Blacktail Mountain Ski Area": "Blacktail Mountain Resort",
}

logger = logging.getLogger(__name__)


def _clean_text(value: str) -> str:
    return value.replace("\xa0", " ").strip()


def _normalize_url(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    return urljoin(BASE_URL, href)


def _parse_link_list(list_node) -> List[Dict[str, Optional[str]]]:
    if not list_node:
        return []
    items = []
    for li in list_node.find_all("li"):
        anchor = li.find("a")
        name = _clean_text(anchor.get_text(strip=True)) if anchor else _clean_text(li.text)
        url = _normalize_url(anchor["href"]) if anchor and anchor.has_attr("href") else None
        if name:
            items.append({"name": name, "url": url})
    return items


def parse_reservations_page(html_content: str) -> Dict[str, List[Dict[str, Optional[str]]]]:
    """Parse the reservations section from the blackout/reservations page."""
    soup = BeautifulSoup(html_content, "html.parser")

    reservations_heading = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4")
        and _clean_text(tag.get_text(strip=True)).lower() == "reservations"
    )
    if not reservations_heading:
        return {"required": [], "optional": []}

    required_list = reservations_heading.find_next("ul")

    optional_heading = reservations_heading.find_next(
        lambda tag: tag.name in ("h3", "h4")
        and "voluntary" in _clean_text(tag.get_text(strip=True)).lower()
    )
    optional_list = optional_heading.find_next("ul") if optional_heading else None

    return {
        "required": _parse_link_list(required_list),
        "optional": _parse_link_list(optional_list),
    }


def normalize_reservation_name(name: str) -> str:
    """Map reservation list names to resorts.csv names when needed."""
    return RESERVATION_NAME_MAP.get(name, name)


def build_reservation_records(
    parsed_data: Dict[str, List[Dict[str, Optional[str]]]]
) -> List[Dict[str, Optional[str]]]:
    """Build reservation records with normalized resort names."""
    records: List[Dict[str, Optional[str]]] = []

    for entry in parsed_data.get("required", []):
        raw_name = entry.get("name")
        if not raw_name:
            continue
        records.append(
            {
                "name": normalize_reservation_name(raw_name),
                "reservation_status": RESERVATION_STATUS_REQUIRED,
                "reservation_url": entry.get("url"),
            }
        )

    for entry in parsed_data.get("optional", []):
        raw_name = entry.get("name")
        if not raw_name:
            continue
        name = normalize_reservation_name(raw_name)
        if any(record["name"] == name for record in records):
            continue
        records.append(
            {
                "name": name,
                "reservation_status": RESERVATION_STATUS_OPTIONAL,
                "reservation_url": entry.get("url"),
            }
        )

    return records


def build_reservation_map(
    parsed_data: Dict[str, List[Dict[str, Optional[str]]]]
) -> Dict[str, Dict[str, str]]:
    """Build a resort-name keyed map for merging into the resorts dataset."""
    reservation_map: Dict[str, Dict[str, Optional[str]]] = {}

    for entry in parsed_data.get("resorts", []):
        name = entry.get("name")
        if not name:
            continue
        reservation_map[name] = {
            "status": entry.get("reservation_status", RESERVATION_STATUS_NOT_REQUIRED),
            "url": entry.get("reservation_url"),
        }

    return reservation_map


def merge_reservations_into_resorts(resorts_df, reservation_map: Dict[str, Dict[str, str]]):
    """Merge reservation info into `resorts_df` (by `name` column)."""

    def _map_for_name(name: str):
        info = reservation_map.get(name)
        if not info:
            return RESERVATION_STATUS_NOT_REQUIRED, ""
        return info.get("status", RESERVATION_STATUS_NOT_REQUIRED), info.get("url", "")

    mapped = resorts_df["name"].apply(_map_for_name)
    resorts_df["reservation_status"] = mapped.apply(lambda t: t[0])
    resorts_df["reservation_url"] = mapped.apply(lambda t: t[1])

    missing_in_resorts = sorted(set(reservation_map.keys()) - set(resorts_df["name"]))
    if missing_in_resorts:
        logger.warning("Reservation resorts missing from resorts_df:")
        for name in missing_in_resorts:
            logger.warning("- %s", name)

    return resorts_df


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Parse Indy Pass reservation requirements.")
    parser.add_argument(
        "--read-mode",
        choices=["cache", "live"],
        default="cache",
        help="Use cached HTML or fetch live page (default: cache).",
    )
    parser.add_argument(
        "--cache-path",
        default=DEFAULT_CACHE_PATH,
        help="Path to cached blackout/reservations HTML.",
    )
    parser.add_argument(
        "--output-path",
        default="data/reservations_raw.json",
        help="Path to write parsed reservations JSON.",
    )
    args = parser.parse_args()

    html = fetch_blackout_reservations_html(
        read_mode=args.read_mode,
        cache_path=args.cache_path,
    )
    parsed = parse_reservations_page(html)
    records = build_reservation_records(parsed)
    with open(args.output_path, "w", encoding="utf-8") as json_file:
        json.dump({"resorts": records}, json_file, indent=2)
    required_count = sum(1 for record in records if record["reservation_status"] == "Required")
    optional_count = sum(1 for record in records if record["reservation_status"] == "Optional")
    logger.info(
        "Parsed %d required and %d optional reservations.",
        required_count,
        optional_count,
    )


if __name__ == "__main__":
    main()

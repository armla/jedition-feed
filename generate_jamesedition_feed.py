#!/usr/bin/env python3
"""Generate The Agency Costa Rica's curated JamesEdition ELITE XML feed.

Design rules:
- Independent from all other portals.
- Exclusive-first, then curated non-exclusive listings until the 50-listing cap.
- First 12 eligible portal images in source media order.
- Horizontal tour video first, then supplementary listing video fields.
- English SSR description extraction and authoritative coordinate-map enrichment.
- A run may only replace the public XML after complete validation succeeds.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

INVENTORY_URL = "https://api.lxcostarica.com/api/v1/listings"
COORDINATES_URL = "https://live.theagency.cr/api/public/coordinates"
BRANDED_PROPERTY_ROOT = "https://theagency.cr/property/"
MIN_PRICE_USD = 500_000
MAX_LISTINGS = 50
MAX_IMAGES = 12
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def clean(value: Any) -> str:
    return "" if value is None else " ".join(str(value).split())


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def first_value(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record and present(record[key]):
            return record[key]
    return None


def fetch_bytes(url: str, timeout: int = 55, attempts: int = 2) -> bytes:
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers=REQUEST_HEADERS)
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(2 * (attempt + 1))
    assert error is not None
    raise error


def fetch_json(url: str) -> Any:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def source_images(property_record: dict[str, Any]) -> list[str]:
    ordered: list[tuple[float, int, str]] = []
    for index, item in enumerate(property_record.get("media") or []):
        if not isinstance(item, dict) or item.get("isonportalfeed") is not True:
            continue
        url = first_value(item, "url", "image_url", "src", "full_url", "original_url")
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            continue
        order = numeric(item.get("sortonportalfeed"))
        ordered.append((order if order is not None else 9_999_999, index, url))
    ordered.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
    seen: set[str] = set()
    return [url for _, _, url in ordered if not (url in seen or seen.add(url))]


def normalise_video(value: Any) -> str | None:
    url = clean(value)
    if not url:
        return None
    if "youtube.com/embed/" in url:
        video_id = url.split("youtube.com/embed/", 1)[1].split("?", 1)[0].split("/", 1)[0]
        return f"https://www.youtube.com/watch?v={video_id}" if video_id else None
    return url


def source_videos(property_record: dict[str, Any], listing: dict[str, Any]) -> list[str]:
    # Horizontal/primary tour first, followed by other populated video fields.
    priority_fields = (
        property_record.get("virtual_tour_video_url"),
        listing.get("live_tour_url"),
        listing.get("vertical_video_1"),
        listing.get("vertical_video_2"),
    )
    videos: list[str] = []
    for raw in priority_fields:
        url = normalise_video(raw)
        if url and url not in videos:
            videos.append(url)
    return videos


def jamesedition_type(source_type: Any, property_type: Any) -> str | None:
    source = f"{clean(source_type)} {clean(property_type)}".lower()
    mapping = (
        ("private island", "Private island"), ("farm", "Farm ranch"), ("ranch", "Farm ranch"),
        ("finca", "Finca"), ("estate", "Estate"), ("chalet", "Chalet"),
        ("townhouse", "Townhouse"), ("bungalow", "Bungalow"), ("penthouse", "Penthouse"),
        ("co-op", "Co op"), ("co op", "Co op"), ("apartment", "Apartment"),
        ("land", "Land"), ("lot", "Land"), ("villa", "Villa"), ("house", "House"),
        ("single family", "House"), ("condominium", "Condo"), ("condo", "Condo"),
        ("residential", "House"),
    )
    for needle, target in mapping:
        if needle in source:
            return target
    return None


def priority_value(row: dict[str, Any]) -> int:
    value = numeric(row.get("priority"))
    return int(value) if value is not None else 99


def ordinary_rank(row: dict[str, Any]) -> tuple[Any, ...]:
    priority = priority_value(row)
    band = 0 if priority <= 2 else 1 if priority <= 4 else 2 if priority <= 10 else 3 if priority <= 17 else 4
    return (band, priority, 0 if row["featured"] else 1, -row["price"], row["reference"])


def candidate_rows(inventory: list[Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for property_record in inventory:
        if not isinstance(property_record, dict):
            continue
        images = source_images(property_record)
        for listing in property_record.get("listings") or []:
            if not isinstance(listing, dict):
                continue
            price = numeric(first_value(listing, "listingprice", "price"))
            country = clean(property_record.get("country") or listing.get("country"))
            listing_type = clean(first_value(listing, "listingtype", "listing_type", "type"))
            status = clean(listing.get("status"))
            source_property_type = clean(first_value(listing, "property_subtype", "propertytype") or first_value(property_record, "property_subtype", "propertytype"))
            property_type = jamesedition_type(source_property_type, first_value(listing, "propertytype") or property_record.get("propertytype"))
            reference = clean(first_value(listing, "lx_mls_id", "id", "reference", "permalink"))
            priority = first_value(listing, "priority") if present(listing.get("priority")) else property_record.get("priority")
            exclusive = bool(listing.get("exclusive_listing") if "exclusive_listing" in listing else property_record.get("exclusive_listing"))
            if not (
                listing_type.lower() == "sale"
                and status.lower() == "active"
                and listing.get("publish") is True
                and price is not None
                and price >= MIN_PRICE_USD
                and country.lower() in ("costa rica", "cr")
                and property_type
                and reference
            ):
                continue
            if any(word in source_property_type.lower() for word in ("commercial", "hotel", "restaurant", "store")):
                continue
            # Priority 18–20 are retained only when an exclusive record is explicitly marked as such.
            if not exclusive and (numeric(priority) or 99) >= 18:
                continue
            agent = listing.get("agent") if isinstance(listing.get("agent"), dict) else property_record.get("agent") if isinstance(property_record.get("agent"), dict) else {}
            permalink = clean(listing.get("permalink"))
            agent_email = clean(first_value(agent, "email"))
            if agent_email.lower() == "juliane@lxcostarica.com":
                agent_email = "juliane.maurach@theagencyre.com"
            records.append({
                "property_key": clean(first_value(property_record, "id", "property_id")) or reference,
                "reference": reference,
                "title": clean(first_value(listing, "name", "title_en", "title") or first_value(property_record, "title_en", "name", "title")),
                "price": price,
                "currency": clean(first_value(listing, "currency", "currency_code")) or "USD",
                "listing_type": listing_type.lower(),
                "status": status,
                "priority": clean(priority),
                "exclusive": exclusive,
                "featured": bool(listing.get("featured_property") if "featured_property" in listing else property_record.get("featured_property")),
                "property_type": property_type,
                "source_property_type": source_property_type,
                "country": "CR",
                "region": clean(property_record.get("state") or listing.get("state")),
                "city": clean(property_record.get("city") or listing.get("city")),
                "address": clean(property_record.get("address") or listing.get("address")),
                "bedrooms": numeric(property_record.get("bedrooms") or listing.get("bedrooms")),
                "bathrooms": numeric(first_value(property_record, "fullbathrooms", "bathrooms") or first_value(listing, "fullbathrooms", "bathrooms")),
                "living_area": numeric(first_value(property_record, "totalarea", "area_m2", "living_area") or first_value(listing, "totalarea", "area_m2", "living_area")),
                "land_area": numeric(first_value(property_record, "lotsize", "lot_size", "land_area") or first_value(listing, "lotsize", "lot_size", "land_area")),
                "images": images[:MAX_IMAGES],
                "videos": source_videos(property_record, listing),
                "permalink": permalink,
                "external_url": BRANDED_PROPERTY_ROOT + permalink.lstrip("/"),
                "agent_id": clean(first_value(agent, "id", "reference")) or "office",
                "agent_first_name": clean(first_value(agent, "firstname", "first_name")) or "The Agency",
                "agent_last_name": clean(first_value(agent, "lastname", "last_name")) or "Costa Rica",
                "agent_email": agent_email or "costaricateam@theagencyre.com",
                "agent_phone": clean(first_value(agent, "mobile", "phone")) or "+50685129333",
                "agent_photo": clean(first_value(agent, "image_url")),
                "last_modified": clean(first_value(listing, "lastmodifieddate") or property_record.get("lastmodifieddate")),
            })
    # One listing variant per property.
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["property_key"]].append(record)
    deduplicated = [sorted(group, key=ordinary_rank)[0] for group in grouped.values()]
    exclusives = sorted((row for row in deduplicated if row["exclusive"]), key=ordinary_rank)
    non_exclusives = sorted((row for row in deduplicated if not row["exclusive"]), key=ordinary_rank)
    return exclusives + non_exclusives


def extract_ssr_description(page: str) -> str | None:
    payload = html.unescape(page.replace('\\"', '"'))
    pointer = re.search(r'"description":"\$([0-9a-z]+)"', payload)
    if not pointer:
        return None
    marker = re.search(rf'{re.escape(pointer.group(1))}:T([0-9a-fA-F]+),', payload)
    if not marker:
        return None
    length = int(marker.group(1), 16)
    content = payload[marker.end():marker.end() + length]
    content = content.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    content = content.replace("\\u0026", "&").replace("\\u2013", "–").replace("\\u2014", "—").replace("\\u2019", "’")
    content = "\n\n".join(" ".join(paragraph.split()) for paragraph in content.split("\n\n") if paragraph.strip())
    if len(content) < 120 or "<script" in content or '"children"' in content:
        return None
    return content


def extract_ssr_coordinates(page: str) -> tuple[float | None, float | None]:
    payload = page.replace('\\"', '"')
    for pattern in (
        r'"lat":\s*(-?\d+(?:\.\d+)?),\s*"lng":\s*(-?\d+(?:\.\d+)?)',
        r'"latitude":"?(-?\d+(?:\.\d+)?)"?,\s*"longitude":"?(-?\d+(?:\.\d+)?)"?',
    ):
        found = re.search(pattern, payload)
        if found:
            return float(found.group(1)), float(found.group(2))
    return None, None


def enrich_candidate(row: dict[str, Any], coordinate_map: dict[str, Any], cache_entry: dict[str, Any] | None) -> dict[str, Any] | None:
    # Coordinates endpoint is authoritative. SSR is solely a fallback for a missing MLS key and English description.
    coordinate = coordinate_map.get(row["reference"], {}) if isinstance(coordinate_map, dict) else {}
    latitude = numeric(coordinate.get("lat")) if isinstance(coordinate, dict) else None
    longitude = numeric(coordinate.get("lon")) if isinstance(coordinate, dict) else None
    cache_matches = bool(
        isinstance(cache_entry, dict)
        and cache_entry.get("title") == row["title"]
        and cache_entry.get("last_modified") == row["last_modified"]
        and clean(cache_entry.get("description"))
    )
    if cache_matches:
        row["description"] = clean(cache_entry["description"])
        row["latitude"] = latitude if latitude is not None else numeric(cache_entry.get("latitude"))
        row["longitude"] = longitude if longitude is not None else numeric(cache_entry.get("longitude"))
        if row["latitude"] is not None and row["longitude"] is not None:
            return row
    try:
        page = fetch_bytes(row["external_url"], timeout=50).decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"WARN: description retrieval failed for {row['reference']}: {exc}", file=sys.stderr)
        return None
    description = extract_ssr_description(page)
    fallback_latitude, fallback_longitude = extract_ssr_coordinates(page)
    row["description"] = description
    row["latitude"] = latitude if latitude is not None else fallback_latitude
    row["longitude"] = longitude if longitude is not None else fallback_longitude
    if not description or row["latitude"] is None or row["longitude"] is None:
        print(f"WARN: excluding incomplete candidate {row['reference']}", file=sys.stderr)
        return None
    return row


def safe_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, quote(parts.path, safe="/%:@"), quote(parts.query, safe="=&%"), ""))


def text_element(parent: ET.Element, tag: str, value: Any, attrs: dict[str, str] | None = None) -> ET.Element:
    element = ET.SubElement(parent, tag, attrs or {})
    element.text = clean(value)
    return element


def build_xml(records: list[dict[str, Any]]) -> bytes:
    root = ET.Element("jamesedition_feed", {"version": "3.9"})
    agents_node = ET.SubElement(root, "agents")
    agents: dict[str, dict[str, Any]] = {}
    for row in records:
        agent_ref = f"tacr-agent-{row['agent_id']}"
        agents.setdefault(agent_ref, row)
    for agent_ref, row in sorted(agents.items()):
        agent = ET.SubElement(agents_node, "agent", {"reference": agent_ref})
        text_element(agent, "first_name", row["agent_first_name"])
        text_element(agent, "last_name", row["agent_last_name"])
        text_element(agent, "email", row["agent_email"])
        text_element(agent, "phone1", row["agent_phone"])
        if row["agent_photo"]:
            text_element(agent, "profile_picture_url", row["agent_photo"])
        text_element(agent, "language_codes", "eng,spa")
    adverts = ET.SubElement(root, "adverts")
    for row in records:
        advert = ET.SubElement(adverts, "advert", {"reference": row["reference"], "category": "real estate"})
        text_element(advert, "type", "sale")
        text_element(advert, "price", str(int(row["price"])), {"currency": row["currency"]})
        text_element(advert, "property_type", row["property_type"])
        text_element(advert, "title", row["title"])
        text_element(advert, "description", row["description"])
        location = ET.SubElement(advert, "location")
        text_element(location, "country", row["country"])
        if row["region"]:
            text_element(location, "region", row["region"])
        text_element(location, "city", row["city"])
        if row["address"]:
            text_element(location, "address", row["address"])
        text_element(location, "latitude", f"{row['latitude']:.6f}")
        text_element(location, "longitude", f"{row['longitude']:.6f}")
        text_element(advert, "hide_address", "yes")
        if row["bedrooms"] and row["bedrooms"] > 0:
            text_element(advert, "bedrooms", str(int(row["bedrooms"])))
        if row["bathrooms"] and row["bathrooms"] > 0:
            text_element(advert, "bathrooms", str(int(row["bathrooms"])))
        if row["living_area"] and row["living_area"] > 0:
            text_element(advert, "living_area", str(int(row["living_area"])), {"unit": "sqm"})
        if row["land_area"] and row["land_area"] > 0:
            text_element(advert, "land_area", str(int(row["land_area"])), {"unit": "sqm"})
        media = ET.SubElement(advert, "media")
        for image_url in row["images"]:
            image = ET.SubElement(media, "image")
            text_element(image, "image_url", safe_url(image_url))
        for video_url in row["videos"]:
            video = ET.SubElement(media, "video")
            text_element(video, "video_url", video_url)
        text_element(advert, "external_url", row["external_url"])
        text_element(advert, "agent_reference", f"tacr-agent-{row['agent_id']}")
    ET.indent(root, space="  ")
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n"


def validate_xml(xml_content: bytes) -> dict[str, int]:
    root = ET.fromstring(xml_content)
    adverts = root.findall("./adverts/advert")
    if len(adverts) != MAX_LISTINGS:
        raise ValueError(f"Expected exactly {MAX_LISTINGS} adverts; generated {len(adverts)}.")
    references: set[str] = set()
    videos = 0
    for advert in adverts:
        reference = advert.attrib.get("reference", "")
        if not reference or reference in references:
            raise ValueError(f"Missing or duplicate listing reference: {reference!r}")
        references.add(reference)
        required = ("type", "price", "property_type", "title", "description", "location/country", "location/city", "location/latitude", "location/longitude", "agent_reference")
        missing = [field for field in required if not clean(advert.findtext(field))]
        if missing:
            raise ValueError(f"{reference} is missing required fields: {', '.join(missing)}")
        if len(advert.findall("./media/image")) < 2:
            raise ValueError(f"{reference} has fewer than two images.")
        if len(advert.findall("./media/image")) > MAX_IMAGES:
            raise ValueError(f"{reference} exceeds the {MAX_IMAGES}-image limit.")
        latitude = float(advert.findtext("location/latitude", "nan"))
        longitude = float(advert.findtext("location/longitude", "nan"))
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError(f"{reference} has invalid coordinates.")
        videos += len(advert.findall("./media/video"))
    return {"adverts": len(adverts), "videos": videos}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Path to the public XML file.")
    parser.add_argument("--state", required=True, help="Path to non-sensitive generated feed metadata.")
    parser.add_argument("--cache", required=True, help="Path to the non-sensitive description enrichment cache.")
    args = parser.parse_args()
    output = Path(args.output)
    state_path = Path(args.state)
    cache_path = Path(args.cache)
    output.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    except (OSError, json.JSONDecodeError):
        cache = {}
    if not isinstance(cache, dict):
        cache = {}

    try:
        inventory = fetch_json(INVENTORY_URL)
        coordinates = fetch_json(COORDINATES_URL)
        if not isinstance(inventory, list) or not isinstance(coordinates, dict):
            raise ValueError("Unexpected source API response shape.")
    except Exception as exc:
        # Preserve the last known-good Pages file. A source failure must never publish an empty feed.
        print(f"SAFE EXIT: source unavailable or invalid: {exc}", file=sys.stderr)
        return 0

    candidates = candidate_rows(inventory)
    complete: list[dict[str, Any]] = []
    # The known first 50 candidates comprise the current published roster.  Do not fetch a broad
    # reserve universe nightly; that increases upstream load and compromises job-time reliability.
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {
            executor.submit(enrich_candidate, dict(row), coordinates, cache.get(row["reference"])): row
            for row in candidates[:MAX_LISTINGS]
        }
        for future in as_completed(future_map):
            enriched = future.result()
            if enriched is not None:
                complete.append(enriched)

    # Concurrent work must be returned to the deterministic exclusive-first rank before publishing.
    complete.sort(key=lambda row: (0 if row["exclusive"] else 1, ordinary_rank(row)))
    selected = complete[:MAX_LISTINGS]
    if len(selected) != MAX_LISTINGS:
        raise RuntimeError(f"Only {len(selected)} complete listings available; retained existing public feed.")

    xml_content = build_xml(selected)
    stats = validate_xml(xml_content)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=output.parent, prefix="feed-", suffix=".xml") as temp:
        temp.write(xml_content)
        temporary_name = temp.name
    os.replace(temporary_name, output)

    state = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_policy": "exclusive-first; $500,000 USD minimum; 50-listing cap",
        "reference_count": len(selected),
        "exclusive_count": sum(row["exclusive"] for row in selected),
        "nonexclusive_count": sum(not row["exclusive"] for row in selected),
        "videos": stats["videos"],
        "references": [row["reference"] for row in selected],
        "source_fingerprint": hashlib.sha256("|".join(f"{row['reference']}:{row['last_modified']}" for row in selected).encode()).hexdigest(),
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    next_cache = {
        row["reference"]: {
            "title": row["title"],
            "last_modified": row["last_modified"],
            "description": row["description"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
        for row in selected
    }
    cache_path.write_text(json.dumps(next_cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "published", **state}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

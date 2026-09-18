#!/usr/bin/env python3
"""Regression coverage for ELITE exclusion and portal activity identity."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

MODULE_PATH = Path(__file__).resolve().parents[1] / "generate_jamesedition_feed.py"
spec = importlib.util.spec_from_file_location("jamesedition_feed", MODULE_PATH)
assert spec and spec.loader
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)


def row(reference: str, *, exclusive: bool, priority: int) -> dict:
    return {
        "reference": reference,
        "title": f"Residence {reference}",
        "exclusive": exclusive,
        "priority": str(priority),
        "featured": False,
        "price": 2_000_000 - priority,
        "currency": "USD",
        "listing_type": "sale",
        "property_type": "Villa",
        "source_property_type": "House",
        "country": "CR",
        "address": "Private community",
        "community": "Private community",
        "city": "Tamarindo",
        "region": "Guanacaste",
        "region_description": "Tamarindo",
        "bedrooms": None,
        "bathrooms": None,
        "floors": None,
        "living_area": None,
        "land_area": None,
        "latitude": 10.300001,
        "longitude": -85.840001,
        "external_url": f"https://theagency.cr/property/{reference.lower()}",
        "description": "A complete English description long enough for a validated premium listing.",
        "images": ["https://images.example/1.jpg", "https://images.example/2.jpg"],
        "videos": [],
        "agent_id": "office",
        "agent_first_name": "The Agency",
        "agent_last_name": "Costa Rica",
        "agent_email": "costaricateam@theagencyre.com",
        "agent_phone": "+50685129333",
        "agent_photo": "",
        "last_modified": "2026-09-11T00:00:00Z",
    }


records = [
    row("ELITE-A", exclusive=True, priority=1),
    row("ELITE-B", exclusive=True, priority=2),
    row("PORTAL-A", exclusive=False, priority=5),
    row("PORTAL-B", exclusive=False, priority=5),
    row("PORTAL-C", exclusive=False, priority=6),
]
selected = feed.select_roster(records, 3, {"ELITE-A", "ELITE-B"})
assert [item["reference"] for item in selected] == ["PORTAL-A", "PORTAL-B", "PORTAL-C"]
assert not ({item["reference"] for item in selected} & {"ELITE-A", "ELITE-B"})

elite_payload = feed.activity_payload(row("LX001", exclusive=True, priority=1), "https://feed.example/elite.xml")
portal_payload = feed.activity_payload(row("LX001", exclusive=False, priority=5), "https://feed.example/portal.xml", "PORTAL")
assert elite_payload["publication_key"] == "JamesEdition:LX001"
assert portal_payload["publication_key"] == "JamesEdition:PORTAL:LX001"
assert portal_payload["feed_tier"] == "PORTAL"

posted: list[dict] = []

class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *_): return False


def success(request, timeout=15):
    posted.append(json.loads(request.data.decode("utf-8")))
    return Response()

with tempfile.TemporaryDirectory() as directory:
    state = Path(directory) / "activity.json"
    original = feed.urlopen
    try:
        feed.urlopen = success
        result = feed.sync_publication_activities(
            [row("PORTAL-A", exclusive=False, priority=5)],
            state,
            "https://hook.example",
            "https://feed.example/portal.xml",
            feed_label="PORTAL",
            mode="test",
            test_reference="PORTAL-A",
        )
    finally:
        feed.urlopen = original
    assert result == {"mode": "test", "queued": 1, "sent": 1, "failed": 0, "enabled": 1}
    assert posted[0]["publication_key"] == "JamesEdition:PORTAL:PORTAL-A"
    assert posted[0]["is_test"] is True
    assert not state.exists()

propertybase_rendition = "https://s3.amazonaws.com/propertybase-clients/org/property/media/1277x640/hero.jpg"
assert feed.canonical_image_url(propertybase_rendition) == "https://s3.amazonaws.com/propertybase-clients/org/property/media/hero.jpg"
assert feed.canonical_image_url("https://images.example/hero.jpg") == "https://images.example/hero.jpg"

property_record = {
    "virtual_tour_video_url": "https://www.youtube.com/embed/HORIZONTAL",
    "virtual_tour_url": "https://my.matterport.com/show/?m=VALID",
}
listing_record = {
    "live_tour_url": "https://www.youtube.com/embed/SECONDARY",
    "vertical_video_1": "https://www.youtube.com/embed/VERTICAL",
}
assert feed.source_videos(property_record, listing_record) == ["https://www.youtube.com/watch?v=HORIZONTAL"]
assert feed.source_virtual_tour(property_record, listing_record) == "https://my.matterport.com/show/?m=VALID"
assert feed.supported_virtual_tour_url("https://www.youtube.com/watch?v=VERTICAL") is None

media_row = row("MEDIA-001", exclusive=True, priority=1)
media_row.update({
    "videos": feed.source_videos(property_record, listing_record),
    "virtual_tour": feed.source_virtual_tour(property_record, listing_record),
})
xml = feed.build_xml([media_row])
assert feed.validate_xml(xml, 1) == {"adverts": 1, "videos": 1, "virtual_tours": 1}

assert feed.positive_integer("2", maximum=99) == 2
assert feed.positive_integer(2.5, maximum=99) is None
assert feed.positive_integer(100, maximum=99) is None
stories_property = {"Stories__c": 3}
stories_row = row("STORIES-001", exclusive=True, priority=1)
stories_row["floors"] = feed.positive_integer(stories_property["Stories__c"], maximum=99)
stories_xml = feed.build_xml([stories_row])
stories_advert = ET.fromstring(stories_xml).find("./adverts/advert")
assert stories_advert is not None and stories_advert.findtext("floors") == "3"
assert feed.validate_xml(stories_xml, 1) == {"adverts": 1, "videos": 0, "virtual_tours": 0}

stories_source = {
    "id": "PROPERTY-STORIES-001",
    "country": "Costa Rica",
    "Stories__c": 2,
    "media": [
        {"isonportalfeed": True, "sortonportalfeed": 1, "url": "https://images.example/first.jpg"},
        {"isonportalfeed": True, "sortonportalfeed": 2, "url": "https://images.example/second.jpg"},
    ],
    "listings": [{
        "lx_mls_id": "SOURCE-STORIES-001",
        "listingtype": "Sale",
        "status": "Active",
        "publish": True,
        "listingprice": 2_000_000,
        "priority": "1",
        "property_subtype": "House",
        "propertytype": "House",
        "name": "Stories mapping residence",
        "permalink": "stories-mapping-residence",
        "agent": {"id": "agent-1", "firstname": "The", "lastname": "Agency", "email": "team@example.test"},
    }],
}
assert feed.candidate_rows([stories_source])[0]["floors"] == 2

print("PASS: roster, activity identity, canonical images, compliant media, and Stories mapping verified.")

#!/usr/bin/env python3
"""Regression coverage for ELITE exclusion and portal activity identity."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

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
        "address": "Private community",
        "community": "Private community",
        "city": "Tamarindo",
        "region": "Guanacaste",
        "region_description": "Tamarindo",
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

print("PASS: portal roster excludes ELITE references and uses isolated activity identity.")

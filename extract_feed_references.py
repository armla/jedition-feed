#!/usr/bin/env python3
"""Extract unique JamesEdition advert references from a validated XML feed."""
from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to a JamesEdition XML feed.")
    parser.add_argument("--output", required=True, help="Path for newline-delimited MLS references.")
    parser.add_argument("--expected-count", type=int, required=True, help="Exact advertised record count expected in source feed.")
    args = parser.parse_args()

    root = ET.parse(args.input).getroot()
    if root.tag != "jamesedition_feed":
        raise ValueError("Source XML does not have a jamesedition_feed root.")
    references = [item.attrib.get("reference", "").strip() for item in root.findall("./adverts/advert")]
    if len(references) != args.expected_count:
        raise ValueError(f"Expected {args.expected_count} source adverts; found {len(references)}.")
    if not all(references) or len(set(references)) != len(references):
        raise ValueError("Source XML includes missing or duplicate advert references.")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sorted(references)) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

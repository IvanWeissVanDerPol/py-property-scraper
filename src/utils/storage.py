import json
from pathlib import Path
from typing import Iterator

from src.models.property import PropertyListing


def save_jsonl(listing: PropertyListing, output_dir: Path, source: str):
    output_dir = output_dir / source
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "listings.jsonl"
    with open(filepath, "a") as f:
        f.write(listing.model_dump_json() + "\n")


def load_jsonl(filepath: Path) -> Iterator[PropertyListing]:
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                yield PropertyListing.model_validate_json(line)


def deduplicate(filepath: Path) -> list[PropertyListing]:
    seen = {}
    for listing in load_jsonl(filepath):
        key = listing.source_url
        if key not in seen or listing.scraped_at > seen[key].scraped_at:
            seen[key] = listing
    return list(seen.values())

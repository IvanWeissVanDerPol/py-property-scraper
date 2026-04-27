import json
from pathlib import Path
from datetime import datetime
from collections import Counter

SOURCE_COLORS = {
    "clasipar": "🟧",
    "infocasas": "🔵",
    "inmueblespy": "🟢",
    "propiedadesya": "🟣",
    "buscocasita": "🟡",
    "agentiz": "⚪",
}

SOURCE_WEIGHTS = {
    "infocasas": 5,
    "clasipar": 4,
    "inmueblespy": 3,
    "propiedadesya": 2,
    "buscocasita": 1,
}

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_all() -> list[dict]:
    """Load all listings from all sources into a single list."""
    all_listings = []
    for source_dir in sorted(DATA_DIR.iterdir()):
        if not source_dir.is_dir() or source_dir.name.startswith("_"):
            continue
        clean_path = source_dir / "cleaned.jsonl"
        raw_path = source_dir / "listings.jsonl"
        path = clean_path if clean_path.exists() else raw_path
        if path.exists():
            with open(path) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        all_listings.append(json.loads(line))
    return all_listings


def merge_by_url(listings: list[dict]) -> list[dict]:
    """Merge listings with the same source_url, keeping the richest entry."""
    # Group by normalized URL
    groups = {}
    for d in listings:
        url = d.get("source_url", "")
        key = url.rstrip("/").lower()
        groups.setdefault(key, []).append(d)

    merged = []
    for key, group in groups.items():
        if len(group) == 1:
            merged.append(group[0])
            continue
        # Merge: take the entry from the highest-weighted source
        group.sort(key=lambda x: SOURCE_WEIGHTS.get(x.get("source", ""), 0), reverse=True)
        best = dict(group[0])
        for other in group[1:]:
            for field in best:
                if not best[field] and other.get(field):
                    best[field] = other[field]
        merged.append(best)
    return merged


def generate_catalog(listings: list[dict]) -> dict:
    """Generate a structured catalog of all data."""
    cities = Counter()
    types = Counter()
    sources = Counter()
    price_range_pyg = []
    price_range_usd = []
    with_coords = 0
    with_images = 0
    with_beds = 0

    for d in listings:
        city = d.get("city", "") or ""
        if city:
            cities[city] += 1
        ptype = d.get("property_type", "") or ""
        if ptype:
            types[ptype] += 1
        sources[d.get("source", "")] += 1
        if d.get("price") and d["price"] > 1000:
            price_range_pyg.append(d["price"])
        if d.get("price_usd") and d["price_usd"] > 10:
            price_range_usd.append(d["price_usd"])
        if d.get("coordinates"):
            with_coords += 1
        if d.get("images"):
            with_images += 1
        if d.get("bedrooms") is not None:
            with_beds += 1

    return {
        "total": len(listings),
        "by_source": dict(sources.most_common()),
        "by_type": dict(types.most_common()),
        "top_cities": dict(cities.most_common(20)),
        "price_stats": {
            "pyg": {"count": len(price_range_pyg), "min": min(price_range_pyg) if price_range_pyg else 0,
                    "max": max(price_range_pyg) if price_range_pyg else 0},
            "usd": {"count": len(price_range_usd), "min": min(price_range_usd) if price_range_usd else 0,
                    "max": max(price_range_usd) if price_range_usd else 0},
        },
        "coverage": {
            "gps_coordinates": with_coords,
            "images": with_images,
            "bedrooms": with_beds,
        },
    }


def export_merged_jsonl(output_path: Path):
    """Merge all sources and export unified dataset."""
    all_listings = load_all()
    merged = merge_by_url(all_listings)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for d in merged:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"Merged {len(all_listings)} raw → {len(merged)} unique listings to {output_path}")
    return merged


def export_csv(output_path: Path):
    """Export unified data as CSV for spreadsheet/analysis."""
    import csv
    all_listings = load_all()
    merged = merge_by_url(all_listings)
    if not merged:
        return

    fields = [
        "source", "title", "property_type", "price", "price_usd", "currency",
        "city", "district", "zone", "bedrooms", "bathrooms",
        "total_area_m2", "built_area_m2", "latitude", "longitude",
        "description", "listing_date", "agency", "source_url",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for d in merged:
            row = dict(d)
            coords = d.get("coordinates")
            if coords and len(coords) == 2:
                row["latitude"] = coords[0]
                row["longitude"] = coords[1]
            row["listing_date"] = str(row.get("listing_date", "")) if row.get("listing_date") else ""
            writer.writerow(row)
    print(f"Exported {len(merged)} listings to {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["catalog", "merge", "csv"], default="catalog")
    args = parser.parse_args()

    if args.action == "catalog":
        listings = load_all()
        cat = generate_catalog(listings)
        print("=" * 60)
        print(f"  PARAGUAY PROPERTY CATALOG")
        print(f"  Total listings: {cat['total']:,}")
        print("=" * 60)
        print(f"\n  By source:")
        for src, count in cat["by_source"].items():
            emoji = SOURCE_COLORS.get(src, "❓")
            print(f"    {emoji} {src:15s} {count:5d}")
        print(f"\n  By property type:")
        for ptype, count in cat["by_type"].items():
            print(f"    {ptype:20s} {count:5d}")
        print(f"\n  Top cities:")
        for city, count in cat["top_cities"].items():
            print(f"    {city:25s} {count:5d}")
        print(f"\n  Price ranges:")
        ps = cat["price_stats"]
        print(f"    PYG: {ps['pyg']['count']:,} listings  ({ps['pyg']['min']:,.0f} - {ps['pyg']['max']:,.0f})")
        print(f"    USD: {ps['usd']['count']:,} listings  (${ps['usd']['min']:,.0f} - ${ps['usd']['max']:,.0f})")
        print(f"\n  Coverage:")
        for field, count in cat["coverage"].items():
            print(f"    with {field}: {count:,} ({count*100//max(cat['total'],1)}%)")

    elif args.action == "merge":
        export_merged_jsonl(DATA_DIR / "_merged" / "listings.jsonl")

    elif args.action == "csv":
        export_csv(DATA_DIR / "_merged" / "listings.csv")

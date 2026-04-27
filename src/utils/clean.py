import json
import re
from pathlib import Path
from collections import defaultdict


TEXT_FIELDS = {"title", "description", "city", "district", "zone", "address"}

PROPERTY_TYPE_MAP = {
    "officina": "oficina",
    "galpón": "galpon",
    "galpon": "galpon",
    "ph": "ph",
    "casa": "casa",
    "casa ": "casa",
    "departamento": "departamento",
    "terreno": "terreno",
    "local": "local",
    "oficina": "oficina",
    "quinta": "quinta",
}


def _strip_html(text):
    if not text or not isinstance(text, str):
        return text
    text = re.sub(r'<span\s+style="font-size:\s*0[^>]*>.*?</span>', "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    return text


def _strip_weird_chars(text):
    if not text or not isinstance(text, str):
        return text
    text = re.sub(r"[\u200b-\u200f\u2028-\u202f\u2060-\u2064\ufeff]", "", text)
    text = text.strip()
    return text


def _normalize_city(val):
    if not val or not isinstance(val, str):
        return val
    val = val.strip().title()
    return val


def clean_listing(d):
    original = dict(d)
    issues = defaultdict(int)

    # Strip HTML from all text fields
    for field in TEXT_FIELDS:
        if field in d and isinstance(d[field], str):
            cleaned = _strip_html(d[field])
            cleaned = _strip_weird_chars(cleaned)
            if cleaned != d.get(field):
                issues[f"html_stripped_{field}"] += 1
            # If after HTML removal the field still looks like HTML/page content, null it
            if re.search(r'(?:og:description|meta\s+property|content=|class=|href=)', cleaned, re.IGNORECASE):
                d[field] = None
                issues[f"html_remnant_{field}"] += 1
            else:
                d[field] = cleaned

    # Strip whitespace from all string fields
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = v.strip()
            d[k] = _strip_weird_chars(d[k])

    # Sanity-check bedrooms
    bedrooms = d.get("bedrooms")
    if bedrooms is not None and isinstance(bedrooms, (int, float)):
        if bedrooms > 20:
            d["bedrooms"] = None
            issues["bedrooms_too_high"] += 1

    # Sanity-check bathrooms
    bathrooms = d.get("bathrooms")
    if bathrooms is not None and isinstance(bathrooms, (int, float)):
        if bathrooms > 15:
            d["bathrooms"] = None
            issues["bathrooms_too_high"] += 1

    # Sanity-check price PYG
    price = d.get("price")
    if price is not None and isinstance(price, (int, float)):
        if 0 < price < 1000:
            d["price"] = None
            issues["price_pyg_too_low"] += 1

    # Sanity-check price USD
    price_usd = d.get("price_usd")
    if price_usd is not None and isinstance(price_usd, (int, float)):
        if price_usd > 10_000_000:
            d["price_usd"] = None
            issues["price_usd_too_high"] += 1

    # Sanity-check total_area_m2
    total_area = d.get("total_area_m2")
    if total_area is not None and isinstance(total_area, (int, float)):
        if total_area > 1_000_000:
            d["total_area_m2"] = None
            issues["total_area_too_high"] += 1

    # Sanity-check built_area_m2
    built_area = d.get("built_area_m2")
    if built_area is not None and isinstance(built_area, (int, float)):
        if built_area > 100_000:
            d["built_area_m2"] = None
            issues["built_area_too_high"] += 1

    # Normalize city names
    city = d.get("city")
    if city and isinstance(city, str):
        normalized = _normalize_city(city)
        if normalized != city:
            issues["city_normalized"] += 1
        d["city"] = normalized

    # Normalize property_type
    ptype = d.get("property_type")
    if ptype and isinstance(ptype, str):
        ptype_lower = ptype.strip().lower()
        mapped = PROPERTY_TYPE_MAP.get(ptype_lower, ptype_lower)
        if mapped != ptype:
            issues["property_type_normalized"] += 1
        d["property_type"] = mapped

    # Fill empty title from description
    title = d.get("title", "") or ""
    desc = d.get("description", "") or ""
    if not title.strip() and desc.strip():
        d["title"] = desc.strip()[:80]
        issues["title_filled_from_description"] += 1

    # Ensure currency field
    price = d.get("price")
    price_usd = d.get("price_usd")
    currency = d.get("currency")
    if currency not in ("PYG", "USD"):
        if price and price_usd:
            d["currency"] = "PYG"
        elif price_usd and not price:
            d["currency"] = "USD"
        elif price and not price_usd:
            d["currency"] = "PYG"
        issues["currency_fixed"] += 1

    # Set bedrooms/bathrooms to None for land (zero means absent)
    ptype = d.get("property_type", "")
    if ptype in ("terreno", "terreno "):
        if d.get("bedrooms") == 0:
            d["bedrooms"] = None
            issues["bedrooms_zero_to_none"] += 1
        if d.get("bathrooms") == 0:
            d["bathrooms"] = None
            issues["bathrooms_zero_to_none"] += 1

    d["_issues"] = dict(issues)
    return d


def generate_quality_report(listings, original_count):
    total_issues = defaultdict(int)
    issues_by_source = defaultdict(lambda: defaultdict(int))

    for d in listings:
        src = d.get("source", "unknown")
        for issue_type, count in d.get("_issues", {}).items():
            total_issues[issue_type] += count
            issues_by_source[src][issue_type] += count

    return {
        "total_input": original_count,
        "total_output": len(listings),
        "issues_fixed_by_type": dict(total_issues),
        "issues_by_source": {k: dict(v) for k, v in issues_by_source.items()},
    }


def print_report(report):
    sep = "=" * 50
    print(sep)
    print(f"  CLEANING QUALITY REPORT")
    print(f"  Input:  {report['total_input']} listings")
    print(f"  Output: {report['total_output']} listings")
    print(sep)

    total_fixes = sum(report["issues_fixed_by_type"].values())
    print(f"\n  Total issues fixed: {total_fixes}")
    if report["issues_fixed_by_type"]:
        print(f"\n  By issue type:")
        for issue, count in sorted(report["issues_fixed_by_type"].items(), key=lambda x: -x[1]):
            print(f"    {issue:40s} {count:5d}")

    if report["issues_by_source"]:
        print(f"\n  By source:")
        for src, issues in sorted(report["issues_by_source"].items()):
            src_total = sum(issues.values())
            print(f"    {src:20s} {src_total:5d} issues")
            for issue, count in sorted(issues.items(), key=lambda x: -x[1]):
                print(f"      {issue:38s} {count:4d}")
    print()


def clean_all(input_dir):
    files = sorted(Path(input_dir).rglob("listings.jsonl"))
    all_raw = []
    all_cleaned_with_issues = []
    original_count = 0

    for f in files:
        source = f.parent.name
        listings = []
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    listings.append(json.loads(line))
                    original_count += 1

        cleaned = [clean_listing(d) for d in listings]

        out_dir = f.parent
        out_path = out_dir / "cleaned.jsonl"
        with open(out_path, "w") as fh:
            for d in cleaned:
                d_copy = {k: v for k, v in d.items() if k != "_issues"}
                fh.write(json.dumps(d_copy, ensure_ascii=False) + "\n")

        print(f"  Cleaned {source:20s} {len(listings):5d} → {len(cleaned):5d} -> {out_path}")
        all_raw.extend(listings)
        all_cleaned_with_issues.extend(cleaned)

    report = generate_quality_report(all_cleaned_with_issues, original_count)
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", nargs="?", default=str(Path(__file__).parent.parent.parent / "data"))
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    report = clean_all(input_dir)
    print_report(report)

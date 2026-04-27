import re
from datetime import datetime

from playwright.sync_api import sync_playwright

from config.settings import DATA_DIR
from src.models.property import PropertyListing
from src.utils.storage import save_jsonl

BASE_URL = "https://omnimls.com"

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['es-PY', 'es', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
"""

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

_RE_BEDS = re.compile(r"(\d+)\s*Beds?")
_RE_BATHS = re.compile(r"(\d+)\s*Toilets?")
_RE_PARKING = re.compile(r"(\d+)\s*Parking")
_RE_LAND = re.compile(r"([\d,]+)\s*m²\s*Land")
_RE_BUILT = re.compile(r"(?:•|\s)([\d,]+)\s*m²\s*Construction\s*Size")
_RE_PRICE_USD = re.compile(r"\$([\d,]+)\s*USD")
_RE_PRICE_PYG = re.compile(r"PYG\s*([\d,]+)")


def _parse_area_text(text: str) -> tuple[float | None, float | None]:
    total = None
    built = None
    m_land = _RE_LAND.search(text)
    if m_land:
        total = float(m_land.group(1).replace(",", ""))
    m_built = _RE_BUILT.search(text)
    if m_built:
        built = float(m_built.group(1).replace(",", ""))
    return total, built


def _parse_details_text(text: str) -> dict:
    parsed: dict = {}
    m_beds = _RE_BEDS.search(text)
    if m_beds:
        parsed["bedrooms"] = int(m_beds.group(1))
    m_baths = _RE_BATHS.search(text)
    if m_baths:
        parsed["bathrooms"] = int(m_baths.group(1))
    m_parking = _RE_PARKING.search(text)
    if m_parking:
        parsed["parking_spots"] = int(m_parking.group(1))
    features = []
    if "Pets" in text:
        features.append("pets")
    if "Pool" in text:
        features.append("pool")
    if features:
        parsed["features"] = features
    return parsed


def _parse_price_line(text: str) -> tuple[float | None, float | None, str]:
    text = text.strip()
    if not text or text.lower().startswith("ask for price"):
        return None, None, "USD"
    m_usd = _RE_PRICE_USD.search(text)
    if m_usd:
        return None, float(m_usd.group(1).replace(",", "")), "USD"
    m_pyg = _RE_PRICE_PYG.search(text)
    if m_pyg:
        return float(m_pyg.group(1).replace(",", "")), None, "PYG"
    return None, None, "USD"


def _parse_address(text: str) -> dict:
    parts = [p.strip() for p in text.rsplit(",", 2)]
    if len(parts) == 3:
        return {"address": parts[0], "district": parts[1], "city": parts[2]}
    elif len(parts) == 2:
        return {"address": None, "district": parts[0], "city": parts[1]}
    return {"address": None, "district": None, "city": None}


def _parse_listing_block(lines: list[str]) -> dict | None:
    if len(lines) < 3:
        return None

    title = lines[0]
    address_text = lines[1]
    area_line = lines[2]

    loc = _parse_address(address_text)
    total_area, built_area = _parse_area_text(area_line)

    result = {
        "title": title,
        "source_url": "",
        "price_usd": None,
        "price_pyg": None,
        "currency": "USD",
        "property_type": "casa",
        "city": loc.get("city"),
        "district": loc.get("district"),
        "address": loc.get("address"),
        "bedrooms": None,
        "bathrooms": None,
        "parking_spots": None,
        "total_area_m2": total_area,
        "built_area_m2": built_area,
        "features": [],
        "has_video": False,
    }

    rest = lines[3:]
    details_found = False
    price_found = False

    for line in rest:
        stripped = line.strip()

        has_beds = _RE_BEDS.search(stripped)
        has_baths = _RE_BATHS.search(stripped)
        has_parking = _RE_PARKING.search(stripped)
        has_pets = "Pets" in stripped
        has_pool = "Pool" in stripped

        if has_beds or has_baths or has_parking or has_pets or has_pool:
            if not details_found:
                parsed = _parse_details_text(stripped)
                result["bedrooms"] = parsed.get("bedrooms")
                result["bathrooms"] = parsed.get("bathrooms")
                result["parking_spots"] = parsed.get("parking_spots")
                if "features" in parsed:
                    result["features"] = parsed["features"]
                details_found = True
                continue

        if "$" in stripped or stripped.startswith("PYG") or stripped.lower().startswith("ask for price"):
            if not price_found:
                pyg, usd, currency = _parse_price_line(stripped)
                result["price_pyg"] = pyg
                result["price_usd"] = usd
                result["currency"] = currency
                price_found = True
                continue

        if stripped.lower() == "video":
            result["has_video"] = True

        if stripped == "Pets" and "pets" not in result["features"]:
            result["features"].append("pets")
        if stripped == "Pool" and "pool" not in result["features"]:
            result["features"].append("pool")

    return result


def _extract_listings_from_text(text: str) -> list[dict]:
    blocks = text.split("House for sale\n")
    listings = []

    for block_str in blocks[1:]:
        lines = block_str.split("\n")
        lines = [l.strip() for l in lines if l.strip()]

        filtered = []
        for l in lines:
            if re.match(r"^\d+/\d+$", l):
                continue
            if l.lower() in ("previous", "next", "view"):
                continue
            filtered.append(l)

        listing = _parse_listing_block(filtered)
        if listing and listing["title"]:
            listings.append(listing)

    return listings


def run(max_pages: int = 15):
    output_dir = DATA_DIR / "omnimls"
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    seen_urls: set = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1920, "height": 1080},
            locale="es-PY",
        )
        context.add_init_script(STEALTH_JS)
        page = context.new_page()

        for page_num in range(1, max_pages + 1):
            if page_num == 1:
                url = f"{BASE_URL}/v/results/type_house/listing-type_sale/in-country_paraguay"
            else:
                url = f"{BASE_URL}/v/results/type_house/listing-type_sale/in-country_paraguay/page_{page_num}"

            print(f"  Page {page_num}: {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  Page {page_num}: timeout/nav error: {e}")
                page.wait_for_timeout(5000)

            body_text = page.locator("body").inner_text()

            listings = _extract_listings_from_text(body_text)

            if not listings:
                print(f"  Page {page_num}: no listings found, stopping.")
                break

            detail_links = page.locator("a[href^='/listing/']")
            seen_detail = set()
            detail_urls = []
            for ci in range(detail_links.count()):
                try:
                    href = detail_links.nth(ci).get_attribute("href") or ""
                    full = BASE_URL + href
                    if full not in seen_detail:
                        seen_detail.add(full)
                        detail_urls.append(full)
                except Exception:
                    pass

            for i, listing_data in enumerate(listings):
                url_for_listing = (
                    detail_urls[i] if i < len(detail_urls)
                    else f"{url}#{listing_data['title'][:40]}"
                )
                if url_for_listing in seen_urls:
                    continue
                seen_urls.add(url_for_listing)
                listing_data["source_url"] = url_for_listing

                listing = PropertyListing(
                    source="omnimls",
                    source_url=listing_data["source_url"],
                    title=listing_data["title"],
                    property_type=listing_data["property_type"],
                    price=listing_data.get("price_pyg"),
                    price_usd=listing_data.get("price_usd"),
                    currency=listing_data.get("currency", "USD"),
                    city=listing_data.get("city"),
                    district=listing_data.get("district"),
                    address=listing_data.get("address"),
                    bedrooms=listing_data.get("bedrooms"),
                    bathrooms=listing_data.get("bathrooms"),
                    parking_spots=listing_data.get("parking_spots"),
                    total_area_m2=listing_data.get("total_area_m2"),
                    built_area_m2=listing_data.get("built_area_m2"),
                    features=listing_data.get("features", []),
                    scraped_at=datetime.now(),
                )
                save_jsonl(listing, DATA_DIR, "omnimls")
                total += 1

            print(f"  Page {page_num}: {len(listings)} listings, {total} unique so far")

        browser.close()

    print(f"\nOmniMLS done. Total: {total} listings")

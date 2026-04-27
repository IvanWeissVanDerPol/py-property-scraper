import re
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright

from config.settings import DATA_DIR
from src.models.property import PropertyListing
from src.utils.storage import save_jsonl

BASE_URL = "https://www.remax.com.py"

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['es-PY', 'es', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
"""

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

_NUM_SEQ_RE = re.compile(r"^(\d+)\s+(\d+)\s+(\d+)\s+([\d,]+)$")
_PROPERTY_TYPES = [
    "Casa", "Departamento", "Terreno", "Duplex", "Local Comercial",
    "Oficina", "Penthouse", "Country", "Finca", "Galpon",
    "Cochera", "Edificio", "Hotel", "Casa Rural", "Casa de Campo",
    "Chalet", "Bunker", "Piso", "Estudio", "Loft",
]


def parse_price(text: str) -> tuple[float | None, float | None, str, str | None]:
    text = text.strip().replace("\u00a0", " ")
    listing_type = None
    if not text:
        return None, None, "PYG", None
    listing_type = "rental" if "mensual" in text.lower() else "sale"
    text_clean = re.sub(r"\s*Mensual.*", "", text, flags=re.IGNORECASE).strip()
    text_clean = re.sub(r"\s*mes.*", "", text_clean, flags=re.IGNORECASE).strip()
    if text_clean.endswith("$"):
        num_str = text_clean[:-1].strip()
        currency = "USD"
    elif text_clean.startswith("$"):
        num_str = text_clean[1:].strip()
        currency = "USD"
    elif text_clean.endswith("\u20b2") or text_clean.endswith("Gs."):
        num_str = text_clean.replace("\u20b2", "").replace("Gs.", "").strip()
        currency = "PYG"
    elif "\u20b2" in text_clean:
        num_str = text_clean.replace("\u20b2", "").strip()
        currency = "PYG"
    else:
        num_str = text_clean
        currency = "PYG"
    num_str = num_str.replace(".", "").replace(",", "").strip()
    try:
        val = float(num_str)
    except ValueError:
        return None, None, currency, listing_type
    if currency == "USD":
        return None, val, currency, listing_type
    return val, None, currency, listing_type


def parse_number_sequence(text: str) -> dict:
    m = _NUM_SEQ_RE.match(text.strip())
    if not m:
        return {}
    return {
        "bedrooms": int(m.group(1)),
        "bathrooms": int(m.group(2)),
        "parking_spots": int(m.group(3)),
        "total_area_m2": float(m.group(4).replace(",", "")),
    }


def parse_location(text: str) -> dict:
    if not text:
        return {"city": None, "district": None}
    parts = [p.strip() for p in text.split(",")]
    parts = [p for p in parts if p.lower() != "paraguay"]
    if len(parts) >= 2:
        return {"city": parts[0], "district": parts[1]}
    if len(parts) == 1:
        return {"city": parts[0], "district": None}
    return {"city": None, "district": None}


def get_url(card) -> str | None:
    link = card.query_selector("a[href*='/es-py/propiedades/']")
    if link:
        href = link.get_attribute("href") or ""
        if href.startswith("/"):
            return BASE_URL + href
        return href
    link = card.query_selector("a[href]")
    if link:
        href = link.get_attribute("href") or ""
        if href.startswith("/") and "propiedades" in href:
            return BASE_URL + href
        if href.startswith("http"):
            return href
    return None


def parse_listing_card(card) -> dict | None:
    text = card.inner_text().strip()
    if not text:
        return None
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    source_url = get_url(card)
    result = {
        "source": "remax",
        "source_url": source_url or "",
        "title": "",
        "price_pyg": None,
        "price_usd": None,
        "currency": "PYG",
        "listing_type": None,
        "property_type": None,
        "city": None,
        "district": None,
        "bedrooms": None,
        "bathrooms": None,
        "parking_spots": None,
        "total_area_m2": None,
        "description": "",
    }
    price_candidates = []
    for line in lines:
        if "$" in line or "\u20b2" in line or "Gs." in line:
            pyg, usd, currency, lst_type = parse_price(line)
            if pyg is not None or usd is not None:
                price_candidates.append((line, pyg, usd, currency, lst_type))
        for pt in _PROPERTY_TYPES:
            if line.lower().startswith(pt.lower()) or line == pt:
                result["property_type"] = pt.lower()
                break
    if price_candidates:
        _, pyg, usd, currency, lst_type = price_candidates[0]
        result["price_pyg"] = pyg
        result["price_usd"] = usd
        result["currency"] = currency
        result["listing_type"] = lst_type
    for line in lines:
        if "$" in line or "\u20b2" in line or "Gs." in line:
            continue
        parsed_seq = parse_number_sequence(line)
        if parsed_seq:
            result.update(parsed_seq)
            break
    for line in lines:
        if "Paraguay" in line or ("," in line and not line.startswith("http") and not line.startswith("/")):
            loc = parse_location(line)
            if loc["city"] or loc["district"]:
                result["city"] = loc["city"]
                result["district"] = loc["district"]
                break
    title_candidates = []
    for line in lines:
        is_price = "$" in line or "\u20b2" in line or "Gs." in line
        is_seq = bool(_NUM_SEQ_RE.match(line.strip()))
        is_location = "Paraguay" in line or ("," in line and len(line) < 80)
        if not is_price and not is_seq and not is_location and len(line) > 10:
            title_candidates.append(line)
    if title_candidates:
        result["title"] = min(title_candidates, key=len)
        remaining = [l for l in title_candidates if l != result["title"]]
        result["description"] = " | ".join(remaining[:3])
    return result


def _to_property_listing(data: dict) -> PropertyListing:
    return PropertyListing(
        source=data["source"],
        source_url=data["source_url"],
        title=data["title"],
        property_type=data.get("property_type") or "otro",
        price=data["price_pyg"] if data["currency"] == "PYG" else data["price_usd"],
        price_usd=data.get("price_usd"),
        currency=data.get("currency") or "PYG",
        city=data.get("city"),
        district=data.get("district"),
        bedrooms=data.get("bedrooms"),
        bathrooms=data.get("bathrooms"),
        total_area_m2=data.get("total_area_m2"),
        parking_spots=data.get("parking_spots"),
        description=data.get("description") or "",
        scraped_at=datetime.now(),
    )


def get_listing_cards(page) -> list:
    cards = page.query_selector_all("div[class*=card]")
    if not cards:
        cards = page.query_selector_all("a[href*='/es-py/propiedades/']")
        if cards:
            return cards
    if not cards:
        cards = page.query_selector_all("article")
    if not cards:
        cards = page.query_selector_all("div[class*=listing]")
    return cards


def run(max_pages: int = 10):
    output_dir = DATA_DIR / "remax"
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "listings.jsonl"
    total = 0
    seen_urls = set()
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
            page_url = f"{BASE_URL}/listings" if page_num == 1 else f"{BASE_URL}/listings?page={page_num}"
            print(f"Page {page_num}: {page_url}")
            try:
                page.goto(page_url, wait_until="networkidle", timeout=45000)
            except Exception as e:
                print(f"  Nav error on page {page_num}: {e}")
                page.wait_for_timeout(8000)
            page.wait_for_timeout(5000)
            body_text = page.inner_text("body")
            cards = get_listing_cards(page)
            if not cards or len(cards) < 2:
                print(f"  No listing cards on page {page_num}. Body: {len(body_text)} chars.")
                property_links = page.query_selector_all("a[href*='/es-py/propiedades/']")
                if property_links:
                    print(f"  Found {len(property_links)} property links")
                    cards = property_links
                else:
                    print(f"  No property links either. Stopping.")
                    break
            page_listings = 0
            for card in cards:
                try:
                    data = parse_listing_card(card)
                    if data and data["source_url"] and data["source_url"] not in seen_urls:
                        seen_urls.add(data["source_url"])
                        listing = _to_property_listing(data)
                        save_jsonl(listing, DATA_DIR, "remax")
                        page_listings += 1
                        total += 1
                except Exception:
                    continue
            print(f"  Page {page_num}: {page_listings} new listings (total: {total})")
            if page_listings == 0 and page_num > 1:
                print("  No new listings on consecutive page, stopping.")
                break
            page.wait_for_timeout(1500)
        browser.close()
    print(f"\nRE/MAX done. Total: {total} listings -> {filepath}")


if __name__ == "__main__":
    run(max_pages=5)

import re
import json
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright

from config.settings import DATA_DIR
from src.models.property import PropertyListing
from src.utils.storage import save_jsonl

CATEGORIES = [
    ("casa", "venta"),
    ("lotes", ""),
    ("apartamento", "venta"),
    ("otros", ""),
    ("oficina", ""),
    ("fincas", ""),
]

TYPE_MAP = {
    "casa": "casa",
    "lotes": "terreno",
    "apartamento": "departamento",
    "otros": "otro",
    "oficina": "local",
    "fincas": "country",
}

BASE_URL = "https://inmuebles.mercadolibre.com.py"

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['es-PY', 'es', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
"""

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def parse_price(text: str) -> tuple[float | None, float | None, str]:
    text = text.strip()
    if not text:
        return None, None, "PYG"
    if text.startswith("US$"):
        num = text.replace("US$", "").strip().replace(".", "")
        try:
            usd = float(num)
        except ValueError:
            usd = None
        return None, usd, "USD"
    if text.startswith("\u20b2"):
        num = text.replace("\u20b2", "").strip().replace(".", "")
        try:
            pyg = float(num)
        except ValueError:
            pyg = None
        return pyg, None, "PYG"
    num = text.replace(".", "")
    try:
        val = float(num)
    except ValueError:
        return None, None, "PYG"
    return val, None, "PYG"


_DETAIL_PATTERNS = [
    (r"(\d+)\s*dormitorios?", "bedrooms"),
    (r"(\d+)\s*ba\u00f1os?", "bathrooms"),
    (r"(\d+(?:\.?\d+)?)\s*m\u00b2\s*cubiertos?", "built_area_m2"),
    (r"(\d+(?:\.?\d+)?)\s*m\u00b2\s*totales?", "total_area_m2"),
    (r"(\d+(?:\.?\d+)?)\s*m\u00b2\s*de\s*terreno", "total_area_m2"),
]


def parse_details(details: list[str]) -> dict:
    parsed = {}
    for detail in details:
        detail_lower = detail.lower()
        for pattern, field in _DETAIL_PATTERNS:
            m = re.search(pattern, detail_lower)
            if m:
                val = m.group(1).replace(".", "")
                if field in ("built_area_m2", "total_area_m2"):
                    parsed[field] = float(val)
                else:
                    parsed[field] = int(val)
    return parsed


def parse_location(text: str) -> dict:
    if not text:
        return {"city": None, "district": None}
    parts = [p.strip() for p in text.split(",")]
    if len(parts) >= 2:
        return {"city": parts[0], "district": parts[1]}
    if len(parts) == 1:
        return {"city": parts[0], "district": None}
    return {"city": None, "district": None}


def _category_url(cat_type: str, action: str) -> str:
    parts = [BASE_URL]
    parts.append(cat_type)
    if action:
        parts.append(action)
    return "/".join(parts) + "/"


def scrape_category(page, cat_type: str, action: str, max_pages: int = 6) -> list[dict]:
    url = _category_url(cat_type, action)
    listings = []
    seen_urls = set()

    for page_num in range(1, max_pages + 1):
        page_url = url
        if page_num > 1:
            offset = (page_num - 1) * 50 + 1
            page_url = url.rstrip("/") + f"/_Desde_{offset}"

        print(f"  [{cat_type}] Page {page_num}: {page_url}")
        try:
            page.goto(page_url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"  [{cat_type}] Timeout/nav error on page {page_num}: {e}")
            page.wait_for_timeout(5000)

        page.wait_for_timeout(3000)

        cards = page.query_selector_all("ol.ui-search-layout > li")
        if not cards:
            cards = page.query_selector_all("li.ui-search-layout__item")

        if not cards:
            print(f"  [{cat_type}] No listings found on page {page_num}, stopping.")
            break

        for card in cards:
            try:
                listing = _extract_card(card, cat_type)
                if listing and listing["source_url"] not in seen_urls:
                    seen_urls.add(listing["source_url"])
                    listings.append(listing)
            except Exception as e:
                print(f"  [{cat_type}] Error extracting card: {e}")
                continue

        print(f"  [{cat_type}] Page {page_num}: {len(cards)} cards, {len(listings)} unique")

        next_btn = page.query_selector("a[title*='Siguiente']")
        if not next_btn:
            next_btn = page.query_selector("a.andes-pagination__button--next:not(.andes-pagination__button--disabled)")
        if not next_btn:
            print(f"  [{cat_type}] No next page, stopping.")
            break

        page.wait_for_timeout(1000)

    return listings


def _extract_card(card, cat_type: str) -> dict | None:
    link_el = card.query_selector("a[href]")
    if not link_el:
        return None
    url = link_el.get_attribute("href") or ""
    if not url.startswith("http"):
        url = "https://inmuebles.mercadolibre.com.py" + url

    title_el = card.query_selector("h3")
    if not title_el:
        title_el = card.query_selector("[class*=title]")
    title = title_el.inner_text().strip() if title_el else ""

    price_el = card.query_selector(".andes-money-amount")
    price_text = price_el.text_content().strip() if price_el else ""

    detail_els = card.query_selector_all("li[class*=attribute]")
    details = [el.inner_text().strip() for el in detail_els if el.inner_text().strip()]

    location_el = card.query_selector("[class*=location]")
    location_text = location_el.inner_text().strip() if location_el else ""

    img_el = card.query_selector("img[src*=mlstatic]")
    images = [img_el.get_attribute("src")] if img_el else []

    price_pyg, price_usd, currency = parse_price(price_text)
    detail_parsed = parse_details(details)
    loc = parse_location(location_text)

    return {
        "title": title,
        "source_url": url,
        "price_pyg": price_pyg,
        "price_usd": price_usd,
        "currency": currency,
        "property_type": TYPE_MAP.get(cat_type, "otro"),
        "city": loc["city"],
        "district": loc["district"],
        "bedrooms": detail_parsed.get("bedrooms"),
        "bathrooms": detail_parsed.get("bathrooms"),
        "built_area_m2": detail_parsed.get("built_area_m2"),
        "total_area_m2": detail_parsed.get("total_area_m2"),
        "images": images,
        "source": "mercadolibre",
    }


def _to_property_listing(data: dict) -> PropertyListing:
    return PropertyListing(
        source=data["source"],
        source_url=data["source_url"],
        title=data["title"],
        property_type=data["property_type"],
        price=data["price_pyg"] if data["currency"] == "PYG" else data["price_usd"],
        price_usd=data["price_usd"],
        currency=data["currency"],
        city=data["city"],
        district=data["district"],
        bedrooms=data["bedrooms"],
        bathrooms=data["bathrooms"],
        built_area_m2=data["built_area_m2"],
        total_area_m2=data["total_area_m2"],
        images=data["images"],
        scraped_at=datetime.now(),
    )


def run(max_pages: int = 6):
    output_dir = DATA_DIR / "mercadolibre"
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / "listings.jsonl"

    total = 0
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

        for cat_type, action in CATEGORIES:
            print(f"\nScraping: {cat_type}/{action or 'venta'}")
            listings = scrape_category(page, cat_type, action, max_pages)
            for data in listings:
                listing = _to_property_listing(data)
                save_jsonl(listing, DATA_DIR, "mercadolibre")
            total += len(listings)
            print(f"  [{cat_type}] Done: {len(listings)} listings")

        browser.close()

    print(f"\nMercadoLibre done. Total: {total} listings -> {filepath}")


if __name__ == "__main__":
    run(max_pages=6)

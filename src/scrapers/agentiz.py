# Agentiz PY scraper — ad-posting platform, NOT a listing directory.
# Inventory is too small (~25 PY listings) and JS-rendered via API calls.
# Not worth the effort — kept for completeness.

import re
from urllib.parse import urljoin

from parsel import Selector

from src.models.property import PropertyListing, SourceConfig
from src.scrapers.base import BaseScraper


PG_CONFIG = SourceConfig(
    name="agentiz",
    display_name="Agentiz Paraguay",
    base_url="https://py.agentiz.com",
    search_urls=["/es/residential-property/listing?deal=1"],
    max_pages=1,
    rate_limit_delay=2.0,
)

PRICE_RE = re.compile(r"Gs\.?\s*([\d.,]+)")
FLOAT_CLEAN_RE = re.compile(r"[^\d.]")
BEDROOM_RE = re.compile(r"(\d+)\s*br", re.IGNORECASE)
AREA_RE = re.compile(r"([\d.,]+)\s*m²", re.IGNORECASE)
FLOORS_RE = re.compile(r"(\d+)\s*(?:piso|p|er\s*piso|°\s*piso)", re.IGNORECASE)
TOTAL_FLOORS_RE = re.compile(r"(\d+)\s*(?:pisos|niveles)", re.IGNORECASE)
BATHROOM_RE = re.compile(r"(\d+)\s*(?:baño|ba\~?|[bt]h)", re.IGNORECASE)

# Category in URL → property_type mapping
CATEGORY_TYPE_MAP = {
    "housing": "casa",
    "apartment": "departamento",
    "land": "terreno",
    "penthouse": "penthouse",
    "commercial": "local",
}


def _parse_pyg_price(text: str) -> float | None:
    normalized = text.replace("Gs.", "").replace(".", "").replace(",", ".").strip()
    m = PRICE_RE.search(normalized)
    if m:
        val = FLOAT_CLEAN_RE.sub("", m.group(1))
        try:
            return float(val)
        except ValueError:
            return None
    return None


def _extract_id(url: str) -> str | None:
    m = re.search(r"/id-([a-z0-9]+)", url)
    return m.group(1) if m else None


def _detect_property_type(url: str) -> str:
    for key, val in CATEGORY_TYPE_MAP.items():
        if key in url.lower():
            return val
    return "otros"


def _detect_deal_type(url: str, search_sel: Selector | None = None) -> str:
    """Return 'venta' or 'alquiler' based on URL or page state."""
    if "for-rent" in url.lower() or "deal=2" in url.lower():
        return "alquiler"
    if "for-sale" in url.lower() or "deal=1" in url.lower():
        return "venta"
    if search_sel is not None:
        checked = search_sel.css('input[name="100"]:checked')
        if checked:
            parent = checked.xpath("..")
            text = parent.css("::text").get("").strip()
            if "alquiler" in text.lower():
                return "alquiler"
    return "venta"


class AgentizScraper(BaseScraper):
    def __init__(self, config: SourceConfig = PG_CONFIG):
        super().__init__(config)
        self.base_url = config.base_url

    def extract_listings(self, html: str, source_url: str) -> list[dict]:
        """Extract listing data from search result page (used by run() via parse_search_page)."""
        sel = Selector(html)
        listings = []
        for card in sel.css(".b-property-card"):
            link_el = card.css("a.b-property-card-header-main-link")
            href = link_el.attrib.get("href", "")
            if not href:
                continue
            url = urljoin(self.base_url, href)
            title = link_el.css("::text").get("").strip()
            location = card.css(".b-property-card-header-secondary::text").get("").strip()
            raw_price = card.css(".b-property-card-price-value::text").get("")
            price = _parse_pyg_price(raw_price) if raw_price else None
            briefly_items = card.css("ul.b-property-card-briefly li span::text").getall()
            bedrooms = None
            area_m2 = None
            for item in briefly_items:
                item = item.strip()
                m = BEDROOM_RE.search(item)
                if m:
                    bedrooms = int(m.group(1))
                    continue
                m = AREA_RE.search(item)
                if m:
                    val = m.group(1).replace(".", "").replace(",", ".")
                    try:
                        area_m2 = float(val)
                    except ValueError:
                        pass
            description = card.css("p.b-property-card-description::text").get("").strip()
            listings.append({
                "url": url,
                "title": title,
                "location": location,
                "price": price,
                "bedrooms": bedrooms,
                "area_m2": area_m2,
                "description": description,
            })
        return listings

    def _extract_listing_urls(self, sel: Selector) -> list[str]:
        urls = []
        for a in sel.css("a.b-property-card-header-main-link"):
            href = a.attrib.get("href", "")
            if href:
                full = urljoin(self.base_url, href)
                urls.append(full)
        seen = set()
        return [u for u in urls if not (u in seen or seen.add(u))]

    def _extract_next_page(self, sel: Selector) -> str | None:
        return None

    def extract_detail(self, url: str) -> PropertyListing | None:
        html = self.fetch(url)
        if not html:
            return None
        sel = Selector(html)

        # Title
        title = sel.css("#ad_view_header_main_text::text").get("").strip()
        if not title:
            title = sel.css("h1.b-view-header-main span:first-child::text").get("").strip()

        external_id = _extract_id(url)

        # Location from secondary header
        location_text = sel.css("#subheader_location_text::text").get("")
        if not location_text:
            location_text = sel.css("h2.b-view-header-secondary::text").get("")
        location_text = (location_text or "").strip()
        city = None
        district = None
        if location_text:
            parts = [p.strip() for p in location_text.split(",")]
            city = parts[0] if parts else None

        # Price
        raw_price = sel.css(".b-view-price-value::text").get("")
        price = _parse_pyg_price(raw_price) if raw_price else None

        # Briefly (bedrooms, area)
        bedrooms = None
        total_area_m2 = None
        for item in sel.css(".b-view-briefly li .text::text").getall():
            item = item.strip()
            m = BEDROOM_RE.search(item)
            if m:
                bedrooms = int(m.group(1))
                continue
            m = AREA_RE.search(item)
            if m:
                val = m.group(1).replace(".", "").replace(",", ".")
                try:
                    total_area_m2 = float(val)
                except ValueError:
                    pass

        # Structured details from <section class="b-view-details">
        bathrooms = None
        floors = None
        built_area_m2 = None
        for section in sel.css("section.b-view-details"):
            header = section.css("h3.b-view-details-header::text").get("").strip()
            for term, definition in self._extract_dl_pairs(section):
                if term == "dormitorios" and bedrooms is None:
                    try:
                        bedrooms = int(definition)
                    except ValueError:
                        pass
                elif "baño" in term and bathrooms is None:
                    try:
                        bathrooms = int(definition)
                    except ValueError:
                        pass
                elif "área" in term and "total" in term and total_area_m2 is None:
                    try:
                        total_area_m2 = float(definition.replace(",", "."))
                    except ValueError:
                        pass
                elif "construida" in term or "edificada" in term:
                    try:
                        built_area_m2 = float(definition.replace(",", "."))
                    except ValueError:
                        pass
                elif "piso" in term and floors is None:
                    try:
                        floors = int(definition)
                    except ValueError:
                        pass

        # Description
        description_parts = sel.css(".b-view-text p::text").getall()
        description = "\n".join(p.strip() for p in description_parts if p.strip())

        # Images from gallery
        images = []
        for img in sel.css(".b-view-gallery picture.images_item img, picture.images_item img"):
            src = img.attrib.get("src", "")
            if src and not src.startswith("data:"):
                images.append(urljoin(self.base_url, src))

        # Contact info
        contact_name = None
        contact_phone = None
        name_el = sel.css(".b-view-details.contacts .person_set .name::text").get("")
        if name_el:
            contact_name = name_el.strip()
        call_btn = sel.css("button.call")
        if call_btn:
            numbers = call_btn.attrib.get("data-numbers", "")
            if numbers:
                contact_phone = numbers

        # Property type from URL
        prop_type = _detect_property_type(url)

        # Deal type
        deal_type = _detect_deal_type(url, sel)

        # Listing date
        listing_date = None
        time_el = sel.css("time.b-view-header-time")
        if time_el:
            dt = time_el.attrib.get("datetime", "")
            if dt:
                from datetime import date
                try:
                    listing_date = date.fromisoformat(dt[:10])
                except ValueError:
                    pass

        return PropertyListing(
            source=self.config.name,
            source_url=url,
            external_id=external_id,
            title=title,
            property_type=prop_type,
            price=price,
            currency="PYG",
            city=city,
            district=district,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            total_area_m2=total_area_m2,
            built_area_m2=built_area_m2,
            floors=floors,
            description=description,
            images=images,
            contact_name=contact_name,
            contact_phone=contact_phone,
            listing_date=listing_date,
        )

    def _extract_dl_pairs(self, section: Selector) -> list[tuple[str, str]]:
        pairs = []
        for dl in section.css("dl.details_set"):
            terms = dl.css("dt.term::text").getall()
            defs = dl.css("dd.definition::text").getall()
            for t, d in zip(terms, defs):
                pairs.append((t.strip().lower().rstrip(";:"), d.strip()))
        return pairs

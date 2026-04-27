# Buscocasita Paraguay scraper — simple HTML, no JS required.
# Homepage shows latest listings, detail pages have structured fields.
# Pagination via ?page=N on /buscar-propiedades.html.

import re
from urllib.parse import urljoin

from parsel import Selector

from src.models.property import PropertyListing, SourceConfig
from src.scrapers.base import BaseScraper


# Map "Tipo de inmueble:" labels to normalized property_type
PROPERTY_TYPE_MAP = {
    "casa": "casa",
    "departamento": "departamento",
    "terreno": "terreno",
    "local comercial": "local",
    "oficina": "oficina",
    "edificio": "edificio",
    "penthouse": "penthouse",
    "country": "country",
    "otros": "otros",
}

# Patterns for scraping area values from detail fields
AREA_RE = re.compile(r"([\d.,]+)\s*m2", re.IGNORECASE)
PRICE_PYG_RE = re.compile(r"G\s*([\d.,]+)")
PRICE_USD_RE = re.compile(r"USD\s*([\d.,]+)")
FLOAT_CLEAN_RE = re.compile(r"[^\d.]")


def _parse_price(text: str) -> tuple[float | None, float | None, str]:
    """Parse price text like 'G 1.760.000.000,00 guaraníes' or 'USD 150.000,00 dólares'.
    Returns (price_pyg, price_usd, currency).
    """
    # Remove thousand separators (dots) and normalize decimal comma
    normalized = text.replace(".", "").replace(",", ".")

    m = PRICE_PYG_RE.search(normalized)
    if m:
        val = float(FLOAT_CLEAN_RE.sub("", m.group(1)))
        return val, None, "PYG"

    m = PRICE_USD_RE.search(normalized)
    if m:
        val = float(FLOAT_CLEAN_RE.sub("", m.group(1)))
        return None, val, "USD"

    return None, None, "PYG"


def _extract_id_from_url(url: str) -> str | None:
    """Extract numeric ID from URL like /slug_395727.html"""
    m = re.search(r"_(\d+)\.html$", url)
    return m.group(1) if m else None


def _map_property_type(raw: str) -> str:
    raw_lower = raw.strip().lower()
    for key, val in PROPERTY_TYPE_MAP.items():
        if key in raw_lower:
            return val
    return "otros"


BC_CONFIG = SourceConfig(
    name="buscocasita",
    display_name="BuscoCasita Paraguay",
    base_url="https://paraguay.buscocasita.com",
    search_urls=["/"],
    max_pages=50,
    rate_limit_delay=2.0,
)


class BuscocasitaScraper(BaseScraper):
    def __init__(self, config: SourceConfig = BC_CONFIG):
        super().__init__(config)

    def _extract_listing_urls(self, sel: Selector) -> list[str]:
        """Homepage: .inmueble div > a with href. Search page: .inmueblefila2 > a."""
        urls = []
        for a in sel.css(".inmueble a[href], .inmueblefila2 a[href]"):
            href = a.attrib.get("href", "")
            if href and href.endswith(".html") and "_" in href:
                full = urljoin(self.config.base_url, href)
                urls.append(full)
        # Deduplicate while preserving order
        seen = set()
        return [u for u in urls if not (u in seen or seen.add(u))]

    def _extract_next_page(self, sel: Selector) -> str | None:
        """Search page has pagination: .pactivo links. Homepage has none."""
        # Check for next page via the active page link pattern
        current = sel.css("span.pinactivo::text").get()
        if not current:
            return None
        try:
            cur_page = int(current.strip())
        except ValueError:
            return None
        next_page = cur_page + 1
        link = sel.css(f'a.pactivo[href*="page={next_page}"]::attr(href)').get()
        if link:
            return urljoin(self.config.base_url, link)
        return None

    def extract_listings(self, html: str, source_url: str) -> list[dict]:
        return []

    def extract_detail(self, url: str) -> PropertyListing | None:
        html = self.fetch(url)
        if not html:
            return None

        sel = Selector(html)

        title = sel.css("#barraseparadora::text").get("").strip()
        if not title:
            title = sel.css("title::text").get("").strip()

        external_id = _extract_id_from_url(url)

        # Extract structured fields from the detail table
        fields = {}
        for fila in sel.css(".inmueblefila"):
            label = fila.css(".inmueblecampo1::text").get("").strip().rstrip(":")
            value = fila.css(".inmueblecampo2 *::text").get("").strip()
            if label:
                fields[label.lower()] = value

        # Price
        raw_price = fields.get("precio", "")
        price_pyg, price_usd, currency = _parse_price(raw_price)

        # Property type from "Tipo de inmueble:"
        raw_type = fields.get("tipo de inmueble", "")
        prop_type = _map_property_type(raw_type)
        transaction = "alquiler" if "alquiler" in raw_type.lower() else "venta"

        # Location fields
        city = fields.get("ciudad", None)
        district = fields.get("barrio", None)
        zone = fields.get("zona", None)

        # Area
        total_area = None
        raw_area = fields.get("área del terreno", "")
        if raw_area:
            m = AREA_RE.search(raw_area)
            if m:
                total_area = float(m.group(1).replace(".", "").replace(",", "."))

        # Bedrooms / bathrooms from description heuristic (detail page has no structured fields for these)
        bedrooms = None
        bathrooms = None
        desc_text = " ".join(sel.css(".inmuebledetalle *::text").getall())

        bed_m = re.search(r"(\d+)\s*dorm", desc_text, re.IGNORECASE)
        if bed_m:
            bedrooms = int(bed_m.group(1))
        bath_m = re.search(r"(\d+)\s*bañ", desc_text, re.IGNORECASE)
        if not bath_m:
            bath_m = re.search(r"(\d+)\s*banio", desc_text, re.IGNORECASE)
        if not bath_m:
            bath_m = re.search(r"(\d+)\s*bath", desc_text, re.IGNORECASE)
        if bath_m:
            bathrooms = int(bath_m.group(1))

        # Description
        description = ""
        desc_header = sel.xpath(
            '//div[contains(@class, "inmuebletitulo") and contains(text(), "Descripción")]'
        )
        if desc_header:
            # The next sibling with class inmuebledetalle
            desc_div = desc_header.xpath(
                "following-sibling::div[contains(@class, 'inmuebledetalle')][1]"
            )
            if desc_div:
                description = desc_div.get()  # raw HTML includes <br /> tags
                # Clean it to plain text
                description = re.sub(r"<br\s*/?>", "\n", description)
                description = re.sub(r"<[^>]+>", "", description)
                description = description.strip()

        # Images
        images = []
        for img in sel.css(".inmueblefoto"):
            src = img.attrib.get("src", "")
            if src and "buscocasita.com/img" in src:
                images.append(src)

        # Contact — not exposed on detail pages (contact is via form only)

        return PropertyListing(
            source=self.config.name,
            source_url=url,
            external_id=external_id,
            title=title,
            property_type=prop_type,
            price=price_pyg,
            price_usd=price_usd,
            currency=currency,
            city=city,
            district=district,
            zone=zone,
            total_area_m2=total_area,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            description=description,
            images=images,
        )

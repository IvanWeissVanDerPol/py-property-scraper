"""Scraper for inmueblespy.com — Paraguayan real estate portal (Houzez WP theme)."""

import json
import re
from typing import Optional

from parsel import Selector

from src.models.property import PropertyListing, SourceConfig
from src.scrapers.base import BaseScraper
from src.utils.storage import save_jsonl


INMUEBLESPY_CONFIG = SourceConfig(
    name="inmueblespy",
    display_name="InmueblesPY",
    base_url="https://inmueblespy.com",
    search_urls=["/venta/"],
    max_pages=50,
)


class InmueblesPYScraper(BaseScraper):
    """Houzez WordPress theme. Search pages: static HTML cards. Detail pages: JSON-LD in <head>."""

    def __init__(self):
        super().__init__(INMUEBLESPY_CONFIG)

    def extract_listings(self, html: str, source_url: str) -> list[dict]:
        sel = Selector(html)
        urls, _ = self.parse_search_page(html)
        return [{"url": u} for u in urls]

    def _extract_listing_urls(self, sel: Selector) -> list[str]:
        urls = []
        for link in sel.css(
            '.item-listing-wrap a.listing-thumb[href], '
            '.listing-thumb a[href], '
            '.item-title a[href], '
            '.item-wrap a[href*="/inmueble/"]'
        ):
            href = link.attrib.get("href", "").strip()
            if not href:
                continue
            if href.startswith("http"):
                urls.append(href)
            elif href.startswith("/"):
                urls.append(f"{self.config.base_url}{href}")
        return list(dict.fromkeys(urls))

    def _extract_next_page(self, sel: Selector) -> str | None:
        # Direct URL construction is handled in run() override.
        # This method is kept for the base class interface but unused.
        return None

    def run(self):
        """Override base run(): construct paginated URLs directly.

        InmueblesPY uses WordPress /venta/ and /venta/page/N/ pagination.
        Direct URL construction is more reliable than DOM-based next-page detection
        which can fail on Houzez theme variations.
        """
        seen_urls = set()
        base_url = self.config.base_url
        search_path = self.config.search_urls[0]

        for page_num in range(1, self.config.max_pages + 1):
            if page_num == 1:
                url = f"{base_url}{search_path}"
            else:
                url = f"{base_url}/venta/page/{page_num}/"

            html = self.fetch(url)
            if not html:
                # 404 or error means no more pages
                break

            sel = Selector(html)
            urls = self._extract_listing_urls(sel)

            if not urls:
                # Empty page = no more listings
                break

            for listing_url in urls:
                if listing_url in seen_urls:
                    continue
                seen_urls.add(listing_url)
                listing = self.extract_detail(listing_url)
                if listing:
                    save_jsonl(listing, self.output_dir, self.config.name)

            print(f"[{self.config.name}] Page {page_num}: {len(urls)} listings")

        print(f"[{self.config.name}] Done. Scraped {len(seen_urls)} unique listings.")

    def extract_detail(self, url: str) -> Optional[PropertyListing]:
        html = self.fetch(url)
        if not html:
            return None

        ld = self._extract_jsonld(html)
        sel = Selector(html)

        title = ld.get("name", "")
        if not title:
            title = " ".join(sel.css("h1::text").getall()).strip()

        external_id = ""
        ip_match = re.search(r"(IP-\d+)", html)
        if ip_match:
            external_id = ip_match.group(1)

        desc = ld.get("description", "")
        if not desc:
            desc = " ".join(sel.css(".property-description-wrap *::text").getall()).strip()

        property_type_raw = self._extract_houzez_detail(html, "Tipo", "Tipo de Inmueble")
        property_type = self._normalize_type(property_type_raw)

        price_pyg, price_usd, currency = self._parse_price_from_ld(ld, html)

        address = ld.get("address", {})
        city = address.get("addressLocality", "")
        district = self._extract_houzez_detail(html, "Barrio")
        street = address.get("streetAddress", "")

        geo = ld.get("geo", {})
        coordinates = None
        if geo.get("latitude") and geo.get("longitude"):
            coordinates = (float(geo["latitude"]), float(geo["longitude"]))

        bedrooms = ld.get("numberOfBedrooms")
        bathrooms = ld.get("numberOfBathroomsTotal")
        total_area_m2 = None
        floor_size = ld.get("floorSize", {})
        if floor_size.get("value"):
            total_area_m2 = float(floor_size["value"])
        built_area_m2 = self._extract_houzez_float(html, "Tamaño Construido", "Construido")
        year_built = ld.get("yearBuilt")
        parking_spots = self._extract_houzez_int(html, "Estacionamiento", "Garage", "Cochera")

        images = ld.get("image", [])

        seller = ld.get("offers", {}).get("seller", {})
        contact_name = seller.get("name", "")
        contact_phone = ""
        if seller.get("telephone"):
            contact_phone = seller["telephone"].replace("tel:", "").strip()
        agency = self._extract_houzez_detail(html, "Agencia")
        if not agency:
            agency = seller.get("name", "")

        listing = PropertyListing(
            source=self.config.name,
            source_url=url,
            external_id=external_id or None,
            title=title,
            property_type=property_type,
            price=price_pyg,
            price_usd=price_usd,
            currency=currency,
            city=city.strip(),
            district=district.strip() if district else None,
            address=street.strip() if street else None,
            coordinates=coordinates,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            total_area_m2=total_area_m2,
            built_area_m2=built_area_m2,
            parking_spots=parking_spots,
            year_built=year_built,
            description=desc.strip(),
            images=images if images else [],
            contact_name=contact_name.strip() if contact_name else None,
            contact_phone=contact_phone if contact_phone else None,
            agency=agency.strip() if agency else None,
        )
        return listing

    def _extract_jsonld(self, html: str) -> dict:
        m = re.search(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )
        if m:
            try:
                data = json.loads(m.group(1))
                if isinstance(data, dict) and data.get("@type") == "RealEstateListing":
                    return data
            except json.JSONDecodeError:
                pass
        return {}

    def _extract_houzez_detail(self, html: str, *labels: str) -> str:
        for label in labels:
            m = re.search(
                rf'{re.escape(label)}[:\s]*</[^>]+>\s*<[^>]+>\s*([^<]+)',
                html, re.IGNORECASE
            )
            if m:
                return m.group(1).strip()
            m2 = re.search(rf'<li[^>]*>.*?{re.escape(label)}.*?<strong[^>]*>([^<]+)</strong>', html, re.IGNORECASE | re.DOTALL)
            if m2:
                return m2.group(1).strip()
            pattern = rf'{re.escape(label)}\s*:\s*([^<\n]+)'
            m3 = re.search(pattern, html, re.IGNORECASE)
            if m3:
                return m3.group(1).strip()
        return ""

    def _extract_houzez_int(self, html: str, *labels: str) -> Optional[int]:
        for label in labels:
            text = self._extract_houzez_detail(html, label)
            if text:
                m = re.search(r"(\d+)", text)
                if m:
                    return int(m.group(1))
        return None

    def _extract_houzez_float(self, html: str, *labels: str) -> Optional[float]:
        for label in labels:
            text = self._extract_houzez_detail(html, label)
            if text:
                m = re.search(r"([\d.,]+)\s*m²", text)
                if m:
                    return float(m.group(1).replace(".", "").replace(",", "."))
                m = re.search(r"([\d.]+)", text)
                if m:
                    return float(m.group(1).replace(".", ""))
        return None

    def _parse_price_from_ld(self, ld: dict, html: str) -> tuple[Optional[float], Optional[float], str]:
        offers = ld.get("offers", {})
        price_currency = offers.get("priceCurrency", "PYG")
        price_value = offers.get("price")

        if price_value is not None:
            price_float = float(price_value)
            if price_currency == "USD":
                if price_float > 5000000:
                    return price_float, None, "PYG"
                return None, price_float, "USD"
            return price_float, None, "PYG"

        m = re.search(r'class="price-prefix"[^>]*>([0-9.]+)<', html)
        if m:
            num = m.group(1).replace(".", "")
            return float(num), None, "PYG"
        m = re.search(r'₲\s*([0-9.]+)', html)
        if m:
            num = m.group(1).replace(".", "")
            return float(num), None, "PYG"
        m = re.search(r'USD\s*([0-9.]+)', html)
        if m:
            return None, float(m.group(1)), "USD"
        m = re.search(r'\$\s*([0-9.]+)', html, re.IGNORECASE)
        if m:
            return None, float(m.group(1)), "USD"
        return None, None, "PYG"

    def _normalize_type(self, raw: str) -> str:
        mapping = {
            "casa unifamiliar": "casa",
            "casa multifamiliar": "casa",
            "casa de campo": "casa",
            "casa adosada": "casa",
            "departamento": "departamento",
            "apartamento": "departamento",
            "terreno urbano": "terreno",
            "terreno rural": "terreno",
            "local": "local",
            "comercio": "local",
            "oficina": "local",
            "penthouse": "penthouse",
            "country": "country",
            "residencial": "casa",
            "duplex": "casa",
        }
        raw_lower = raw.strip().lower()
        for key, val in mapping.items():
            if key in raw_lower:
                return val
        return raw.strip()

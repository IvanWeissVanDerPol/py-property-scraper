"""
InfoCasas.com.py scraper.

Extracts property listings from InfoCasas (Paraguay's leading real estate portal).
Parses __NEXT_DATA__ embedded JSON from Next.js search pages.
All listing fields are available in the search page JSON — no detail page requests needed.
"""

import json
import re
from datetime import date, datetime

from src.models.property import PropertyListing, SourceConfig
from src.scrapers.base import BaseScraper


PROPERTY_TYPE_MAP = {
    1: "casa",
    2: "departamento",
    3: "terreno",
    4: "local",
    5: "oficina",
    6: "country",
    7: "penthouse",
    8: "galpón",
    9: "cochera",
}


class InfoCasasScraper(BaseScraper):
    def __init__(self):
        config = SourceConfig(
            name="infocasas",
            display_name="InfoCasas Paraguay",
            base_url="https://www.infocasas.com.py",
            search_urls=["/venta"],
            max_pages=500,
        )
        super().__init__(config)

    def extract_listings(self, html: str, source_url: str) -> list[dict]:
        return []

    def extract_detail(self, url: str) -> PropertyListing | None:
        html = self.fetch(url)
        if not html:
            return None
        return self._parse_listing_from_html(html, url)

    def run(self):
        seen_ids = set()
        for search_path in self.config.search_urls:
            page = 1
            while page <= self.config.max_pages:
                if page == 1:
                    url = f"{self.config.base_url}{search_path}"
                else:
                    url = f"{self.config.base_url}{search_path}?page={page}"

                html = self.fetch(url)
                if not html:
                    break

                listings = self._extract_search_listings(html)
                if not listings:
                    break

                for raw in listings:
                    listing_id = raw.get("id")
                    if listing_id in seen_ids:
                        continue
                    seen_ids.add(listing_id)

                    listing = self._parse_listing(raw, url, listing_id)
                    if listing:
                        from src.utils.storage import save_jsonl
                        save_jsonl(listing, self.output_dir, self.config.name)

                print(f"[{self.config.name}] Page {page}: {len(listings)} listings")
                page += 1

        print(f"[{self.config.name}] Done. Scraped {len(seen_ids)} unique listings.")

    def _extract_search_listings(self, html: str) -> list[dict]:
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        if not match:
            return []
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
        page_props = data.get("props", {}).get("pageProps", {})
        fetch_result = page_props.get("fetchResult", {})
        search_fast = fetch_result.get("searchFast", fetch_result)
        return search_fast.get("data", [])

    def _parse_listing(
        self, raw: dict, source_url: str, listing_id: int
    ) -> PropertyListing | None:
        if not raw.get("title"):
            return None

        raw_link = raw.get("link", "")
        listing_url = f"{self.config.base_url}{raw_link}" if raw_link else source_url

        currency = raw.get("currency", {})
        if isinstance(currency, dict):
            currency_name = currency.get("name", "")
        else:
            currency_name = str(currency) if currency else ""

        if currency_name == "U$S":
            price = raw.get("price_amount_usd")
            price_usd = price
            target_currency = "USD"
        elif currency_name == "Gs.":
            price = raw.get("price", {})
            if isinstance(price, dict):
                price = price.get("amount")
            price_usd = raw.get("price_amount_usd")
            target_currency = "PYG"
        else:
            price = raw.get("price_amount_usd")
            price_usd = price
            target_currency = "USD"

        property_type_id = raw.get("property_type_id") or raw.get("typeID")
        property_type = PROPERTY_TYPE_MAP.get(property_type_id, "otro")

        locations = raw.get("locations", {})
        coordinates = None
        location_point = locations.get("location_point", "")
        if location_point and location_point.startswith("POINT ("):
            coords_str = location_point[7:-1]
            parts = coords_str.strip().split()
            if len(parts) == 2:
                try:
                    coordinates = (float(parts[1]), float(parts[0]))
                except (ValueError, IndexError):
                    pass

        if not coordinates:
            lat = raw.get("latitude")
            lon = raw.get("longitude")
            if lat is not None and lon is not None:
                try:
                    coordinates = (float(lat), float(lon))
                except (ValueError, TypeError):
                    pass

        city = None
        state_names = locations.get("state", [])
        if state_names:
            city = state_names[0].get("name")

        neighbourhood = locations.get("neighbourhood", [])
        district = neighbourhood[0].get("name") if neighbourhood else None

        owner = raw.get("owner", {}) or {}
        agency = owner.get("name") if owner.get("type") == "inmobiliaria" else None
        contact_name = owner.get("name")
        contact_phone = owner.get("whatsapp_phone") or owner.get("masked_phone")

        images = []
        for img in raw.get("images", []):
            if isinstance(img, dict):
                url = img.get("image") or img.get("url")
                if url:
                    images.append(url)

        if not images:
            main_img = raw.get("img")
            if main_img:
                images.append(main_img)

        features = []
        for fac in raw.get("facilities", []):
            if isinstance(fac, dict) and fac.get("name"):
                features.append(fac["name"])

        created_raw = raw.get("created_at")
        listing_date = None
        if created_raw:
            try:
                listing_date = datetime.strptime(created_raw, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        updated_raw = raw.get("updated_at")
        last_updated = None
        if updated_raw:
            try:
                last_updated = datetime.strptime(updated_raw, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        description = raw.get("description") or ""
        if description:
            description = re.sub(r"<[^>]+>", "", description).strip()

        return PropertyListing(
            source=self.config.name,
            source_url=listing_url,
            external_id=str(listing_id),
            title=raw.get("title", ""),
            property_type=property_type,
            price=price,
            price_usd=price_usd,
            currency=target_currency,
            city=city or "",
            district=district or "",
            address=raw.get("address") or "",
            coordinates=coordinates,
            bedrooms=self._safe_int(raw.get("bedrooms")),
            bathrooms=self._safe_int(raw.get("bathrooms")),
            total_area_m2=self._safe_float(raw.get("m2")),
            built_area_m2=self._safe_float(raw.get("m2Built")),
            floors=self._safe_int(raw.get("floorsCount")),
            parking_spots=self._safe_int(raw.get("garage")),
            description=description,
            features=features,
            images=images,
            contact_name=contact_name,
            contact_phone=contact_phone,
            agency=agency,
            listing_date=listing_date,
            last_updated=last_updated,
        )

    def _safe_int(self, value) -> int | None:
        if value is None:
            return None
        try:
            v = int(value)
            return v if v >= 0 else None
        except (ValueError, TypeError):
            return None

    def _safe_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

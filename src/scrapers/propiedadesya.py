# PropiedadesYA Paraguay scraper — Houzez WordPress site.
# Parses search pages via HTML, extracts detail pages via JSON-LD + HTML fallback.

import json
import re
from datetime import datetime
from urllib.parse import urljoin

from parsel import Selector

from src.models.property import PropertyListing, SourceConfig
from src.scrapers.base import BaseScraper

PY_CONFIG = SourceConfig(
    name="propiedadesya",
    display_name="PropiedadesYA Paraguay",
    base_url="https://propiedadesya.com.py",
    search_urls=["/propiedades/"],
    max_pages=50,
    rate_limit_delay=2.0,
)

WP_API_URL = "https://propiedadesya.com.py/wp-json/wp/v2/properties"

PROPERTY_TYPE_MAP = {
    "casa": "casa",
    "departamento": "departamento",
    "terreno": "terreno",
    "local-comercial": "local",
    "oficina": "oficina",
    "edificio": "edificio",
    "estancia": "estancia",
    "chacra-estancia": "estancia",
    "quinta-casa-de-campo": "country",
    "duplex": "casa",
    "deposito-tinglado": "local",
}

STATUS_MAP = {
    "venta": "venta",
    "alquiler": "alquiler",
}

NUM_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _parse_pyg_price(val: str) -> float | None:
    if not val:
        return None
    clean = val.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None


def _parse_usd_price(val: str) -> float | None:
    if not val:
        return None
    clean = val.replace(".", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return None


def _slug_from_class_list(class_list: list[str], prefix: str) -> str | None:
    for cls in class_list:
        if cls.startswith(prefix):
            return cls[len(prefix) :]
    return None


def _clean_html(html_text: str) -> str:
    text = re.sub(r"<[^>]+>", "", html_text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class PropiedadesYAScraper(BaseScraper):
    def __init__(self, config: SourceConfig = PY_CONFIG):
        super().__init__(config)
        self._type_map: dict[int, str] = {}
        self._status_map: dict[int, str] = {}
        self._city_map: dict[int, str] = {}

    def _fetch_taxonomies(self):
        for endpoint, store in [
            ("property_type", self._type_map),
            ("property_status", self._status_map),
            ("property_city", self._city_map),
        ]:
            try:
                resp = self.client.get(
                    f"{self.config.base_url}/wp-json/wp/v2/{endpoint}?per_page=100"
                )
                resp.raise_for_status()
                for term in resp.json():
                    slug = term.get("slug", "")
                    store[term["id"]] = slug
            except Exception:
                pass

    def _extract_listing_urls(self, sel: Selector) -> list[str]:
        urls = []
        for a in sel.css('a[href*="/property/"]'):
            href = a.attrib.get("href", "")
            if href and href.count("/property/") == 1 and not href.startswith("https://api.whatsapp.com"):
                full = urljoin(self.config.base_url, href)
                if full not in urls:
                    urls.append(full)
        return urls

    def _extract_next_page(self, sel: Selector) -> str | None:
        next_icon = sel.css(
            ".pagination a.page-link i.icon-arrow-right-1"
        )
        if next_icon:
            parent = next_icon.xpath("ancestor::a[1]")
            href = parent.attrib.get("href", "")
            if href:
                return urljoin(self.config.base_url, href)
        return None

    def _api_extract_listing(self, item: dict) -> PropertyListing | None:
        meta = item.get("property_meta", {})
        title = item.get("title", {}).get("rendered", "")
        link = item.get("link", "")
        external_id = str(item.get("id", ""))

        class_list = item.get("class_list", [])
        type_slug = _slug_from_class_list(class_list, "property_type-") or "otros"
        prop_type = PROPERTY_TYPE_MAP.get(type_slug, type_slug.replace("-", " ").strip())

        status_slug = _slug_from_class_list(class_list, "property_status-") or "venta"
        status = STATUS_MAP.get(status_slug, status_slug)

        price_raw = meta.get("fave_property_price", [""])[0]
        currency = meta.get("fave_currency", [""])[0] or "PYG"
        price_pyg = _parse_pyg_price(price_raw) if currency == "PYG" else None
        price_usd = _parse_usd_price(price_raw) if currency == "USD" else None

        city_slug = _slug_from_class_list(class_list, "property_city-")
        city = city_slug.replace("-", " ").title() if city_slug else None
        address = meta.get("fave_property_map_address", [""])[0] or None

        lat_raw = meta.get("houzez_geolocation_lat", [None])[0]
        lon_raw = meta.get("houzez_geolocation_long", [None])[0]
        coordinates = None
        if lat_raw and lon_raw:
            try:
                coordinates = (float(lat_raw), float(lon_raw))
            except ValueError:
                pass

        bedrooms = None
        baths_raw = meta.get("fave_property_bedrooms", [""])[0]
        if baths_raw:
            try:
                bedrooms = int(float(baths_raw))
            except ValueError:
                pass
        bathrooms = None
        baths_raw = meta.get("fave_property_bathrooms", [""])[0]
        if baths_raw:
            try:
                bathrooms = int(float(baths_raw))
            except ValueError:
                pass

        total_area_m2 = None
        land_raw = meta.get("fave_property_land", [""])[0]
        if land_raw:
            try:
                total_area_m2 = float(land_raw)
            except ValueError:
                pass

        built_area_m2 = None
        size_raw = meta.get("fave_property_size", [""])[0]
        if size_raw:
            try:
                built_area_m2 = float(size_raw)
            except ValueError:
                pass

        parking = None
        garage_raw = meta.get("fave_property_garage", [""])[0]
        if garage_raw:
            try:
                parking = int(float(garage_raw))
            except ValueError:
                pass

        year_built = None
        year_raw = meta.get("fave_property_year", [""])[0]
        if year_raw:
            try:
                year_built = int(float(year_raw))
            except ValueError:
                pass

        description = _clean_html(item.get("content", {}).get("rendered", ""))

        features = []
        for cls in class_list:
            if cls.startswith("property_feature-"):
                feat = cls[len("property_feature-"):].replace("-", " ").title()
                features.append(feat)

        images = []
        img_ids = meta.get("fave_property_images", [])
        if img_ids:
            for img_id_str in img_ids:
                if not img_id_str or not img_id_str.strip():
                    continue
                try:
                    img_id = int(img_id_str.strip())
                    resp = self.client.get(
                        f"{self.config.base_url}/wp-json/wp/v2/media/{img_id}"
                    )
                    resp.raise_for_status()
                    img_data = resp.json()
                    src = img_data.get("source_url", "")
                    if src:
                        images.append(src)
                except Exception:
                    pass

        video_url = meta.get("fave_video_url", [""])[0] or None

        contact_phone = None
        contact_name = None
        agent_display = meta.get("fave_agent_display_option", [""])[0]
        if agent_display == "agent_info":
            agent_ids = meta.get("fave_agents", [])
            if agent_ids:
                try:
                    agent_id = int(agent_ids[0])
                    resp = self.client.get(
                        f"{self.config.base_url}/wp-json/wp/v2/agents/{agent_id}"
                    )
                    resp.raise_for_status()
                    agent_data = resp.json()
                    contact_name = agent_data.get("title", {}).get("rendered")
                    agent_meta = agent_data.get("meta", {})
                    phone = agent_meta.get("fave_agent_phone", [None])[0] if isinstance(agent_meta.get("fave_agent_phone"), list) else agent_meta.get("fave_agent_phone")
                    if phone:
                        contact_phone = str(phone)
                except Exception:
                    pass

        listing_date = None
        date_str = item.get("date", "")
        if date_str:
            try:
                listing_date = datetime.fromisoformat(date_str.split("T")[0]).date()
            except (ValueError, IndexError):
                pass

        return PropertyListing(
            source=self.config.name,
            source_url=link,
            external_id=external_id,
            title=title,
            property_type=prop_type,
            price=price_pyg,
            price_usd=price_usd,
            currency=currency,
            city=city,
            address=address,
            coordinates=coordinates,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            total_area_m2=total_area_m2,
            built_area_m2=built_area_m2,
            parking_spots=parking,
            year_built=year_built,
            description=description,
            features=features,
            images=images,
            video_url=video_url,
            contact_name=contact_name,
            contact_phone=contact_phone,
            listing_date=listing_date,
            status=status,
        )

    def _parse_jsonld(self, sel: Selector) -> dict | None:
        for script in sel.css('script[type="application/ld+json"]::text').getall():
            try:
                data = json.loads(script)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("@type") == "RealEstateListing":
                return data
            if isinstance(data, dict) and data.get("@graph"):
                for node in data["@graph"]:
                    if node.get("@type") == "RealEstateListing":
                        return node
        return None

    def _html_extract_listing(self, url: str) -> PropertyListing | None:
        html = self.fetch(url)
        if not html:
            return None

        sel = Selector(html)
        ld = self._parse_jsonld(sel)

        title = ""
        description = ""
        price_pyg = None
        price_usd = None
        currency = "PYG"
        bedrooms = None
        bathrooms = None
        total_area_m2 = None
        built_area_m2 = None
        parking = None
        year_built = None
        city = None
        address = None
        coordinates = None
        images = []
        contact_name = None
        contact_phone = None

        if ld:
            title = ld.get("name", "")
            description = ld.get("description", "").replace("\u00a0", " ").strip()
            bedrooms = ld.get("numberOfBedrooms")
            bathrooms = ld.get("numberOfBathroomsTotal")
            addr = ld.get("address", {})
            if addr:
                address = addr.get("streetAddress") or None
                city = addr.get("addressLocality") or None
            geo = ld.get("geo", {})
            if geo and geo.get("latitude") and geo.get("longitude"):
                try:
                    coordinates = (float(geo["latitude"]), float(geo["longitude"]))
                except (ValueError, TypeError):
                    pass
            offers = ld.get("offers", {})
            if offers:
                raw_currency = offers.get("priceCurrency", "PYG")
                raw_price = offers.get("price")
                if raw_price is not None:
                    price_val = float(raw_price)
                    if raw_currency == "PYG":
                        price_pyg = price_val
                        currency = "PYG"
                    elif raw_currency == "USD":
                        if price_val > 500_000_000:
                            price_pyg = price_val
                            currency = "PYG"
                        else:
                            price_usd = price_val
                            currency = "USD"
            seller = offers.get("seller", {}) if offers else {}
            if seller:
                contact_name = seller.get("name") or None
                contact_phone = seller.get("telephone") or None
            raw_images = ld.get("image", [])
            if isinstance(raw_images, list):
                images = [img for img in raw_images if isinstance(img, str)]
            elif isinstance(raw_images, str):
                images = [raw_images]

        if not title:
            title = sel.css("h1::text").get("").strip()
        if not title:
            title = sel.css("title::text").get("").strip()

        external_id = None
        id_text = sel.xpath(
            '//strong[contains(text(), "PropiedadesYA")]/text()'
        ).get()
        if id_text:
            m = re.search(r"(\d+)", id_text)
            if m:
                external_id = m.group(1)
        if not external_id:
            id_text = sel.css(
                ".list-lined li:contains('ID') *::text"
            ).getall()
            full = " ".join(id_text)
            m = re.search(r"(\d+)", full)
            if m:
                external_id = m.group(1)

        if not price_pyg and not price_usd:
            price_text = sel.css(
                ".item-price span, .property-price span, .price span::text"
            ).get("")
            if price_text:
                price_text = price_text.strip()
                if price_text.startswith("Gs."):
                    price_pyg = _parse_pyg_price(price_text.replace("Gs.", "").strip())
                elif price_text.startswith("$"):
                    price_usd = _parse_usd_price(price_text.replace("$", "").strip())
                    currency = "USD"

        prop_type = "otros"
        type_texts = sel.css(
            ".breadcrumb .breadcrumb-item a::text"
        ).getall()
        for t in type_texts:
            slug = t.strip().lower().replace(" ", "-")
            mapped = PROPERTY_TYPE_MAP.get(slug)
            if mapped:
                prop_type = mapped
                break
        if prop_type == "otros":
            detail_rows = sel.css(
                ".property-detail .detail-row, .detail-table tr"
            )
            for row in detail_rows:
                label = row.css("th::text, .detail-label::text").get("").strip().lower()
                if "tipo" in label:
                    val = row.css("td::text, .detail-value::text").get("").strip().lower()
                    mapped = PROPERTY_TYPE_MAP.get(val.replace(" ", "-"))
                    if mapped:
                        prop_type = mapped
                    break

        status_links = sel.css(
            'a[href*="/status/"]::text, .property-status-badge span::text, '
            '.item-status span::text'
        ).getall()
        status = "active"
        for s in status_links:
            s = s.strip().lower()
            if s in STATUS_MAP:
                status = STATUS_MAP[s]
                break

        if not address:
            address = sel.css(
                ".property-address span, .item-address span::text"
            ).get("").strip() or None
        if not city:
            city_el = sel.css(
                ".property-city a span, .item-city::text, "
                ".breadcrumb .breadcrumb-item:last-child span::text"
            ).get()
            if city_el:
                city = city_el.strip()

        if not description:
            desc_el = sel.css(
                "#property-description-wrap .block-content-wrap"
            ).get()
            if desc_el:
                description = _clean_html(desc_el)
            if not description:
                description = sel.css(
                    ".property-description p::text"
                ).get("").strip()

        if bedrooms is None or bathrooms is None or (total_area_m2 is None and built_area_m2 is None):
            for row in sel.css(
                ".property-detail .detail-row, .detail-table tr, "
                ".property-meta li, .list-3-cols li"
            ):
                text = row.css("*::text").getall()
                text = " ".join(t.strip() for t in text if t.strip())
                text_lower = text.lower()
                m = NUM_RE.search(text)
                if not m:
                    continue
                val_str = m.group(1)
                try:
                    val = int(float(val_str.replace(".", "")))
                except ValueError:
                    continue
                if "dorm" in text_lower or "cama" in text_lower:
                    if bedrooms is None:
                        bedrooms = val
                elif "bañ" in text_lower or "banio" in text_lower or "bath" in text_lower or "baño" in text_lower:
                    if bathrooms is None:
                        bathrooms = val
                elif ("terreno" in text_lower or "total" in text_lower) and (
                    "m²" in text or "m2" in text_lower or "metros" in text_lower
                ):
                    if total_area_m2 is None:
                        total_area_m2 = float(val_str)
                elif ("constru" in text_lower or "edificado" in text_lower or "cubiert" in text_lower) and (
                    "m²" in text or "m2" in text_lower
                ):
                    if built_area_m2 is None:
                        built_area_m2 = float(val_str)
                elif "estacion" in text_lower or "garage" in text_lower or "cochera" in text_lower:
                    if parking is None:
                        parking = val
                elif "año" in text_lower or "antigü" in text_lower:
                    if year_built is None:
                        year_built = val

            if total_area_m2 is None:
                area_el = sel.css(
                    ".property-area span::text, .area-size::text, "
                    ".list-3-cols li:contains('m²')::text"
                ).get()
                if area_el:
                    m = re.search(r"([\d.,]+)\s*m²", area_el)
                    if m:
                        total_area_m2 = float(m.group(1).replace(".", "").replace(",", "."))

        if not images:
            for img in sel.css(
                ".gallery-item img, .property-gallery img, "
                "#property-gallery img, .slides img"
            ):
                src = img.attrib.get("src", "") or img.attrib.get("data-src", "")
                if src and "propiedadesya" in src:
                    src = re.sub(r"-\d+x\d+", "", src)
                    if src not in images:
                        images.append(src)

        video_url = None
        iframe = sel.css(
            "iframe[src*='youtube'], iframe[src*='youtu.be']"
        ).attrib.get("src")
        if iframe:
            video_url = iframe

        if not contact_phone:
            phone_el = sel.css(
                "a[href^='tel:']::attr(href)"
            ).get()
            if phone_el:
                contact_phone = phone_el.replace("tel:", "")
        if not contact_name:
            contact_name = sel.css(
                ".agent-name::text, .agent-info .name::text, "
                ".property-contact .media-body .title::text"
            ).get("").strip() or None

        features = []
        for feat_el in sel.css(
            ".amenities-list li span::text, .features-list li::text, "
            ".property-features li span::text"
        ):
            feat = feat_el.get().strip()
            if feat:
                features.append(feat)

        if not coordinates:
            maps_link = sel.css(
                'a[href*="maps.google.com"]::attr(href)'
            ).get()
            if maps_link:
                m = re.search(r"q=([-\d.]+),([-\d.]+)", maps_link)
                if m:
                    try:
                        coordinates = (float(m.group(1)), float(m.group(2)))
                    except ValueError:
                        pass

        listing_date = None
        date_el = sel.css(
            ".property-date span::text, .listing-date span::text, "
            ".item-date::text"
        ).get()
        if date_el:
            date_el = date_el.strip()
            try:
                listing_date = datetime.strptime(date_el, "%B %d, %Y").date()
            except ValueError:
                pass
        if not listing_date:
            modified_el = sel.css(
                ".property-updated span::text"
            ).get()
            if modified_el:
                modified_el = modified_el.strip()
                try:
                    listing_date = datetime.strptime(modified_el, "%B %d, %Y").date()
                except ValueError:
                    pass

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
            address=address,
            coordinates=coordinates,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            total_area_m2=total_area_m2,
            built_area_m2=built_area_m2,
            parking_spots=parking,
            year_built=year_built,
            description=description,
            features=features,
            images=images,
            video_url=video_url,
            contact_name=contact_name,
            contact_phone=contact_phone,
            listing_date=listing_date,
            status=status,
        )

    def _try_api(self) -> list[PropertyListing]:
        listings = []
        page = 1

        while page <= self.config.max_pages:
            url = f"{WP_API_URL}?per_page=50&page={page}"
            html = self.fetch(url)
            if not html:
                break

            try:
                data = json.loads(html)
            except json.JSONDecodeError:
                break

            if not data:
                break

            for item in data:
                listing = self._api_extract_listing(item)
                if listing:
                    listings.append(listing)

            if len(data) < 50:
                break

            page += 1

        return listings

    def extract_listings(self, html: str, source_url: str) -> list[dict]:
        return []

    def extract_detail(self, url: str) -> PropertyListing | None:
        return self._html_extract_listing(url)

    def run(self):
        print(f"[{self.config.name}] Scraping via HTML parsing.")
        super().run()

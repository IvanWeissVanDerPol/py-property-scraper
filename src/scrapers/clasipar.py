"""Scraper for Clasipar (clasipar.paraguay.com) — Paraguay's largest classifieds platform."""

import re
from datetime import date, datetime

from parsel import Selector

from src.models.property import PropertyListing, SourceConfig
from src.scrapers.base import BaseScraper
from src.utils.storage import save_jsonl
from config.settings import DATA_DIR

_AGENCY_TYPES = {"inmobiliaria": True, "particular": False}

_PROPERTY_TYPE_MAP = {
    "casas": "casa",
    "departamentos": "departamento",
    "terrenos": "terreno",
    "locales-oficinas-salones": "local",
}


class ClasiparScraper(BaseScraper):
    def __init__(self):
        config = SourceConfig(
            name="clasipar",
            display_name="Clasipar",
            base_url="https://clasipar.paraguay.com",
            search_urls=[
                "/venta/casas",
                "/venta/departamentos",
                "/venta/terrenos",
                "/inmuebles/locales-oficinas-salones",
            ],
            max_pages=370,
        )
        super().__init__(config)

    def _extract_listing_urls(self, sel: Selector) -> list[str]:
        urls = []
        for article in sel.css("article.box-anuncio"):
            href = article.css("a::attr(href)").get()
            if href and "/inmuebles/" in href:
                if href.startswith("/"):
                    href = self.config.base_url + href
                urls.append(href)
        return urls

    def _extract_next_page(self, sel: Selector) -> str | None:
        return None

    def extract_listings(self, html: str, source_url: str) -> list[dict]:
        return []

    def extract_detail(self, url: str) -> PropertyListing | None:
        html = self.fetch(url)
        if not html:
            return None
        text = html

        title = self._extract_title(text, url)
        external_id = self._extract_id(text)
        price_pyg, price_usd = self._extract_prices(text)
        currency = "USD" if price_usd and not price_pyg else "PYG"

        department = self._extract_field(text, "Departamento")
        city = self._extract_field(text, "Ciudad")
        zone = self._extract_field(text, "Zona")
        raw_bedrooms = self._extract_number(text, "Dormitorios")
        raw_bathrooms = self._extract_number(text, "Baños")
        raw_total_area = self._extract_number_safe(text, "Superficie de terreno", 1_000_000)
        raw_built_area = self._extract_number_safe(text, "Superficie construida", 1_000_000)

        listing_date_str = self._extract_field(text, "Publicado el")
        listing_date = self._parse_date(listing_date_str) if listing_date_str else None

        agency = self._extract_agency(text)

        property_type = self._detect_property_type(url, title)

        description = self._extract_description(text)

        images = self._extract_images(text)

        return PropertyListing(
            source=self.config.name,
            source_url=url,
            external_id=external_id,
            title=title,
            property_type=property_type,
            price=price_pyg,
            price_usd=price_usd,
            currency=currency,
            city=city,
            district=department,
            zone=zone,
            bedrooms=raw_bedrooms,
            bathrooms=raw_bathrooms,
            total_area_m2=raw_total_area,
            built_area_m2=raw_built_area,
            description=description,
            agency=agency,
            listing_date=listing_date,
            images=images,
        )

    def run(self):
        seen_urls = set()
        for search_path in self.config.search_urls:
            page_num = 1
            while page_num <= self.config.max_pages:
                if page_num == 1:
                    url = f"{self.config.base_url}{search_path}"
                else:
                    url = f"{self.config.base_url}{search_path}?pagina={page_num}"
                html = self.fetch(url)
                if not html:
                    break
                sel = Selector(html)
                listing_urls, _ = self.parse_search_page(html)

                if not listing_urls:
                    break

                for listing_url in listing_urls:
                    if listing_url in seen_urls:
                        continue
                    seen_urls.add(listing_url)
                    listing = self.extract_detail(listing_url)
                    if listing:
                        save_jsonl(listing, DATA_DIR, self.config.name)

                print(f"[{self.config.name}] Page {page_num}: {len(listing_urls)} listings")
                page_num += 1

        print(f"[{self.config.name}] Done. Scraped {len(seen_urls)} unique listings.")

    _SEO_SPAM_PATTERNS = [
        r"<span[^>]*style=\"?'?font-size:\s*0[^>]*>.*?</span>",
        r"Los\s+mejores\s+anuncios\s+clasificados\s+de",
        r"El\s+mejor\s+clasificado",
        r"Fuente\s+del\s+anuncio:\s*https?://\S+",
    ]

    def _clean_seo_spam(self, text: str) -> str:
        for pat in self._SEO_SPAM_PATTERNS:
            text = re.sub(pat, "", text, flags=re.DOTALL | re.IGNORECASE)
        return text

    def _extract_title(self, text: str, url: str) -> str:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.DOTALL)
        if m:
            raw = self._clean_seo_spam(m.group(1))
            raw = re.sub(r"<[^>]+>", "", raw)
            raw = re.sub(r"\s+", " ", raw).strip()
            if raw:
                return raw
        m2 = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
        if m2:
            raw = m2.group(1).strip()
            raw = re.sub(r"\s+#\d+\s*\|.*", "", raw).strip()
            if raw:
                return raw
        return url.rstrip("/").split("/")[-1].replace("-", " ").title()

    def _extract_id(self, text: str) -> str | None:
        m = re.search(r"Nro\.\s*de\s*Anuncio[:\s]*</span>[^<]*<[^>]*>(\d+)", text, re.IGNORECASE)
        if m:
            return m.group(1)
        m2 = re.search(r"Nro\.\s*de\s*Anuncio[:\s]*(\d+)", text, re.IGNORECASE)
        if m2:
            return m2.group(1)
        return None

    def _extract_prices(self, text: str) -> tuple[float | None, float | None]:
        price_pyg = None
        price_usd = None

        pyg_matches = re.findall(r"(?<!US\$)Gs\.\s*([\d.]+)", text)
        if pyg_matches:
            raw = pyg_matches[0].replace(".", "")
            try:
                price_pyg = float(raw)
            except ValueError:
                pass

        usd_matches = re.findall(r"US\$\.[\s]*([\d.,]+)", text)
        if usd_matches:
            raw = usd_matches[0]
            raw = raw.replace(".", "").replace(",", ".")
            try:
                price_usd = float(raw)
            except ValueError:
                pass

        # Sanity: improbable values → None
        if price_usd is not None and price_usd > 10_000_000:
            price_usd = None
        if price_pyg is not None and 0 < price_pyg < 1000:
            price_pyg = None

        return price_pyg, price_usd

    @staticmethod
    def _strip_html(val: str) -> str:
        val = re.sub(r'<span\s+style="font-size:\s*0[^>]*>.*?</span>', '', val, flags=re.DOTALL | re.IGNORECASE)
        val = re.sub(r'<[^>]+>', '', val)
        val = re.sub(r'\s+', ' ', val).strip()
        return val

    def _extract_field(self, text: str, field: str) -> str | None:
        escaped = re.escape(field)
        patterns = [
            escaped + r"[:\s]*</span>(?:[^<]*(?:<(?!/?strong>)[^>]*>)?)*?<strong>([^<]+)",
            escaped + r"[:\s]*<strong>([^<]+)",
            escaped + r"[:\s]*\n*([^\n]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val:
                    return val
        return None

    _NUM_CAPS = {"Dormitorios": 20, "Baños": 15, "Ba\u00f1os": 15}

    def _extract_number(self, text: str, keyword: str) -> int | None:
        patterns = [
            re.escape(keyword) + r"[^:]*:[^<]*<strong>(\d+)",
            re.escape(keyword) + r"[:\s]*</span>[^<]*<[^>]*>\s*(\d+)",
            re.escape(keyword) + r"[:\s]*<strong>(\d+)",
            re.escape(keyword) + r"[:\s]*\*\*(\d+)\*\*",
            re.escape(keyword) + r"[:\s]*\n*(\d+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                try:
                    val = int(m.group(1))
                    cap = self._NUM_CAPS.get(keyword)
                    if cap is not None and val > cap:
                        return None
                    return val
                except ValueError:
                    pass
        return None

    def _extract_number_safe(self, text: str, keyword: str, cap: float) -> float | None:
        patterns = [
            re.escape(keyword) + r"[^:]*:[^<]*<strong>([\d.,]+)",
            re.escape(keyword) + r"[:\s]*</span>[^<]*<[^>]*>\s*([\d.,]+)",
            re.escape(keyword) + r"[:\s]*<strong>([\d.,]+)",
            re.escape(keyword) + r"[:\s]*\*\*([\d.,]+)\*\*",
            re.escape(keyword) + r"[:\s]*\n*([\d.,]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                raw = m.group(1).replace(".", "").replace(",", ".")
                try:
                    val = float(raw)
                    if val > cap:
                        return None
                    return val
                except ValueError:
                    pass
        return None

    def _parse_date(self, date_str: str) -> date | None:
        date_str = date_str.strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def _extract_agency(self, text: str) -> str | None:
        m = re.search(r"Ofrecido por[:\s]*<strong>([^<]+)", text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip().lower()
            is_agency = _AGENCY_TYPES.get(raw)
            if is_agency is True:
                return raw.capitalize()
            elif is_agency is False:
                return raw.capitalize()
        m2 = re.search(r"Ofrecido por:\s*(Particular|Inmobiliaria)", text, re.IGNORECASE)
        if m2:
            return m2.group(1).strip().capitalize()
        return None

    def _detect_property_type(self, url: str, title: str) -> str:
        path_lower = url.lower()
        for path_seg, prop_type in _PROPERTY_TYPE_MAP.items():
            if path_seg in path_lower:
                return prop_type
        title_lower = title.lower()
        if "terreno" in title_lower or "lote" in title_lower:
            return "terreno"
        if "departamento" in title_lower or "depto" in title_lower or "monoambiente" in title_lower:
            return "departamento"
        if "local" in title_lower or "oficina" in title_lower or "salon" in title_lower:
            return "local"
        if "casa" in title_lower:
            return "casa"
        return "casa"

    def _extract_description(self, text: str) -> str:
        m = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)',
            text,
            re.IGNORECASE,
        )
        if m:
            raw = self._clean_seo_spam(m.group(1)).strip()
            if raw:
                return raw
        m2 = re.search(
            r"<h2[^>]*class=\"[^\"]*tit-detalle[^\"]*\"[^>]*>.*?</h2>(.*?)(?:<h[234]|</div>\s*<div[^>]*class=)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if m2:
            raw = re.sub(r"<script[^>]*>.*?</script>", "", m2.group(1), flags=re.DOTALL)
            raw = re.sub(r"<[^>]+>", " ", raw)
            raw = re.sub(r"\s+", " ", raw).strip()
            raw = self._clean_seo_spam(raw)
            return raw
        return ""

    def _extract_images(self, text: str) -> list[str]:
        urls = re.findall(
            r"https://clasicdn\.paraguay\.com/pictures/[^\s\"'>]+L\.(?:webp|jpg|jpeg|png)",
            text,
        )
        seen = set()
        unique = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        return unique

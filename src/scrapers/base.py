from abc import ABC, abstractmethod
from pathlib import Path

import httpx
from parsel import Selector

from config.settings import DATA_DIR
from src.models.property import PropertyListing, SourceConfig
from src.utils.http import get_client, rate_limit
from src.utils.storage import save_jsonl


class BaseScraper(ABC):
    """Base class for all property scrapers."""

    def __init__(self, config: SourceConfig):
        self.config = config
        self.output_dir = DATA_DIR
        self.client: httpx.Client = get_client()

    @abstractmethod
    def extract_listings(self, html: str, source_url: str) -> list[dict]:
        ...

    @abstractmethod
    def extract_detail(self, url: str) -> PropertyListing | None:
        ...

    def parse_search_page(self, html: str) -> tuple[list[str], str | None]:
        """Returns (listing_urls, next_page_url)."""
        sel = Selector(html)
        urls = self._extract_listing_urls(sel)
        next_page = self._extract_next_page(sel)
        return urls, next_page

    def _extract_listing_urls(self, sel: Selector) -> list[str]:
        raise NotImplementedError

    def _extract_next_page(self, sel: Selector) -> str | None:
        raise NotImplementedError

    @rate_limit(2.0)
    def fetch(self, url: str) -> str | None:
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as e:
            print(f"[{self.config.name}] Error fetching {url}: {e}")
            return None

    def run(self):
        """Main entry point: crawl search pages then scrape details."""
        seen_urls = set()
        for search_path in self.config.search_urls:
            next_url = f"{self.config.base_url}{search_path}"
            page_count = 0
            while next_url and page_count < self.config.max_pages:
                html = self.fetch(next_url)
                if not html:
                    break
                listing_urls, next_url = self.parse_search_page(html)

                for url in listing_urls:
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    listing = self.extract_detail(url)
                    if listing:
                        save_jsonl(listing, self.output_dir, self.config.name)

                page_count += 1
                print(f"[{self.config.name}] Page {page_count}: {len(listing_urls)} listings")

        print(f"[{self.config.name}] Done. Scraped {len(seen_urls)} unique listings.")

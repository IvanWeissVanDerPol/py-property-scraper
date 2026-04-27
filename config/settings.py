"""Scraping settings and defaults."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
DEFAULT_DELAY = 2.0  # seconds between requests

# Output format: jsonl or csv
OUTPUT_FORMAT = "jsonl"

# Env-overridable settings
SCRAPER_RATE_LIMIT = float(os.getenv("SCRAPER_RATE_LIMIT", str(DEFAULT_DELAY)))
SCRAPER_MAX_PAGES = int(os.getenv("SCRAPER_MAX_PAGES", "50"))
SCRAPER_OUTPUT_DIR = Path(os.getenv("SCRAPER_OUTPUT_DIR", str(DATA_DIR)))
SCRAPER_OUTPUT_FORMAT = os.getenv("SCRAPER_OUTPUT_FORMAT", OUTPUT_FORMAT)

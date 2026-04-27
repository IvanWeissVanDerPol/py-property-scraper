import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.clasipar import ClasiparScraper
from src.scrapers.infocasas import InfoCasasScraper
from src.scrapers.inmueblespy import InmueblesPYScraper
from src.scrapers.propiedadesya import PropiedadesYAScraper
from src.scrapers.buscocasita import BuscocasitaScraper
from src.scrapers.agentiz import AgentizScraper
from src.scrapers.mercadolibre import run as run_mercadolibre
from config.settings import DATA_DIR


ALL_SCRAPERS = {
    "clasipar": ClasiparScraper,
    "infocasas": InfoCasasScraper,
    "inmueblespy": InmueblesPYScraper,
    "propiedadesya": PropiedadesYAScraper,
    "buscocasita": BuscocasitaScraper,
    "agentiz": AgentizScraper,
    "mercadolibre": "mercadolibre_plugin",
}


def run_mercadolibre_plugin(limit: int | None = None):
    run_mercadolibre(max_pages=limit or 6)


def run_all(limit: int | None = None):
    for name, cls in ALL_SCRAPERS.items():
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}")
        if name == "mercadolibre":
            run_mercadolibre_plugin(limit)
            continue
        scraper = cls()
        if limit:
            scraper.config.max_pages = limit
        scraper.run()

    print("\n\n=== Summary ===")
    for source_dir in sorted(DATA_DIR.iterdir()):
        if source_dir.is_dir():
            filepath = source_dir / "listings.jsonl"
            if filepath.exists():
                count = sum(1 for _ in open(filepath))
                size = filepath.stat().st_size
                print(f"  {source_dir.name:15s} {count:5d} listings ({size // 1024} KB)")


def run_one(name: str, limit: int | None = None):
    cls = ALL_SCRAPERS.get(name)
    if not cls:
        print(f"Unknown scraper: {name}. Available: {list(ALL_SCRAPERS.keys())}")
        return
    if name == "mercadolibre":
        run_mercadolibre_plugin(limit)
        return
    scraper = cls()
    if limit:
        scraper.config.max_pages = limit
    scraper.run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Paraguay Property Scraper")
    parser.add_argument("--source", "-s", help="Run only one source (e.g., clasipar)")
    parser.add_argument("--limit", "-l", type=int, help="Max pages to scrape per source")
    parser.add_argument("--list-sources", action="store_true", help="List available sources")
    args = parser.parse_args()

    if args.list_sources:
        print("Available sources:")
        for name in ALL_SCRAPERS:
            print(f"  {name}")
        sys.exit(0)

    if args.source:
        run_one(args.source, args.limit)
    else:
        run_all(args.limit)

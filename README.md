# 🏠 Paraguay Property Scraper

Web scraping and data aggregation for property listings in Paraguay. Collects house, apartment, and land sale details from all major Paraguayan real estate platforms.

## Sources Found

### Tier 1 — Major Portals (structured, scrapeable)

| Source | URL | Type | Notes |
|---|---|---|---|
| **InfoCasas** | https://www.infocasas.com.py/ | 🇵🇾 Leading portal | Largest PY-specific inventory, well-structured |
| **Clasipar** | https://clasipar.paraguay.com/venta/casas | 🇵🇾 Classifieds | Massive inventory, simple HTML |
| **MercadoLibre Inmuebles** | https://inmuebles.mercadolibre.com.py/ | 🇵🇾 Marketplace | Standardized listing format |
| **InmueblesPY** | https://inmueblespy.com/ | 🇵🇾 Portal | Paraguayan-specific portal |
| **PropiedadesYA** | https://propiedadesya.com.py/ | 🇵🇾 Portal | PY real estate portal |
| **Buscocasita Paraguay** | https://paraguay.buscocasita.com/ | 🇵🇾 Portal | Free listing portal |
| **Agentiz Paraguay** | https://py.agentiz.com/ | 🇵🇾 Portal | Free real estate ads |

### Tier 2 — International Franchises (Paraguay-specific)

| Source | URL | Type | Notes |
|---|---|---|---|
| **Century 21 Paraguay** | https://century21.com.py/ | 🇵🇾 Franchise | Local franchise listings |
| **RE/MAX Paraguay** | https://www.remax.com.py/listings | 🌐 Franchise | Global franchise PY listings |
| **Coldwell Banker Paraguay** | https://coldwellbanker.com.py/ | 🌐 Franchise | Premium properties |
| **Paraguay Real Estate** | https://paraguayrealestate.com.py/ | 🇵🇾 Agency | Local agency |
| **OmniMLS** | https://omnimls.com/v/results/type_house/listing-type_sale/in-country_paraguay | 🌐 MLS | International MLS |

### Tier 3 — International Aggregators

| Source | URL | Type | Notes |
|---|---|---|---|
| **Realtor.com International** | https://www.realtor.com/international/py/ | 🌐 Global | Realtor.com PY section |
| **Zonaprop** | https://www.zonaprop.com.ar/inmuebles-paraguay.html | 🌐 Regional | Argentine portal with PY listings |
| **LatinCarib** | https://latincarib.com/country/paraguay/ | 🌐 Regional | Caribbean/LATAM real estate |
| **Facebook Groups** | `Terrenos Lotes Casas Propiedades en Paraguay` | 📱 Social | Large active groups |
| **Facebook Groups** | `Clasificados Alquileres y Ventas de inmuebles PY` | 📱 Social | Active community |

### Tier 4 — Individual Agencies

| Source | URL | Notes |
|---|---|---|
| **CR Inmobiliaria** | https://www.crinmobiliaria.com.py/ | Local agency |
| **Latinpar / ClasInmuebles** | https://latinpar.com.py/ | Listing service |
| Various smaller agencies | Various | Less structured, harder to scrape |

## Architecture

```
py-property-scraper/
├── src/
│   ├── scrapers/          # Individual site scrapers
│   │   ├── infocasas.py
│   │   ├── clasipar.py
│   │   ├── mercadolibre.py
│   │   ├── inmueblespy.py
│   │   ├── centur21.py
│   │   └── ...
│   ├── models/            # Data models (Pydantic)
│   │   └── property.py
│   ├── utils/             # Shared utilities
│   │   ├── http.py        # Request handling, proxies
│   │   ├── parser.py      # HTML parsing helpers
│   │   └── storage.py     # Save to JSON/CSV/DB
│   └── orchestrator.py    # Run all scrapers, merge results
├── config/
│   ├── sources.yaml       # Source definitions
│   └── settings.py        # Scraping settings
├── data/                  # Output data
├── notebooks/             # Analysis notebooks
├── research/              # Documentation & research
│   ├── sources.md         # This source inventory
│   ├── site-structures.md # Each site's DOM structure
│   └── anti-scraping.md   # Rate limits, blocks, workarounds
├── output/                # Scraped results (JSON/CSV)
├── requirements.txt
└── README.md
```

## Data Model

```python
class PropertyListing(BaseModel):
    source: str                    # Which site it came from
    source_url: str                # Original listing URL
    title: str                     # Listing title
    property_type: str             # casa / departamento / terreno / local / etc
    price: Optional[float]         # In PYG (Guaraníes)
    price_usd: Optional[float]     # In USD if listed
    currency: str                  # PYG / USD
    location: str                  # City, neighborhood
    address: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    area_m2: Optional[float]       # Total area in m²
    area_cubierta: Optional[float] # Covered/built area in m²
    description: str               # Full description text
    images: list[str]              # Image URLs
    features: list[str]            # Amenities: garage, pool, etc.
    contact_phone: Optional[str]
    listing_date: Optional[date]
    scraped_at: datetime
```

## Tech Stack (recommended)

| Component | Tool | Why |
|---|---|---|
| HTTP | `httpx` | Async, HTTP/2, connection pooling |
| Parsing | `parsel` / `beautifulsoup4` | Battle-tested HTML parsing |
| JS-heavy | `playwright` (via skill) | For SPAs (InfoCasas may need it) |
| Anti-block | `scrapy-rotating-proxies` | Avoid IP bans |
| Data | `pydantic` | Validation + schemas |
| Storage | JSONL → DuckDB | Simple, fast for analysis |
| Scheduling | cron / `schedule` | Daily/weekly runs |

## Quick Start

```bash
# Setup
cd py-property-scraper
python -m venv venv
source venv/bin/activate
pip install httpx parsel pydantic

# Run a single scraper
python -m src.scrapers.infocasas

# Run all
python -m src.orchestrator
```

## Ethical Notes

- Respect `robots.txt` and rate limits
- Add delays between requests (1-3s)
- Identify with a user-agent
- Don't re-scrape same URLs each run — cache
- This is for personal/analytical use, not resale of data

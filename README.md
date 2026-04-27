# Paraguay Property Scraper

Web scraping and data aggregation for property listings across Paraguay. Collects house, apartment, land, and commercial property details from **8 online sources**.

**Dataset: 11,760 raw → 11,171 unique listings** — 24MB merged JSONL, 10MB CSV.

## Quick Start

```bash
make install          # setup venv + install deps
make run              # run ALL scrapers (takes hours)
make run-source s=infocasas   # run one scraper
make pipeline         # clean → merge → csv → catalog
make catalog          # print summary stats
```

## Sources

| # | Source | Listings | Method | GPS | USD Price |
|---|---|---|---|---|---|
| 1 | **InfoCasas** 🔵 | 8,016 | Direct HTTP + JSON | ✅ 100% | ✅ 99% |
| 2 | **Clasipar** 🟧 | 1,834 | Direct HTTP + Regex | ❌ | ✅ 74% |
| 3 | **MercadoLibre PY** 🟤 | 986 | Playwright (headless browser) | ❌ | ✅ 40% |
| 4 | **InmueblesPY** 🟢 | 249 | Direct HTTP + JSON-LD | ✅ 54% | ⚠️ 2% |
| 5 | **PropiedadesYA** 🟣 | 46 | WordPress REST API + HTML | ✅ 98% | ✅ 43% |
| 6 | **RE/MAX Paraguay** 🔴 | 24 | Playwright (headless browser) | ❌ | ✅ 42% |
| 7 | **OmniMLS** ⚪ | 7 | Playwright (headless browser) | ❌ | ⚠️ |
| 8 | **Buscocasita** 🟡 | 9 | Direct HTTP | ❌ | ⚠️ |
| | **TOTAL** | **11,171** | | **73%** | **87%** |

### Unscrapable Sources

| Source | Reason |
|---|---|
| **Century 21 PY** | Empty site — no listing directory available |
| **Zonaprop PY** | Cloudflare protected — cannot bypass |
| **Agentiz PY** | JS-rendered ad-posting form, ~25 PY listings total |
| **Coldwell Banker PY** | Too small to justify effort |

## Data Model

Each listing is a JSON object with these fields:

| Field | Type | Description | Coverage |
|---|---|---|---|
| `title` | string | Listing title | 98% |
| `price` | float | Price in PYG (Guaraníes) | 94% |
| `price_usd` | float | Price in USD | 87% |
| `property_type` | string | casa / departamento / terreno / local / etc | 99% |
| `city` | string | City or department | 98% |
| `district` | string | Neighborhood or district | — |
| `bedrooms` | int | 0=studio/land, 1-10+ | 60% |
| `bathrooms` | int | Number of bathrooms | 61% |
| `total_area_m2` | float | Total land area in m² | 72% |
| `built_area_m2` | float | Constructed area in m² | 57% |
| `coordinates` | [lat, lon] | GPS coordinates | 73% |
| `description` | string | Full listing description | 88% |
| `images` | list[str] | Image URLs | 97% |
| `source_url` | string | Original listing link | 100% |

## Dataset

```
data/
├── infocasas/listings.jsonl            # 8,016 raw
├── clasipar/listings.jsonl             # 1,834 raw
├── mercadolibre/listings.jsonl         # 986 raw
├── inmueblespy/listings.jsonl          # 249 raw
├── propiedadesya/listings.jsonl        # 46 raw
├── remax/listings.jsonl                # 24 raw
├── omnimls/listings.jsonl              # 7 raw
├── buscocasita/listings.jsonl          # 9 raw
└── _merged/
    ├── listings.jsonl                  # 11,171 merged (24MB)
    └── listings.csv                    # 11,171 rows for spreadsheets (10MB)
```

## Geographic Distribution

| City / Department | Listings | % |
|---|---|---|
| Asunción | 4,865 | 43% |
| Central | 3,263 | 29% |
| Cordillera | 580 | 5% |
| Alto Paraná | 204 | 2% |
| Luque | 126 | 1% |
| Fernando de la Mora | 114 | 1% |
| San Lorenzo | 89 | <1% |
| 700+ other locations | remaining | |

## Price Analysis (USD)

| Property Type | Median Price | Count |
|---|---|---|
| **Casa** (house) | **$180,000** | 2,602 |
| **Terreno** (land) | **$130,000** | 2,474 |
| **Departamento** (apartment) | **$105,000** | 2,480 |
| Overall median | $140,000 | 9,762 |

## Property Type Distribution

```
casa         ██████████████████████████████   2,947 (26%)
terreno      ████████████████████████████    2,806 (25%)
departamento █████████████████████████       2,550 (23%)
local        ████████████████                1,591 (14%)
otro         █████████                       964  (9%)
country      █                               107  (1%)
oficina                                       49  (<1%)
cochera                                       31  (<1%)
```

## Data Quality

- **HTML stripped**: All text fields cleaned of HTML tags and SEO spam
- **Prices sanity-checked**: Values >$10M USD set to null (PYG/USD confusion), values <100 set to null
- **Bedrooms capped**: Values >20 set to null (Clasipar parsing errors)
- **Deduplicated**: All listings deduplicated by URL across sources
- **7,134 issues fixed** across all sources by the cleaning pipeline

## CLI

```bash
python -m src.orchestrator                    # run all scrapers
python -m src.orchestrator --source infocasas # run one source
python -m src.orchestrator --limit 10         # limit pages per source
python -m src.orchestrator --list-sources     # list available
```

## Pipeline

```bash
make quality-report    # clean all data
make merge             # deduplicate across sources
make csv               # export unified CSV
make catalog           # print summary statistics
make pipeline          # all of the above
```

## Technical Stack

| Component | Tool |
|---|---|
| HTTP | `httpx` (async-capable) |
| HTML parsing | `parsel` (CSS selectors) |
| Browser automation | `playwright` |
| Data validation | `pydantic` |
| Storage | JSONL (append-only) |
| Cleaning | Custom pipeline (HTML strip, sanity checks) |
| Merge | URL-based dedup with source weighting |
| Config | `python-dotenv` + settings.py |

## License

© 2026 — Data collected from public sources. Use responsibly.

# Paraguay Property Data Catalog

> Generated: April 27, 2026 — 4,526 raw listings merged into 3,911 unique.

## Overview

We scraped **5 Paraguayan property listing sources**, producing **4,526 raw listings** which deduplicate to **3,911 unique properties** across Paraguay. Data is stored in three formats: raw (per-source JSONL), merged (JSONL), and unified CSV.

## Source Comparison

| Source | Raw | Unique | Listings / effort | Data Quality | GPS |
|---|---|---|---|---|---|
| InfoCasas | 2,944 | 2,883 | 🔥 131 pages of 7,071 available | Best — full structured data | ✅ 100% |
| Clasipar | 1,255 | 1,255 | 🔥 50 pages of ~200 available | Good — prices, city, zone, images | ❌ |
| InmueblesPY | 272 | 128 | ✅ all available pages | Good — coords, beds, baths, area | ✅ 57% |
| PropiedadesYA | 46 | 46 | ✅ all available (~46 total) | Decent — coords, contact info, USD prices | ✅ 98% |
| Buscocasita | 9 | 9 | ✅ all available | Basic | ❌ |
| **Total** | **4,526** | **3,911** | | | **69% with GPS** |

## What Data Is Available

### ✅ 100% Coverage (present on nearly every listing)
- **Price** — 4,088 listings (90%) have PYG price, 3,933 (87%) have USD price
- **Title** — descriptive listing title
- **Source URL** — original listing link
- **Property type** — classified into 13 types: departamento, terreno, casa, local, country, oficina, etc.
- **City / department** — 2,252 listings in Asunción, 1,003 in Central department
- **Images** — 4,344 listings (96%) have at least one image

### ✅ High Coverage (60-95%)
- **GPS coordinates** — 3,145 listings (69%) have lat/lon, concentrated in InfoCasas + InmueblesPY
- **Bedrooms** — 2,941 (65%) have bedroom count
- **District / neighborhood** — varies by source (71-100% in Clasipar/InfoCasas)
- **Description** — 4,259 (94%) have full description text

### ⚠️ Partial Coverage (20-60%)
- **Bathrooms** — 2,234 (49%)
- **Total area (m²)** — 3,373 (74%)
- **Built area (m²)** — 3,037 (67%)
- **Agency / seller name** — varies
- **Listing date** — only Clasipar + InfoCasas

### ❌ Sparse (<10%)
- **Floors, parking spots, year built, features/amenities** — mostly in InfoCasas data
- **Contact phone/email** — most sites hide behind login/captcha
- **Video tours** — almost none

## Property Types Distribution

| Type | Count | % |
|---|---|---|
| Departamento (apartment) | 1,097 | 24% |
| Terreno (land) | 1,002 | 22% |
| Local (commercial) | 988 | 22% |
| Casa (house) | 986 | 22% |
| Otro (other) | 247 | 5% |
| Country (country house) | 45 | 1% |
| Oficina (office) | 21 | <1% |
| Cochera (garage) | 18 | <1% |
| Others (estancia, edificio, galpón) | 5 | <1% |

Note: Clasipar's "local" category inflates commercial listings. InfoCasas has the best casa/departamento balance.

## Geographic Distribution

| City/Department | Listings |
|---|---|
| Asunción | 2,252 (50%) |
| Central department | 1,003 (22%) |
| Cordillera | 222 (5%) |
| Alto Paraná | 121 (3%) |
| Fernando de la Mora | 86 (2%) |
| Luque | 73 (2%) |
| San Lorenzo | 63 (1%) |
| Lambaré | 51 (1%) |
| Ciudad del Este | 31 |
| Encarnación | 29 |
| 50+ other cities | remainder |

## Price Landscape

### In PYG (Guaraníes)

| Category | Range | Median |
|---|---|---|
| All properties | 1,350 - 550B | ~300k-500M |
| Houses (casa) | ~200M - 5B | ~800M |
| Apartments (departamento) | ~50M - 2B | ~350M |
| Land (terreno) | ~30M - 10B | ~500M |

### In USD

| Category | Range | Median |
|---|---|---|
| All properties | $11 - $3.6B | ~$150k |
| Houses | $50k - $1M | ~$250k |
| Apartments | $30k - $500k | ~$140k |
| Land | $20k - $5M | ~$200k |

Note: Some listings have unrealistic price extremes ($11, 550B PYG) — likely data entry errors or the site mixing PYG/USD.

## Bedroom Distribution

| Bedrooms | Count | % |
|---|---|---|
| 0 (studio/land) | 485 | 16% |
| 1 | 700 | 24% |
| 2 | 620 | 21% |
| 3 | 649 | 22% |
| 4 | 253 | 9% |
| 5+ | 234 | 8% |

## File Organization

```
/home/ai-whisperers/py-property-scraper/
├── data/
│   ├── clasipar/listings.jsonl          # 1,255 raw listings (14MB)
│   ├── infocasas/listings.jsonl         # 2,944 raw listings (8MB)
│   ├── inmueblespy/listings.jsonl       # 272 raw listings (672K)
│   ├── propiedadesya/listings.jsonl     # 46 raw listings (148K)
│   ├── buscocasita/listings.jsonl       # 9 raw listings (16K)
│   └── _merged/
│       ├── listings.jsonl               # 3,911 deduplicated merged (21MB)
│       └── listings.csv                 # 3,911 unified CSV (16MB)
├── research/
│   ├── sources.md                       # Source inventory
│   ├── site-analysis.md                 # Live HTML structure analysis
│   └── data-catalog.md                  # This file
└── src/
    ├── scrapers/                        # 6 scrapers
    ├── models/property.py               # Pydantic schema
    └── utils/merge.py                   # Merge/catalog/CSV tools
```

## How to Use

### Quick analysis
```bash
# Load in Python
import json
with open("data/_merged/listings.jsonl") as f:
    listings = [json.loads(l) for l in f]

# Filter by price
cheap_houses = [l for l in listings 
    if l.get("property_type") == "casa" 
    and l.get("price_usd") 
    and l["price_usd"] < 100000]

# Filter by GPS for mapping
with_coords = [l for l in listings if l.get("coordinates")]
```

### Import into DuckDB for SQL
```sql
CREATE TABLE properties AS 
SELECT * FROM read_json_auto('data/_merged/listings.jsonl');

SELECT city, COUNT(*) as count, 
       AVG(price_usd) as avg_price_usd
FROM properties 
WHERE price_usd > 1000 
GROUP BY city 
ORDER BY count DESC;
```

### Open CSV in any spreadsheet
```bash
open data/_merged/listings.csv
# or import into Google Sheets / Excel
```

## Quality Notes

1. **Prices**: Some Clasipar listings have extreme values ($12, 550B PYG) — filter with `price_usd > 1000 AND price_usd < 10000000` for realistic ranges
2. **Clasipar bedroom data** has some outliers (68, 175, 1500 bedrooms) — likely parsing errors from the SEO-spammed HTML
3. **Agentiz** (py.agentiz.com) was not scrapable — JS-rendered search pages, only ~25 total PY listings anyway
4. **PropiedadesYA** only has 46 total listings on the platform — not a volume source
5. **Cross-source duplicates** were minimal (<5%), mostly high-end properties listed by multiple agencies

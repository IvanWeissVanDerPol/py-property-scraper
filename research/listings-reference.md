# Paraguay Property Listings — Data Reference

> **File: `data/_merged/listings.jsonl`** — 11,171 unique listings
> **Also available as CSV**: `data/_merged/listings.csv`

---

## Data Structure

Each listing is a single JSON object with these fields:

### Identity Fields

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `source` | string | `"infocasas"` | Which website the listing came from |
| `source_url` | string | `"https://..."` | Original URL of the listing |
| `external_id` | string or null | `"2905489"` | ID number from the source site |

### Core Listing Info

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `title` | string | `"Casa en Venta en Barrio Mariscal López"` | Listing title or headline |
| `property_type` | string | `"casa"`, `"departamento"`, `"terreno"`, `"local"`, `"country"`, `"oficina"`, `"cochera"` | Type of property (see full list below) |

### Price

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `price` | float or null | `830000000.0` | Price in Paraguayan Guaraníes (PYG). 94% of listings have this. |
| `price_usd` | float or null | `285000.0` | Price in US Dollars. 87% of listings have this. |
| `currency` | string | `"PYG"` or `"USD"` | Primary currency of the listing |
| `negotiable` | boolean | `false` | Whether the price is marked as negotiable |

### Location

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `city` | string | `"Asunción"`, `"Luque"`, `"Encarnación"` | City or department name. 98% of listings have this. |
| `district` | string or null | `"Las Mercedes"`, `"Central"` | Neighborhood or district within the city |
| `address` | string or null | `"Av. Mariscal López 1234"` | Street address when available |
| `zone` | string or null | `"Zona Norte"` | Zone area description |
| `coordinates` | [float, float] or null | `[-25.289, -57.609]` | GPS coordinates `[latitude, longitude]`. 73% of listings have this. |

### Property Details

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `bedrooms` | int or null | `3` | Number of bedrooms. 0 = studio or land. 60% have this. |
| `bathrooms` | int or null | `2` | Number of bathrooms. 61% have this. |
| `total_area_m2` | float or null | `744.0` | Total land area in square meters. 72% have this. |
| `built_area_m2` | float or null | `588.0` | Constructed/built area in square meters. 57% have this. |
| `floors` | int or null | `2` | Number of floors/levels |
| `parking_spots` | int or null | `2` | Number of garage/parking spaces |
| `year_built` | int or null | `2020` | Construction year |

### Content

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `description` | string | `"Amplia casa con piscina..."` | Full description text. 88% have this. HTML stripped. |
| `features` | list of strings | `["piscina", "jardín", "cochera"]` | List of amenities and features |
| `images` | list of strings | `["https://...img1.jpg", ...]` | Array of image URLs. 97% have at least one. |
| `video_url` | string or null | `"https://youtube.com/..."` | Video tour URL when available |

### Contact

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `contact_name` | string or null | `"Juan Pérez"` | Name of contact person/agent |
| `contact_phone` | string or null | `"+595981..."` | Phone number (often masked by source site) |
| `contact_email` | string or null | `"agencia@email.com"` | Email address (rarely available) |
| `agency` | string or null | `"RE/MAX Paraguay"` | Real estate agency name |

### Metadata

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `listing_date` | date or null | `"2026-04-14"` | When the listing was first posted |
| `last_updated` | date or null | `"2026-04-20"` | When the listing was last updated |
| `scraped_at` | datetime | `"2026-04-27T03:24:00"` | When we scraped this listing |
| `status` | string | `"active"` | Status: `active`, `sold`, `rented`, `removed` |

---

## Property Types

| Type in Data | English | Count | % | Median Price |
|---|---|---|---|---|
| `casa` | House | 2,947 | 26% | $180,000 |
| `terreno` | Land / Lot | 2,806 | 25% | $130,000 |
| `departamento` | Apartment | 2,550 | 23% | $105,000 |
| `local` | Commercial space | 1,591 | 14% | $180,000 |
| `otro` | Other | 964 | 9% | $150,000 |
| `country` | Country house / Farm | 107 | 1% | $730,000 |
| `oficina` | Office | 49 | <1% | $265,000 |
| `cochera` | Garage / Parking | 31 | <1% | $495,000 |
| `galpon` | Warehouse | 4 | <1% | $112,000 |
| `edificio` | Building | 1 | <1% | — |
| `estancia` | Ranch / Estate | 1 | <1% | $20,000 |
| `duplex` | Duplex | 1 | <1% | $900 |

---

## Sources

| Source | Type of Site | Listings | Data Quality |
|--------|-------------|----------|--------------|
| **InfoCasas** | Leading PY real estate portal | 8,016 | ⭐⭐⭐⭐⭐ Best — GPS, beds, baths, area, images |
| **Clasipar** | Largest PY classifieds | 1,834 | ⭐⭐⭐ Good — prices, locations, weak on beds/baths |
| **MercadoLibre** | Marketplace with real estate section | 986 | ⭐⭐⭐⭐ Clean data — beds, baths, area, prices |
| **InmueblesPY** | PY-specific real estate portal | 249 | ⭐⭐⭐ GPS coords, some missing titles |
| **PropiedadesYA** | PY real estate with AI search | 46 | ⭐⭐⭐⭐ GPS on nearly all, contact info |
| **RE/MAX** | International franchise PY site | 24 | ⭐⭐ Low volume |
| **Buscocasita** | Free classifieds portal | 9 | ⭐ Minimal data |
| **OmniMLS** | International MLS aggregator | 7 | ⭐⭐ Has area + rooms |

### URLs of scraped sources

| Source | URL |
|--------|-----|
| InfoCasas | https://www.infocasas.com.py/ |
| Clasipar | https://clasipar.paraguay.com/ |
| MercadoLibre | https://inmuebles.mercadolibre.com.py/ |
| InmueblesPY | https://inmueblespy.com/ |
| PropiedadesYA | https://propiedadesya.com.py/ |
| RE/MAX | https://www.remax.com.py/ |
| Buscocasita | https://paraguay.buscocasita.com/ |
| OmniMLS | https://omnimls.com/ |

---

## Price Distribution

### Overall USD prices (9,762 listings)

| Percentile | Price |
|------------|-------|
| 1% | $1,070 |
| 10% | $39,530 |
| 25% | $75,898 |
| **50% (Median)** | **$140,000** |
| 75% | $280,000 |
| 90% | $645,000 |
| 99% | $3,680,000 |
| Average | $317,472 |
| Maximum | $10,000,000 |

### Price by city (median USD, minimum 5 listings)

| City | Listings | Median | Range |
|------|----------|--------|-------|
| Asunción | 4,865 | $165,000 | $1K - $10M |
| Central | 3,263 | $108,000 | $130 - $9.8M |
| Cordillera | 580 | $139,000 | $750 - $9.5M |
| Alto Paraná | 204 | $162,450 | $5K - $3.4M |
| Luque | 126 | $200,000 | $9K - $1.5M |
| Fernando de la Mora | 114 | $250,000 | $25K - $2.3M |
| San Lorenzo | 89 | $235,000 | $23K - $2.1M |
| Itapúa | 67 | $86,967 | $5K - $700K |
| Lambaré | 59 | $255,000 | $32K - $1.2M |
| Ciudad del Este | 55 | $500,000 | $25K - $4M |

---

## Geographic Coverage

### Top 20 cities/departments

| City | Listings | % of Total | Cumulative % |
|------|----------|-----------|--------------|
| Asunción | 4,865 | 43.6% | 43.6% |
| Central | 3,263 | 29.2% | 72.8% |
| Cordillera | 580 | 5.2% | 78.0% |
| Alto Paraná | 204 | 1.8% | 79.8% |
| Luque | 126 | 1.1% | 80.9% |
| Fernando De La Mora | 114 | 1.0% | 82.0% |
| San Lorenzo | 89 | 0.8% | 82.8% |
| Presidente Hayes | 71 | 0.6% | 83.4% |
| Itapúa | 67 | 0.6% | 84.0% |
| Lambaré | 59 | 0.5% | 84.5% |
| Paraguarí | 59 | 0.5% | 85.0% |
| Ciudad Del Este | 55 | 0.5% | 85.5% |
| Mariano Roque Alonso | 53 | 0.5% | 86.0% |
| San Bernardino | 42 | 0.4% | 86.4% |
| Encarnación | 28 | 0.3% | 86.6% |
| Caaguazú | 28 | 0.3% | 86.9% |
| Capiatá | 26 | 0.2% | 87.1% |
| San Estanislao | 24 | 0.2% | 87.3% |
| Ñemby | 23 | 0.2% | 87.5% |
| Villa Elisa | 23 | 0.2% | 87.7% |

### Geographic summary
- **705 unique locations** across all 17 departments of Paraguay
- **Asunción + Central** = 73% of all listings
- **Top 3** (Asunción + Central + Cordillera) = **78%**
- **50+ cities** have fewer than 5 listings (underserved areas)

---

## Bedrooms

| Bedrooms | Count | % of those with data |
|----------|-------|---------------------|
| Studio / Land (0) | 411 | 6% |
| 1 | 1,360 | 20% |
| 2 | 1,626 | 24% |
| **3 (most common)** | **1,935** | **28%** |
| 4 | 771 | 11% |
| 5 | 567 | 8% |
| 6+ | 70 | 1% |

Average bathrooms: **2.1** per listing (median: 2)

---

## Area (square meters)

| Metric | Land Area | Built Area |
|--------|-----------|------------|
| Listings with data | 8,008 (72%) | 6,370 (57%) |
| Median | 262 m² | 154 m² |
| Average | 1,468 m² | 321 m² |
| Maximum | 97,640 m² | 9,888 m² |

---

## Data Quality Notes

### Prices
- **PYG prices**: stored without thousands separator dots. "1.760.000.000" → `1760000000.0`
- **USD prices**: some listings have PYG mistakenly tagged as USD. Values >$10M were set to null.
- **1% of listings** have unrealistically low prices (<$1K) — data entry errors, kept as-is.

### Bedrooms
- Clasipar parsing has ~15% error rate due to SEO spam in HTML.
- Bedroom counts >20 were set to null.
- 0 bedrooms = studio apartments or land listings.

### Locations
- InfoCasas uses department names in the city field (e.g. "Central" is a department, not a city).
- Clasipar has the widest geographic coverage (57+ cities).
- Coordinates are formatted as `[latitude, longitude]` — suitable for mapping.

### Missing data
- Contact info is largely unavailable (sites hide behind login/recaptcha).
- Clasipar has weak bedroom/bathroom data (only 8-9% coverage).

---

## How This Data Was Collected

| Detail | Value |
|--------|-------|
| Scrape date | April 27, 2026 |
| Scraping tools | httpx + parsel (5 sources), Playwright (3 sources) |
| Rate limiting | 1-3 seconds between requests |
| Cleaning | HTML stripped, prices sanity-checked, bedrooms capped |
| Deduplication | By URL across all sources |
| Merge strategy | Highest-quality source preferred |

---

## Sample Listing (JSON)

```json
{
  "source": "infocasas",
  "title": "Vendo Terreno Zona Shopping Pinedo",
  "property_type": "terreno",
  "price": 110000.0,
  "price_usd": 110000.0,
  "currency": "PYG",
  "city": "Central",
  "district": "Fernando de la Mora",
  "total_area_m2": 492.0,
  "description": "Terreno zona Shopping Pinedo...",
  "coordinates": [-25.3289, -57.5133],
  "images": ["https://cdn4.fincaraiz.com.co/..."],
  "bedrooms": 1,
  "bathrooms": 1,
  "listing_date": "2026-03-23",
  "agency": "AA Inmobiliaria",
  "source_url": "https://www.infocasas.com.py/vendo-terreno-zona-shopping-pinedo/190379072"
}
```

---

*For the full market analysis, see `research/complete-analysis.md`.*
*Raw data: `data/_merged/listings.jsonl` (24 MB, 11,171 lines).*

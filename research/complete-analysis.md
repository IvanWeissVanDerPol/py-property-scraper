# Paraguay Property Market — Complete Data Analysis
**Dataset: 11,171 unique listings across 8 online sources**
**Generated: April 27, 2026**

## 1. Dataset Composition

**Total listings analyzed: 11,171**

| Source | Listings | % | Method |
|--------|---------|---|--------|
| infocasas | 8,016 | 71.8% | Direct HTTP + Next.js JSON |
| clasipar | 1,834 | 16.4% | Direct HTTP + regex |
| mercadolibre | 986 | 8.8% | Playwright headless browser |
| inmueblespy | 249 | 2.2% | Direct HTTP + JSON-LD |
| propiedadesya | 46 | 0.4% | WordPress REST API + HTML |
| remax | 24 | 0.2% | Playwright headless browser |
| buscocasita | 9 | 0.1% | Direct HTTP + HTML |
| omnimls | 7 | 0.1% | Playwright headless browser |
| **TOTAL** | **11,171** | **100%** | |

## 2. Property Type Analysis

| Type | Count | % | Median USD |
|------|-------|---|------------|
| casa | 2,947 | 26.4% | $180,000 |
| terreno | 2,806 | 25.1% | $130,000 |
| departamento | 2,550 | 22.8% | $105,000 |
| local | 1,591 | 14.2% | $180,000 |
| otro | 964 | 8.6% | $150,000 |
|  | 113 | 1.0% | N/A |
| country | 107 | 1.0% | $730,000 |
| oficina | 49 | 0.4% | $265,000 |
| cochera | 31 | 0.3% | $495,000 |
| otros | 5 | 0.0% | $450,000 |
| galpon | 4 | 0.0% | $112,000 |
| estancia | 1 | 0.0% | $20,000 |
| edificio | 1 | 0.0% | N/A |
| duplex | 1 | 0.0% | $900 |
| local comercial | 1 | 0.0% | $400,000 |

## 3. Price Analysis

**USD Prices (9,762 listings):**
- 1th percentile: $1,070
- 10th percentile: $39,530
- 25th percentile: $75,898
- 50th percentile: $140,000
- 75th percentile: $280,000
- 90th percentile: $645,000
- 99th percentile: $3,680,000
- Average: $317,472
- Maximum: $10,000,000

**Median USD price by property type:**
| Type | Median | Count |
|------|--------|-------|
| casa | $180,000 | 2,602 |
| departamento | $105,000 | 2,480 |
| terreno | $130,000 | 2,474 |
| local | $180,000 | 1,210 |
| country | $730,000 | 87 |

## 4. Geographic Analysis

**Total unique locations: 705**

| City / Department | Listings | % | Cumulative | Median USD |
|------------------|---------|---|------------|------------|
| Asunción | 4,865 | 43.6% | 43.6% | $165,000 |
| Central | 3,263 | 29.2% | 72.8% | $108,000 |
| Cordillera | 580 | 5.2% | 78.0% | $139,000 |
| Alto Paraná | 204 | 1.8% | 79.8% | $162,450 |
| Luque | 126 | 1.1% | 80.9% | $200,000 |
| Fernando De La Mora | 114 | 1.0% | 81.9% | $250,000 |
| San Lorenzo | 89 | 0.8% | 82.7% | $235,000 |
| Presidente Hayes | 71 | 0.6% | 83.4% | $240,292 |
| Itapúa | 67 | 0.6% | 84.0% | $86,967 |
| Lambaré | 59 | 0.5% | 84.5% | $255,000 |
| Paraguarí | 59 | 0.5% | 85.0% | $126,497 |
| Ciudad Del Este | 55 | 0.5% | 85.5% | $500,000 |
| Mariano Roque Alonso | 53 | 0.5% | 86.0% | $230,000 |
| San Bernardino | 42 | 0.4% | 86.4% | $300,000 |
| Encarnación | 28 | 0.3% | 86.6% | $270,000 |
| Caaguazú | 28 | 0.3% | 86.9% | $229,276 |
| Capiatá | 26 | 0.2% | 87.1% | $440,000 |
| San Estanislao | 24 | 0.2% | 87.3% | $200,000 |
| Ñemby | 23 | 0.2% | 87.5% | $440,000 |
| Villa Elisa | 23 | 0.2% | 87.7% | $370,000 |
| **TOTAL** | **11,171** | **100%** | **100%** | |

## 5. Bedroom & Bathroom Analysis

**6,740** listings have bedroom data (61% of dataset)

| Bedrooms | Count | % |
|----------|-------|---|
| 0 | 411 | 6% |
| 1 | 1,360 | 20% |
| 10 | 2 | 0% |
| 10+ | 13 | 0% |
| 2 | 1,626 | 24% |
| 3 | 1,935 | 28% |
| 4 | 771 | 11% |
| 5 | 567 | 8% |
| 6 | 33 | 0% |
| 7 | 10 | 0% |
| 8 | 10 | 0% |
| 9 | 2 | 0% |

**Bathrooms:** 6,926 listings with data, avg 2.1, median 2

## 6. Area Analysis

**Land area (m²)** — 8,008 listings: Median 262, Avg 1,468, Max 97,640
**Built area (m²)** — 6,370 listings: Median 154, Avg 321, Max 9,888

## 7. Data Completeness by Source

| Source | Total | Title% | Price% | USD% | Beds% | GPS% | Img% |
|--------|-------|--------|--------|------|-------|------|------|
| infocasas | 8,016 | 100% | 99% | 99% | 74% | 100% | 99% |
| clasipar | 1,834 | 100% | 79% | 74% | 8% | 0% | 94% |
| mercadolibre | 986 | 100% | 94% | 39% | 53% | 0% | 100% |
| inmueblespy | 249 | 54% | 47% | 1% | 26% | 53% | 54% |
| propiedadesya | 46 | 100% | 26% | 43% | 63% | 97% | 100% |
| remax | 24 | 79% | 91% | 41% | 0% | 0% | 0% |
| buscocasita | 9 | 100% | 66% | 33% | 33% | 0% | 100% |
| omnimls | 7 | 100% | 57% | 28% | 85% | 0% | 0% |

## 8. Key Market Insights


### Market Size
- **11,171 unique property listings** collected across 8 Paraguayan online sources
- **InfoCasas** represents 72% of the dataset (8,016 listings)
- **InfoCasas + Clasipar** = 88% of all searchable inventory
- Estimated total online PY real estate market: **12,000-15,000 listings**

### Geographic Concentration
- **Asunción** dominates with **43%** of all listings (4,865)
- **Central department** adds **29%** (3,263)
- Top 3 areas (Asunción + Central + Cordillera) = **78% of all listings**
- **705 unique locations** identified across all 17 departments

### Price Landscape
- **Overall median: $140,000 USD**
- Houses: **$180,000** median — most expensive built category
- Land: **$130,000** median — wide range
- Apartments: **$105,000** median — most affordable built property
- **87% of listings** include USD price, **94%** include PYG price

### Property Types
- Houses (26%), land (25%), apartments (23%) are nearly evenly split
- Together they represent **74% of the market**
- Most common: **3-bedroom** (28% of those with data)

### Data Quality
- **97%** have images, **88%** have descriptions
- **73%** have GPS coordinates (concentrated in InfoCasas)
- **Cross-source duplicate rate**: very low (<2%)
- **7,134 data quality issues** fixed by cleaning pipeline

### Sources Not Covered
- **Century 21 PY**: Empty site — no listing directory
- **Zonaprop PY**: Cloudflare protected
- **Agentiz PY**: JS-rendered ad-posting form, ~25 PY listings
- **Facebook Marketplace**: Technically difficult, against ToS
- All remaining sources: estimated <1,000 additional listings combined

## 9. Methodology & Limitations


### Scraping Approach
- **5 scrapers** use direct HTTP (httpx + parsel) — fastest, most reliable
- **3 scrapers** use Playwright headless browser — for JS-rendered sites
- All scrapers respect rate limits (1-3s between requests)
- Data collected on **April 27, 2026** — a single snapshot

### Data Processing
- HTML tags stripped from all text fields (SEO spam removed)
- Prices sanity-checked: >$10M USD set to null (PYG/USD confusion)
- Bedrooms >20 set to null (parsing errors from Clasipar)
- All listings deduplicated by URL across sources

### Limitations
- **Snapshot only** — no historical price trends
- Some listings may be **sold or expired**
- Contact info **mostly hidden** behind login forms
- Clasipar bedroom/bathroom data has ~15% error rate
- PYG prices use "." as thousands separator

---
*End of report — 11,171 listings analyzed. File: `data/_merged/listings.jsonl`*

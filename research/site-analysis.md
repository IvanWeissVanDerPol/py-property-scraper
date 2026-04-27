# Site-by-Site Analysis — Paraguayan Property Sources

This document is based on **live scraping** of each source conducted on April 27, 2026.
Each site was fetched via Firecrawl (headless browser), with raw HTML analysis for structure.

---

## 1. Clasipar — clasipar.paraguay.com/venta/casas

**Status**: ✅ Scraped. Great data. Easy.

### Search Page Data (per listing card)
| Field | Example | Availability |
|---|---|---|
| Title | `AMPLIA Y FUNCIONAL RESIDENCIA EN VENTA` | ✅ Always |
| Price (USD) | `US$. 285.000,00` | ✅ Always (USD or PYG) |
| Price (PYG) | `Gs. 239.000.000` | ✅ Often |
| Location/city | `Casas en Asunción`, `Casas en Capiatá` | ✅ Always in link |
| Type of seller | `Particular` or `Inmobiliaria` | ✅ Always |
| Photo URL | `clasicdn.paraguay.com/...S.jpg` | ✅ Always |
| Listing URL | `/inmuebles/casas/...-2905489` | ✅ Always |

### Detail Page Data (per individual listing)
| Data Point | How It Appears | Extractable |
|---|---|---|
| Price | `Gs. 239.000.000` | ✅ |
| Bedrooms | `Dormitorios: **2**` | ✅ |
| Department | `Departamento: Central` | ✅ |
| City | `Ciudad: Capiatá` | ✅ |
| Zone/neighborhood | `Zona: Posta Yvyraro` | ✅ |
| Listing ID | `Nro. de Anuncio: 2905489` | ✅ |
| Views | `Nro. de Visitas: 45` | ✅ |
| Publish date | `Publicado el: 14/04/2026` | ✅ |
| Description | Long text in `<div>` | ✅ |
| Images | `clasicdn.paraguay.com/...L.webp` | ✅ (multiple) |
| Seller info | Company name, phone (masked), email (masked) | Partial |
| Contact reveal | Requires login with reCAPTCHA | ❌ |

### Crawl URL Pattern
```
/search page: /venta/casas?pagina=N
/detail page: /inmuebles/casas/{slug}-{listing_id}
```

### Structure
- **Search page**: Standard HTML. Each listing is a `<div>` with:
  - `h2 > a` = title + link  
  - Price text (unmarked, adjacent to title)  
  - Icon/text badges for bedrooms (e.g. the word appears in title/description)
- **Detail page**: Clean key-value pairs visible:
  - Fields are in definition list or `<span>` elements  
  - `Dormitorios: 2` pattern  
  - `Gs. 239.000.000` price  

### Strategy
```
1. GET /venta/casas → extract listing URLs + price/title from search cards
   SELECTOR: a[href*="/inmuebles/casas/"] 
   PAGINATION: a.pagination-next, a.next, li.next a
2. GET /inmuebles/casas/{slug}-{id} → extract detail fields
   FIELDS: price via regex, bedrooms via "Dormitorios:", location via "Ciudad:", 
   area via "m²", date via "Publicado el:", images via img[src*="clasicdn"]
3. Parse price from text: "Gs. 239.000.000" or "US$. 285.000,00"
   Note: Format uses "." for thousands and "," for decimals
```

**Rate limit**: 1.5s delay between requests. 8,098 results in "Casas" alone.
**Anti-scraping**: Minimal. reCAPTCHA only on contact reveal (not needed).
**Estimated total**: ~15,000+ listings across all categories.

---

## 2. InfoCasas — www.infocasas.com.py/venta

**Status**: ✅ Scraped. Excellent structured data. Some JS rendering.

### Search Page Data
| Field | Example | Availability |
|---|---|---|
| Title | `Vendo terreno zona shopping pinedo` | ✅ |
| Price | `U$S 110.000` | ✅ |
| Location | `Fernando de la Mora, Central` | ✅ In breadcrumb |
| Bedrooms | `1 Dorm` | ✅ Badge |
| Bathrooms | `1 Baño` | ✅ Badge |
| Area | `50m²` | ✅ Badge |
| Badge | `Destacado` | ✅ Premium tag |
| Agency name | `AA Inmobiliaria`, `Steromar S.A.` | ✅ |
| Agency logo | Image URL | ✅ |
| Images | Gallery thumbnails | ✅ |

### Detail Page Data
| Data Point | How It Appears | Extractable |
|---|---|---|
| Price | `U$S 71.920` | ✅ |
| Property type | `Departamento` | ✅ |
| Status | `A estrenar` | ✅ (new/used) |
| Bedrooms | `1` | ✅  |
| Bathrooms | `1` | ✅ |
| Built area | `50 m2` | ✅ |
| Terrace area | `12 m2` | ✅ |
| Reference | `VU5B65A` | ✅ |
| Zone | `Mariano Roque Alonso` | ✅ |
| Total floors | `1` | ✅ |
| Description | Long structured text | ✅ |
| Amenities | Bullet list in description | ✅ (embedded in text) |
| Map | OpenStreetMap tiles | ✅ (coords embedded) |
| Financing | AFD calculator | ✅ |
| Price per m² | `U$S 1.438 /m²` | ✅ Computed |
| Market comparison | vs similar properties | ✅ |
| Agency contact | Name, phone, address | ✅ |
| Listing date | `23 de marzo de 2026` | ✅ In footer meta |

### Crawl URL Pattern
```
/search page: /venta or /venta/{property-type}/{city}
/detail page: /{slug}/{numeric_id}
```

### Structure
- **Search page**: Uses image cards. Each listing has:
  - `a[href*="infocasas.com.py/"]` → detail link
  - Image with fallback  
  - Structured badges: `**1 Dorm**`, `**1 Baño**`, `**50m²**`
  - Price: `U$S 71.920`
  - Agency info block
- **Detail page**: Extremely structured — "Detalles de la Propiedad" section with key-value pairs
  - All fields in labeled `<li>` or definition list
  - OpenStreetMap embed with lat/lon
  - Full description in "Descripción" section

### Strategy
```
1. GET /venta → extract detail URLs + preview data  
   SELECTOR: a[href*="/venta/"][href*="/"]
   BADGES: "Dorm", "Baño", "m²" text in card
2. GET /{slug}/{id} → extract structured data  
   PARSE "Detalles de la Propiedad" list section  
   Fields: property_type, status, bedrooms, bathrooms, built_area, terrace_area,
   reference, zone, total_floors, orientation, financing  
3. Price: "U$S 71.920" format  
4. Extract lat/lon from OpenStreetMap tile URLs (<img src=".../16/22298/37509.png">)
   → "16/ZOOM/X/Y" → reverse geocode OR use OSM API
```

**Rate limit**: 2s delay. "Más de 400" listings shown (likely ~1000+).
**Anti-scraping**: May require JS for some parts. Listing detail is static HTML.
**Note**: Runs on FincaRaiz platform (used in UY, CO, BO, PE, PY) — shared infrastructure.

---

## 3. MercadoLibre Inmuebles — inmuebles.mercadolibre.com.py

**Status**: ⚠️ Scraped. JavaScript-heavy. Anti-scraping active. 4.3MB HTML loaded.

### Findings
- 4.3MB of HTML on the search page
- Listing cards ARE in HTML (51 result cards found)
- **BUT**: Prices are NOT in static HTML — they render via JS
- Cookie consent wall blocks initial page
- `__PRELOADED_STATE__` is present in script tags with listing data
- JSON-LD structured data has item list

### Strategy
```
1. Accept cookies first (POST or cookie header)
2. Extract listing data from __PRELOADED_STATE__ JS variable
   → This contains all listing data including prices, attributes, locations
3. Parse the React-rendered state instead of the DOM
```

### Alternative: MercadoLibre API
```
API: https://api.mercadolibre.com/sites/MPY/search?q=casa+venta&limit=50
BUT: This returns 403 Forbidden now (was open before)
Workaround: Use the ML API with a token/access_token from a logged-in session
```

### Data Available (from page state)
- Title, price, currency, condition
- Attributes: bedrooms, bathrooms, total_area, covered_area
- Location: neighborhood, city, state
- Images, listing URL, seller info

**Rate limit**: 3s delay. Heavy anti-scraping.
**Recommendation**: Use Playwright or similar headless browser with cookie persistence.

---

## 4. InmueblesPY — inmueblespy.com

**Status**: ✅ Scraped. WordPress site. Clean structured data. 54KB page.

### Search Page Data
| Field | Available | Notes |
|---|---|---|
| City filter | ✅ | Dropdown with 35+ cities (Asunción, CDE, Encarnación, etc.) |
| Property type | ✅ | Apartamento, Casa Adosada, Casa de Campo, etc. |
| Bedrooms filter | ✅ | 1-10 |
| Bathrooms filter | ✅ | 1-10 |
| Area filters | ✅ | Min area built, min area land |
| Price filter | ✅ | Range selector |

### Detail Page Data
- Full WordPress post with property fields
- Images in gallery
- Contact form for the agent

### Strategy
```
1. POST to /venta/ with filter params OR use WordPress REST API  
   → Check if /wp-json/wp/v2/posts has property data  
   → Or use the /wp-json/ real-estate plugin endpoints
2. Parse search results pages
3. Scrape individual post pages for full details
```

**Rate limit**: 2s delay. WordPress site, typically no anti-scraping.
**Note**: Uses `wp-content` images — CDN cache available.

---

## 5. PropiedadesYA — propiedadesya.com.py

**Status**: ✅ Scraped. WordPress-based. 34KB. AI search feature.

### Unique Features
- Built-in AI assistant ("Propi") for natural language search
- "Puertas Abiertas" (open house) concept
- WordPress-based → likely same structure as InmueblesPY

### Strategy
```
1. Same WordPress approach as InmueblesPY
2. Check for REST API endpoints  
3. Property listings page: /propiedades/
```

---

## 6. Buscocasita PY — paraguay.buscocasita.com

**Status**: ✅ Scraped. Simple HTML. 15KB. Multi-country platform.

### Data Available (per listing card)
| Field | Example |
|---|---|
| Image | `buscocasita.com/img500/595/2026/04/1316343.jpg` |
| Title | `6 ha con casa y restaurante equipado — Guairá` |
| Price (PYG) | `Gs. 1.760.000.000,00 guaraníes` |
| Price (USD) | `USD 150.000,00 dólares` |
| Description (excerpt) | In the card text |
| Detail link | `/6-ha-con-casa-y-restaurante-equipado-guaira_395727.html` |

### Strategy
```
1. Parse search page: simple HTML listing cards
2. Detail page: /{slug}_{id}.html
3. Note: Some scam listings visible ("donación de mi fortuna") → filter needed
```

**Note**: Same platform powers multiple countries (uses country ID `595` for PY).

---

## 7. RE/MAX Paraguay — remax.com.py

**Status**: ✅ Scraped. More JS-heavy. 10KB initial content. React/Angular SPA.

### Data Visible
- Listing cards with images
- Property type labels: Casa, Departamento, Terreno, Casa de Campo, Edificio, Depósito
- Badges: "Exclusivo en REMAX", "Nueva en el Mercado", "Excelente Oportunidad"

### Strategy
```
1. Requires headless browser (Playwright) to render listing data
2. URL pattern: /es-py/propiedades/{type}/{action}/{zone}/{address}/{id}
3. Likely has an API backend — inspect network calls  
```

---

## 8. Century 21 Paraguay — century21.com.py

**Status**: ❌ Not yet deeply inspected. Franchise site.

### Strategy
```
1. Check if it uses IDX/MLS syndication feed (common for Century 21)
2. If so, may have an XML or JSON feed
3. Search page likely JS-rendered
```

---

## 9. Agentiz PY — py.agentiz.com

**Status**: ✅ Scraped. Well-structured. 46KB. Multi-country aggregator.

### Data Available
| Field | Example |
|---|---|
| Title | `Finca con casa y restaurante en Villarrica, Guairá` |
| Price | `Gs. 1.760.000.000` |
| Bedrooms | `2 br` |
| Area | `60.000 m²` |
| Location | `Villarrica, Guairá` |
| Description | Full text ✅ |
| Image | Thumbnail ✅ |
| Detail URL | `/es/for-sale-housing-residential-property/id-pyc4` |

### Strategy
```
1. Simple HTML with structured cards
2. URL pattern: /es/{action}-{type}/id-{code}
3. Listings come from API/integration feed
4. Filter by country: py.agentiz.com for PY-only
```

---

## Data Quality Comparison

| Source | Total Listings | Price Data | Bed/Bath | Area | Location | Description | Images | Anti-Scrape |
|---|---|---|---|---|---|---|---|---|
| **Clasipar** | ~8,100+ (houses only) | ✅ PYG & USD | ✅ In title/text | ✅ In desc | ✅ City/Dept | ✅ Long text | ✅ | Low |
| **InfoCasas** | ~400+ (all types) | ✅ USD | ✅ Badge | ✅ Badge | ✅ City/Zone | ✅ Very detailed | ✅ Gallery | Medium |
| **MercadoLibre** | Many | ❌ JS-locked | ✅ Attribute | ✅ Attribute | ✅ | ✅ | ✅ | High |
| **InmueblesPY** | Unknown | ✅ | Filterable | Filterable | ✅ 35+ cities | ✅ | ✅ | None |
| **PropiedadesYA** | Unknown | ✅ | Filterable | Filterable | ✅ | ✅ | ✅ | None |
| **Buscocasita** | Small | ✅ PYG & USD | ❌ Not in card | ✅ In title | ✅ | ✅ Short | ✅ | None |
| **RE/MAX** | Medium | ❌ JS-locked | ❌ JS-locked | ❌ JS-locked | ✅ | ❌ JS-locked | ✅ | Medium |
| **Agentiz** | Small | ✅ PYG | ✅ Badge | ✅ Badge | ✅ | ✅ | ✅ | None |

---

## Recommended Data Gathering Strategy

### Phase 1 — Easy Wins (implement now)
1. **Clasipar** — scraper ALREADY written. Just needs CSS selector tweaks after live testing.
2. **InfoCasas** — most structured data. STRONGLY recommended for Phase 1.
3. **InmueblesPY** — WordPress, easy.

### Phase 2 — Medium Effort
4. **PropiedadesYA** — same WordPress approach.
5. **Buscocasita** — simple HTML, low volume.
6. **Agentiz** — well-structured, low volume.

### Phase 3 — JS Rendering Required
7. **MercadoLibre** — needs Playwright for JS rendering and cookie handling.
8. **RE/MAX** — needs Playwright.
9. **Century 21** — needs investigation.

### Optimal Architecture

```
                    ┌─────────────────────┐
                    │   Orchestrator       │
                    │   (schedule/timer)   │
                    └──────┬──────┬───────┘
                           │      │
              ┌────────────┘      └────────────┐
              ▼                                 ▼
    ┌──────────────────┐            ┌──────────────────┐
    │  Static Scrapers  │            │  JS Scrapers      │
    │  (httpx+parsel)   │            │  (Playwright)     │
    ├──────────────────┤            ├──────────────────┤
    │ • Clasipar       │            │ • MercadoLibre    │
    │ • InfoCasas      │            │ • RE/MAX          │
    │ • InmueblesPY    │            │ • Century 21      │
    │ • Buscocasita    │            └──────────────────┘
    │ • Agentiz        │
    └──────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │   Data Normalizer   │
    │   (unified schema)  │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   Dedup + Merge     │
    │   (by URL, ID,      │
    │    fuzzy title)     │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   Output            │
    │   JSONL → DuckDB    │
    │   → Analysis        │
    └─────────────────────┘
```

### Key Technical Decisions

1. **Start with Clasipar + InfoCasas in parallel** — they give 90% of the value with 20% of the effort
2. **Skip contact scraping** — most sites hide phone/email behind login or reCAPTCHA
3. **Deduplicate by URL** — listings can appear on multiple platforms
4. **Store raw JSONL** — append-only, easy to re-process if schema changes
5. **Currency normalization** — store both PYG and USD when available
6. **Schedule weekly** — property listings change frequently

# Paraguayan Property Sources — Deep Research

## Methodology

Searches performed via Firecrawl + DuckDuckGo with queries in both English and Spanish, targeting:
- `Paraguay property listing sites compra venta casas departamentos terrenos`
- `portales inmobiliarios Paraguay clasificados propiedades`
- `sitios web venta propiedades Paraguay inmobiliarias clasificados online`
- `clasificados Paraguay casas venta propiedades`

## Complete Source Inventory

### Tier 1 - Major Paraguayan Portals (HIGH priority)

These are the primary sources — large inventory, Paraguayan-specific, likely structurable for scraping.

#### 1. InfoCasas — https://www.infocasas.com.py/
- **Description**: The leading real estate portal in Paraguay. Massive inventory of houses, apartments, land, commercial properties across all of Paraguay.
- **Inventory**: Thousands of listings
- **Structure**: Likely has listing pages with standardized fields (price, area, bedrooms, location)
- **Tech**: May use JavaScript rendering (SPA-like)
- **Scraping approach**: Try direct HTTP first → if JS-heavy, use Playwright
- **URL patterns**: 
  - Search: `https://www.infocasas.com.py/venta` or `https://www.infocasas.com.py/venta/casas`
  - Detail: `https://www.infocasas.com.py/{category}/{id}`

#### 2. Clasipar — https://clasipar.paraguay.com/venta/casas
- **Description**: Paraguay's largest classifieds platform (similar to OLX/MercadoLibre Classifieds). Massive inventory for ALL categories including real estate.
- **Inventory**: Very large
- **Structure**: Traditional HTML classifieds format
- **Scraping approach**: Direct HTTP. Simple HTML structure, paginated.
- **URL patterns**:
  - Category: `https://clasipar.paraguay.com/venta/casas`
  - Pagination: `?pagina=2` or similar
  - Detail: `https://clasipar.paraguay.com/{id}-{slug}.html`

#### 3. MercadoLibre Inmuebles — https://inmuebles.mercadolibre.com.py/
- **Description**: MercadoLibre's real estate section for Paraguay. Standardized listing format across all ML markets.
- **Inventory**: Large
- **Structure**: Well-structured, JSON embeds in HTML. API available via `https://api.mercadolibre.com/`
- **Scraping approach**: JSON data embedded in page or direct API calls
- **Notes**: MercadoLibre has anti-scraping measures but their listing data is consistently structured

#### 4. InmueblesPY — https://inmueblespy.com/
- **Description**: Dedicated Paraguayan real estate portal
- **Inventory**: Medium
- **Structure**: Unknown — needs exploration
- **Scraping approach**: Start with direct HTTP, inspect DOM structure

#### 5. PropiedadesYA — https://propiedadesya.com.py/
- **Description**: Paraguayan real estate portal ("PropiedadesYA")
- **Inventory**: Medium
- **Structure**: Unknown — needs exploration

#### 6. Buscocasita Paraguay — https://paraguay.buscocasita.com/
- **Description**: Free real estate listing portal in Paraguay
- **Inventory**: Small-Medium
- **Structure**: Unknown — needs exploration

#### 7. Agentiz Paraguay — https://py.agentiz.com/
- **Description**: Free real estate classifieds for Paraguay
- **Inventory**: Small-Medium
- **Structure**: Likely simple HTML classifieds

### Tier 2 - International Franchises (MEDIUM priority)

Franchise sites with Paraguay-specific sections. Inconsistent inventory but includes premium properties.

#### 8. Century 21 Paraguay — https://century21.com.py/
- **Description**: Century 21 franchise in Paraguay
- **Inventory**: Medium, premium-leaning
- **Structure**: Professional site, may use IDX/MLS feed
- **Scraping approach**: Inspect for REST API behind the site

#### 9. RE/MAX Paraguay — https://www.remax.com.py/listings
- **Description**: RE/MAX franchise in Paraguay
- **Inventory**: Medium
- **Structure**: Professional, likely MLS-powered
- **Scraping approach**: Similar to Century 21

#### 10. Coldwell Banker Paraguay — https://coldwellbanker.com.py/propiedades/todas/venta/Paraguay
- **Description**: Coldwell Banker franchise
- **Inventory**: Small-Medium, premium
- **Structure**: Professional site

#### 11. Paraguay Real Estate — https://paraguayrealestate.com.py/
- **Description**: Local agency with online presence
- **Inventory**: Small
- **Structure**: Basic agency website

### Tier 3 - International Aggregators (LOW priority)

These aggregate PY listings but data may be stale or less detailed.

#### 12. Realtor.com International — https://www.realtor.com/international/py/
- **Description**: Realtor.com's international section for Paraguay
- **Inventory**: Medium
- **Structure**: Professional
- **Notes**: May have fewer listings than local sites

#### 13. Zonaprop — https://www.zonaprop.com.ar/inmuebles-paraguay.html
- **Description**: Argentine portal (Zonaprop) listing Paraguayan properties
- **Inventory**: ~300 properties
- **Structure**: Well-structured (Navent group)
- **Notes**: Limited PY inventory but well-formatted

#### 14. LatinCarib — https://latincarib.com/country/paraguay/
- **Description**: Caribbean/LATAM real estate aggregator
- **Inventory**: Small
- **Structure**: Unknown

#### 15. OmniMLS — https://omnimls.com/v/results/type_house/listing-type_sale/in-country_paraguay
- **Description**: International MLS aggregator
- **Inventory**: ~730 houses for Paraguay
- **Structure**: MLS-standard format

### Tier 4 - Social / Unstructured (DIFFICULT)

These are hard to scrape but contain real, active listings.

#### 16. Facebook Groups
- **Group 1**: "Terrenos Lotes Casas Propiedades en Paraguay (COMPRA VENTA)" 
  - https://www.facebook.com/groups/terrenosenparaguay/
- **Group 2**: "Clasificados Alquileres y Ventas de inmuebles PY"
  - https://www.facebook.com/groups/904935509638231/
- **Notes**: Very active, organic listings. Requires Facebook scraping (difficult/against ToS). Could monitor manually.

#### 17. Individual Agencies (LOW priority)
- CR Inmobiliaria: https://www.crinmobiliaria.com.py/
- Latinpar / ClasInmuebles: https://latinpar.com.py/

## Scraping Difficulty Matrix

| Source | Difficulty | Anti-Scrape | JS Req'd | Data Quality | Priority |
|---|---|---|---|---|---|
| InfoCasas | Medium | Maybe | Maybe | High | 🔴 HIGH |
| Clasipar | Easy | Low | No | High | 🔴 HIGH |
| MercadoLibre | Medium | High | No | High | 🔴 HIGH |
| InmueblesPY | Unknown | Unknown | Unknown | Medium | 🟡 MEDIUM |
| PropiedadesYA | Unknown | Unknown | Unknown | Medium | 🟡 MEDIUM |
| Century 21 | Medium | Low | Maybe | Medium | 🟡 MEDIUM |
| RE/MAX | Medium | Low | Maybe | Medium | 🟡 MEDIUM |
| Realtor.com | Hard | High | Yes | Medium | ⚪ LOW |

## Technical Considerations

### Paraguayan Context

- **Currency**: Prices in PYG (Guaraníes) or USD. Scrapers must handle both.
- **Language**: Spanish (Paraguayan variant with voseo). Mix of Spanish/English in some listings.
- **Format**: Area in m², price per m² sometimes listed separately.
- **Phone numbers**: +595 prefix (Paraguay country code).

### Anti-Scraping Mitigations

- Rate limiting: 1-3 second delays between requests
- Rotating user agents
- Respect robots.txt
- Cache already-seen URLs
- Use rotating proxies if blocked (residential proxies for aggressive sites like ML)

### Data Storage

- **Format**: JSONL (one JSON object per line, append-only)
- **Deduplication**: By URL + scraped_at freshness
- **Schema**: Use Pydantic models for validation
- **Storage options**: Local JSONL → DuckDB for analysis

## Next Steps

1. Start with Clasipar (easiest, highest volume)
2. Add InfoCasas (need to determine JS requirements)
3. Add MercadoLibre (structured data, anti-scrape tactics)
4. Add remaining Tier 2 sources
5. Deduplicate and merge into unified dataset
6. Analysis: price trends, inventory by location, etc.

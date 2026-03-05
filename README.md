# SEO Auditor

A fast, comprehensive SEO auditing tool that analyzes websites across 11 categories and delivers actionable insights through an interactive dashboard.

## Features

- **11 SEO Categories** — Meta tags, headings, images, links, performance, mobile, structured data, sitemap, robots.txt, tracking & pixels, semantic structure
- **Parallel Execution** — All analyzers run concurrently via ThreadPoolExecutor (~1s vs ~15s sequential)
- **Tracking Detection** — Google Analytics (GA4/UA), GTM, Search Console, Facebook Pixel, LinkedIn Insight, TikTok Pixel, Pinterest Tag, Bing UET, Hotjar, Microsoft Clarity
- **Semantic Analysis** — HTML5 elements, ARIA landmark roles, content-to-HTML ratio, figure/figcaption, time elements
- **Deep Sitemap Parsing** — Sitemap index support, lastmod freshness checks, changefreq/priority detection, cross-domain validation
- **Interactive Dashboard** — Animated score gauge, expandable category cards with color-coded severity indicators

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Install & Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser, enter a URL, and run the audit.

## Category Weights

| Category | Weight |
|----------|--------|
| Meta Tags | 15% |
| Performance | 13% |
| Tracking & Pixels | 10% |
| Images | 10% |
| Links | 10% |
| Headings | 8% |
| Mobile | 8% |
| Semantic Structure | 8% |
| Structured Data | 6% |
| Sitemap | 6% |
| Robots.txt | 6% |

## Project Structure

```
├── main.py                  # FastAPI app with parallel audit endpoint
├── requirements.txt
├── app/
│   ├── config.py            # Timeouts, weights, constants
│   ├── models.py            # Pydantic request/response models
│   ├── fetcher.py           # HTTP page fetcher + parser
│   ├── scoring.py           # Weighted score calculator
│   └── analyzers/
│       ├── meta_tags.py     # Title, description, OG, Twitter cards
│       ├── headings.py      # H1 presence, hierarchy
│       ├── images.py        # Alt text, dimensions, lazy loading
│       ├── links.py         # Internal/external ratio, invalid hrefs
│       ├── performance.py   # Response time, page size, HTTPS
│       ├── mobile.py        # Viewport, fixed widths, media queries
│       ├── structured_data.py # JSON-LD, microdata, RDFa
│       ├── sitemap.py       # Deep sitemap parsing + freshness
│       ├── robots.py        # robots.txt rules + blocking checks
│       ├── tracking.py      # Analytics tags + marketing pixels
│       └── semantic.py      # HTML5 semantics + ARIA roles
└── static/
    ├── index.html           # Dashboard UI
    ├── css/styles.css
    └── js/app.js
```

## API

### `POST /api/audit`

```json
{
  "url": "https://example.com"
}
```

Returns overall score (0–100) and per-category breakdowns with issues.

## External Intelligence Modules

The platform optionally integrates with Similarweb and SEMrush APIs to provide market and competitive intelligence alongside the core SEO audit. These modules are **opt-in** and degrade gracefully when API keys are not configured.

### Environment Variables

```bash
export SIMILARWEB_API_KEY="your-similarweb-api-key"
export SEMRUSH_API_KEY="your-semrush-api-key"
```

Both are optional. When absent, the corresponding module returns `status: "not_configured"` and the audit works normally.

### Usage

Include `include_external: true` in your audit request to activate external intelligence:

```bash
# Full audit + external intelligence
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "include_external": true}'

# Only Similarweb
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "include_external": true, "external_modules": ["similarweb"]}'
```

### Sample Response (external_insights block)

```json
{
  "url": "https://example.com",
  "overall_score": 78,
  "categories": [ "..." ],
  "external_insights": {
    "similarweb": {
      "status": "ok",
      "data_source": "similarweb_api",
      "estimated_monthly_visits": { "value": 1500000, "display": "1.5M" },
      "visit_duration": { "value": 185, "display": "3m 5s" },
      "pages_per_visit": { "value": 3.2, "display": "3.20" },
      "bounce_rate": { "value": 0.45, "display": "45.0%" },
      "traffic_channels": [
        { "channel": "direct", "share": 0.35 },
        { "channel": "search", "share": 0.40 },
        { "channel": "social", "share": 0.10 }
      ],
      "top_countries": [
        { "country": "US", "share": 0.55 },
        { "country": "GB", "share": 0.12 }
      ],
      "top_referring_sites": [{ "domain": "referrer.com", "share": 0.05 }],
      "similar_sites": [{ "domain": "competitor.com", "affinity": 0.82 }]
    },
    "semrush": {
      "status": "ok",
      "data_source": "semrush_api",
      "organic_keywords": [
        { "keyword": "seo tools", "position": 5, "url": "https://example.com", "volume": 12000 }
      ],
      "keyword_distribution": [
        { "range": "1-3", "count": 15 },
        { "range": "4-10", "count": 42 },
        { "range": "11-20", "count": 78 },
        { "range": "21-100", "count": 230 }
      ],
      "estimated_organic_traffic": { "value": 85000, "display": "85.0K" },
      "backlink_summary": {
        "total_backlinks": 15200,
        "referring_domains": 890,
        "follow_count": 12000,
        "nofollow_count": 3200
      },
      "top_backlinks": [{ "source_url": "https://blog.example.org/post", "anchor": "example" }],
      "organic_competitors": [{ "domain": "rival.com", "affinity": 0.75 }]
    }
  }
}
```

### When API Keys Are Missing

```json
{
  "external_insights": {
    "similarweb": { "status": "not_configured", "data_source": "none" },
    "semrush": { "status": "not_configured", "data_source": "none" }
  }
}
```

### Architecture

```
app/
├── providers/
│   ├── base.py           # Abstract provider interface + error handling
│   ├── similarweb.py     # Similarweb API client + response mapper
│   └── semrush.py        # SEMrush API client + response mapper
├── analyzers/
│   ├── traffic_intel.py  # Similarweb analyzer (caching + orchestration)
│   └── search_intel.py   # SEMrush analyzer (caching + orchestration)
├── external_models.py    # Pydantic models for all external insights
├── cache.py              # In-memory TTL cache (1hr default, 200 entries max)
└── utils.py              # Domain normalization + SSRF protection
tests/
├── test_utils.py         # Domain normalization + SSRF tests
├── test_providers.py     # Provider client tests with mocked HTTP
└── test_integration.py   # /api/audit integration tests with mocked providers
```

### Limitations

- External intelligence does **not** affect the core SEO 0–100 score
- Data is only available through official APIs — no scraping
- In-memory cache (not shared across workers); configure `CACHE_TTL_SECONDS` and `CACHE_MAX_ENTRIES` in `app/config.py`
- SEMrush defaults to US database (`database=us`); modify in `app/providers/semrush.py` for other regions

### Running Tests

```bash
pip install pytest httpx
python -m pytest tests/ -v
```

## Tech Stack

- **Backend** — FastAPI, BeautifulSoup, lxml, requests
- **Frontend** — Vanilla JS, Tailwind CSS

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

## Tech Stack

- **Backend** — FastAPI, BeautifulSoup, lxml, requests
- **Frontend** — Vanilla JS, Tailwind CSS

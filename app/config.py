REQUEST_TIMEOUT = 15
SECONDARY_TIMEOUT = 5
MAX_PAGE_SIZE_KB = 3000
TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60
DESCRIPTION_MIN_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 160
H1_MAX_LENGTH = 70

# Crawl settings
CRAWL_MAX_PAGES = 20
CRAWL_TIMEOUT = 10
CRAWL_DELAY = 0.2

# WAVE WebAIM API
WAVE_API_KEY = "ApIXTC826335"
WAVE_API_TIMEOUT = 30

# 14 single-page categories (sum = 1.0); crawl has its own endpoint
CATEGORY_WEIGHTS = {
    "meta_tags": 0.10,
    "performance": 0.09,
    "tracking": 0.07,
    "images": 0.07,
    "links": 0.07,
    "headings": 0.05,
    "mobile": 0.06,
    "semantic": 0.05,
    "structured_data": 0.07,
    "sitemap": 0.05,
    "robots": 0.04,
    "ads_quality": 0.08,
    "serp_features": 0.07,
    "accessibility": 0.13,
}

USER_AGENT = (
    "Mozilla/5.0 (compatible; SEOAuditor/1.0; +https://github.com/seo-auditor)"
)

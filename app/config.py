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

# --- External Intelligence APIs ---
import os

SIMILARWEB_API_KEY = os.environ.get("SIMILARWEB_API_KEY", "")
SEMRUSH_API_KEY = os.environ.get("SEMRUSH_API_KEY", "")

EXTERNAL_API_TIMEOUT = 20  # seconds per external API call
EXTERNAL_MODULE_TIMEOUT = 30  # total timeout for all external modules

# --- Cache ---
CACHE_TTL_SECONDS = 3600  # 1 hour
CACHE_MAX_ENTRIES = 200

# --- PageSpeed Insights ---
PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", "")
PAGESPEED_TIMEOUT = 25
PAGESPEED_CACHE_TTL = 21600  # 6h
PAGESPEED_RPM = 30

# --- Schema Validator ---
SCHEMA_DEFS_CACHE_TTL = 604800  # 7 days

# --- Keyword Planner (privilege-gated) ---
FEATURE_KEYWORD_PLANNER_ENABLED = os.environ.get("FEATURE_KEYWORD_PLANNER_ENABLED", "false").lower() == "true"
KEYWORD_PLANNER_ADMIN_TOKEN = os.environ.get("KEYWORD_PLANNER_ADMIN_TOKEN", "")
GOOGLE_ADS_DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
GOOGLE_ADS_CLIENT_ID = os.environ.get("GOOGLE_ADS_CLIENT_ID", "")
GOOGLE_ADS_CLIENT_SECRET = os.environ.get("GOOGLE_ADS_CLIENT_SECRET", "")
GOOGLE_ADS_REFRESH_TOKEN = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN", "")
GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
GOOGLE_ADS_CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "")
KEYWORD_CACHE_TTL = 86400  # 24h
KEYWORD_RPM = 10

# --- Database ---
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./seo_auditor.db")

# --- Uploads ---
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"))
UPLOAD_MAX_SIZE_MB = 5
UPLOAD_ALLOWED_TYPES = {"image/png", "image/jpeg", "image/svg+xml", "image/webp"}

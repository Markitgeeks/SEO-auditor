from __future__ import annotations

import math
from datetime import datetime, timezone

from fpdf import FPDF

from app.config import CATEGORY_WEIGHTS
from app.models import AuditResponse, CategoryResult, Issue

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------
BRAND_WARM = (200, 199, 197)   # #C8C7C5 - primary brand tone
BRAND_DARK = (45, 42, 38)      # near-black for text
BRAND_BG = (250, 249, 247)     # warm off-white page background
BRAND_CARD = (255, 255, 255)   # white card surfaces
BRAND_ACCENT = (165, 132, 100) # warm bronze accent
BRAND_LINE = (225, 222, 218)   # subtle dividers

# Severity / score colours
GREEN = (34, 160, 80)
YELLOW = (210, 150, 20)
RED = (200, 55, 50)
BLUE = (60, 120, 200)
LIGHT_GREEN = (230, 245, 235)
LIGHT_YELLOW = (255, 248, 230)
LIGHT_RED = (252, 235, 235)
LIGHT_BLUE = (232, 242, 255)
WHITE = (255, 255, 255)
GREY = (140, 140, 140)

CATEGORY_LABELS: dict[str, str] = {
    "meta_tags": "Meta Tags",
    "headings": "Headings",
    "images": "Images",
    "links": "Links",
    "performance": "Performance",
    "mobile": "Mobile",
    "structured_data": "Structured Data",
    "sitemap": "Sitemap",
    "robots": "Robots.txt",
    "tracking": "Tracking & Analytics",
    "semantic": "Semantic Structure",
    "ads_quality": "Ads Landing Page Quality",
    "serp_features": "SERP Feature Eligibility",
    "accessibility": "Accessibility (WAVE)",
}

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "meta_tags": "Title tag, meta description, canonical URL, Open Graph and Twitter Card tags.",
    "headings": "H1 presence, heading hierarchy, structure and length.",
    "images": "Alt text, dimensions, lazy loading attributes.",
    "links": "Internal/external link counts, empty hrefs, nofollow usage.",
    "performance": "Response time, page size, HTTPS, render-blocking scripts.",
    "mobile": "Viewport meta tag, responsive design, fixed-width elements.",
    "structured_data": "JSON-LD, Microdata, RDFa, OpenGraph, Dublin Core with rich snippet validation.",
    "sitemap": "Sitemap.xml accessibility, URL entries, freshness.",
    "robots": "Robots.txt rules, sitemap reference, crawl permissions.",
    "tracking": "Analytics (GA4), Tag Manager, verification tags, marketing pixels.",
    "semantic": "HTML5 semantic elements, ARIA roles, content-to-HTML ratio.",
    "ads_quality": "HTTPS, load speed, mobile viewport, content depth, CTAs, conversion tracking.",
    "serp_features": "Schema-based SERP eligibility, sitelinks, image pack, meta robots checks.",
    "accessibility": "WCAG compliance via WAVE: errors, contrast, alerts, ARIA, structural elements.",
}

SEVERITY_COLORS: dict[str, tuple[int, int, int]] = {
    "error": RED,
    "warning": YELLOW,
    "info": BLUE,
    "pass": GREEN,
}

SEVERITY_BG: dict[str, tuple[int, int, int]] = {
    "error": LIGHT_RED,
    "warning": LIGHT_YELLOW,
    "info": LIGHT_BLUE,
    "pass": LIGHT_GREEN,
}

# ---------------------------------------------------------------------------
# AIOSEO additional findings (from external audit)
# ---------------------------------------------------------------------------
AIOSEO_FINDINGS: list[dict[str, str]] = [
    {
        "category": "Basic SEO",
        "severity": "warning",
        "finding": "Title and meta description are missing target keywords. Include focus keywords naturally in both.",
    },
    {
        "category": "Basic SEO",
        "severity": "warning",
        "finding": "Meta description is too long (179 chars). Recommended maximum is 160 characters.",
    },
    {
        "category": "Images",
        "severity": "error",
        "finding": "23 images have no alt attribute. Every image should have descriptive alt text for accessibility and SEO.",
    },
    {
        "category": "Open Graph",
        "severity": "warning",
        "finding": "Missing og:image meta tag. Social shares will lack a preview image.",
    },
    {
        "category": "Performance",
        "severity": "warning",
        "finding": "Server not using 'expires' headers for images. Enable browser caching for static assets.",
    },
    {
        "category": "Performance",
        "severity": "warning",
        "finding": "Some JavaScript files are not minified (9 files identified including third-party scripts).",
    },
    {
        "category": "Performance",
        "severity": "warning",
        "finding": "Some CSS files are not minified (theme.css identified).",
    },
    {
        "category": "Performance",
        "severity": "error",
        "finding": "Page makes 189 HTTP requests (140 images, 46 JS, 3 CSS). Target under 20 requests for optimal loading.",
    },
    {
        "category": "Performance",
        "severity": "warning",
        "finding": "HTML document size is 78 KB, exceeding the recommended 50 KB maximum. Reduce inline CSS and remove unnecessary markup.",
    },
    {
        "category": "Security",
        "severity": "pass",
        "finding": "Site uses HTTPS. Directory listing is disabled. Not flagged by Google Safe Browsing.",
    },
    {
        "category": "Robots.txt",
        "severity": "info",
        "finding": "Shopify robots.txt contains 165+ rules. Verify only intended paths are blocked from indexing.",
    },
    {
        "category": "Schema.org",
        "severity": "pass",
        "finding": "Schema.org structured data detected on the page.",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_UNICODE_REPLACEMENTS: dict[str, str] = {
    "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-",
    "\u00a0": " ", "\u2192": "->", "\u2190": "<-", "\u2713": "v", "\u2717": "x",
}


def _safe(text: str) -> str:
    for orig, repl in _UNICODE_REPLACEMENTS.items():
        text = text.replace(orig, repl)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _score_color(score: int) -> tuple[int, int, int]:
    if score >= 80:
        return GREEN
    if score >= 50:
        return YELLOW
    return RED


def _score_label(score: int) -> str:
    if score >= 80:
        return "Good"
    if score >= 50:
        return "Needs Work"
    return "Poor"


def _score_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


# ===================================================================
# PDF class
# ===================================================================

class BrandedPDF(FPDF):
    def __init__(self, logo_path: str | None = None) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)  # manual page breaks only
        self.logo_path = logo_path
        self._page_num = 0
        self._bottom = self.h - 22  # usable bottom margin

    def header(self) -> None:
        # Skip header on page 1 (cover)
        if self.page_no() == 1:
            return
        # Warm background
        self.set_fill_color(*BRAND_BG)
        self.rect(0, 0, self.w, self.h, "F")
        # Top bar
        self.set_fill_color(*BRAND_WARM)
        self.rect(0, 0, self.w, 1.5, "F")
        # Logo in header (small)
        if self.logo_path:
            try:
                self.image(self.logo_path, 15, 5, h=8)
            except Exception:
                pass
        # Page title right-aligned
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GREY)
        self.set_xy(self.w - 60, 5)
        self.cell(45, 5, "SEO Audit Report  |  rikumo.com", align="R")
        self.set_y(18)

    def footer(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GREY)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")
        # Bottom accent line
        self.set_draw_color(*BRAND_WARM)
        self.set_line_width(0.5)
        self.line(15, self.h - 10, self.w - 15, self.h - 10)

    def _card(self, x: float, y: float, w: float, h: float) -> None:
        """Draw a white card with subtle shadow."""
        # Shadow
        self.set_fill_color(220, 218, 215)
        self.rect(x + 0.5, y + 0.5, w, h, "F")
        # Card
        self.set_fill_color(*BRAND_CARD)
        self.rect(x, y, w, h, "F")

    def _section_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*BRAND_DARK)
        self.set_x(15)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        # Accent underline
        y = self.get_y()
        self.set_draw_color(*BRAND_ACCENT)
        self.set_line_width(0.8)
        self.line(15, y, 55, y)
        self.set_draw_color(*BRAND_LINE)
        self.set_line_width(0.3)
        self.line(55, y, self.w - 15, y)
        self.set_y(y + 4)

    def _severity_badge(self, x: float, y: float, severity: str) -> float:
        color = SEVERITY_COLORS.get(severity, GREY)
        bg = SEVERITY_BG.get(severity, (240, 240, 240))
        label = severity.upper()
        self.set_font("Helvetica", "B", 6)
        badge_w = self.get_string_width(label) + 5
        badge_h = 4.5
        # Rounded-ish bg
        self.set_fill_color(*bg)
        self.rect(x, y, badge_w, badge_h, "F")
        # Left accent bar
        self.set_fill_color(*color)
        self.rect(x, y, 1, badge_h, "F")
        self.set_text_color(*color)
        self.set_xy(x + 1, y + 0.2)
        self.cell(badge_w - 1, badge_h, label, align="C")
        return badge_w


# ===================================================================
# Renderers
# ===================================================================

def _render_cover(pdf: BrandedPDF, data: AuditResponse) -> None:
    pdf.add_page()
    # Full background
    pdf.set_fill_color(*BRAND_BG)
    pdf.rect(0, 0, pdf.w, pdf.h, "F")

    # Top accent strip
    pdf.set_fill_color(*BRAND_ACCENT)
    pdf.rect(0, 0, pdf.w, 3, "F")

    # Logo centered
    if pdf.logo_path:
        try:
            logo_w = 65
            pdf.image(pdf.logo_path, (pdf.w - logo_w) / 2, 30, w=logo_w)
        except Exception:
            pass

    # Title
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GREY)
    pdf.set_y(62)
    pdf.cell(0, 6, "COMPREHENSIVE", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*BRAND_DARK)
    pdf.set_y(70)
    pdf.cell(0, 14, "SEO Audit Report", align="C", new_x="LMARGIN", new_y="NEXT")

    # Thin divider
    pdf.set_draw_color(*BRAND_WARM)
    pdf.set_line_width(0.5)
    pdf.line(pdf.w / 2 - 30, 88, pdf.w / 2 + 30, 88)

    # URL
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*BRAND_ACCENT)
    pdf.set_y(93)
    pdf.cell(0, 7, _safe(data.url), align="C", new_x="LMARGIN", new_y="NEXT")

    # Date
    now = datetime.now(timezone.utc).strftime("%B %d, %Y")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    pdf.set_y(103)
    pdf.cell(0, 5, f"Generated on {now}", align="C", new_x="LMARGIN", new_y="NEXT")

    # --- Score gauge card ---
    card_w, card_h = 100, 90
    card_x = (pdf.w - card_w) / 2
    card_y = 118
    pdf._card(card_x, card_y, card_w, card_h)

    cx = pdf.w / 2
    cy = card_y + 42
    radius = 30
    score = data.overall_score
    color = _score_color(score)

    # Background arc
    start_angle = 135
    sweep = 270
    pdf.set_draw_color(*BRAND_LINE)
    pdf.set_line_width(4)
    _draw_arc(pdf, cx, cy, radius, start_angle, start_angle + sweep)

    # Foreground arc
    fg_sweep = sweep * score / 100
    if fg_sweep > 0:
        pdf.set_draw_color(*color)
        pdf.set_line_width(4)
        _draw_arc(pdf, cx, cy, radius, start_angle, start_angle + fg_sweep)

    # Score number
    pdf.set_font("Helvetica", "B", 30)
    pdf.set_text_color(*color)
    s = str(score)
    tw = pdf.get_string_width(s)
    pdf.set_xy(cx - tw / 2, cy - 9)
    pdf.cell(tw, 12, s)

    # Label & grade
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    lbl = f"{_score_label(score)}  ({_score_grade(score)})"
    lw = pdf.get_string_width(lbl)
    pdf.set_xy(cx - lw / 2, cy + 6)
    pdf.cell(lw, 5, lbl)

    pdf.set_font("Helvetica", "", 7)
    ow = pdf.get_string_width("out of 100")
    pdf.set_xy(cx - ow / 2, cy + 13)
    pdf.cell(ow, 4, "out of 100")

    # --- Summary stats row ---
    errors = sum(1 for c in data.categories for i in c.issues if i.severity == "error")
    warnings = sum(1 for c in data.categories for i in c.issues if i.severity == "warning")
    infos = sum(1 for c in data.categories for i in c.issues if i.severity == "info")
    passes = sum(1 for c in data.categories for i in c.issues if i.severity == "pass")

    stats_y = card_y + card_h + 12
    stat_items = [
        (str(errors), "Errors", RED),
        (str(warnings), "Warnings", YELLOW),
        (str(infos), "Info", BLUE),
        (str(passes), "Passed", GREEN),
    ]
    stat_w = 35
    total_w = stat_w * len(stat_items)
    sx = (pdf.w - total_w) / 2

    for num, label, clr in stat_items:
        pdf._card(sx, stats_y, stat_w - 3, 22)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*clr)
        pdf.set_xy(sx, stats_y + 3)
        pdf.cell(stat_w - 3, 8, num, align="C")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*GREY)
        pdf.set_xy(sx, stats_y + 12)
        pdf.cell(stat_w - 3, 5, label, align="C")
        sx += stat_w

    # Category count badge
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GREY)
    pdf.set_y(stats_y + 28)
    cat_count = len(data.categories)
    pdf.cell(0, 5, f"{cat_count} categories analyzed  |  WAVE accessibility  |  SERP features  |  Ads quality", align="C")

    # Bottom tagline
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*BRAND_ACCENT)
    pdf.set_y(stats_y + 42)
    pdf.cell(0, 5, "Prepared for Rikumo  |  Japanese Life Store", align="C")
    pdf.set_y(pdf.get_y() + 7)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 4, "Confidential  -  For internal use only", align="C")


def _draw_arc(pdf: BrandedPDF, cx: float, cy: float, r: float,
              start_deg: float, end_deg: float) -> None:
    steps = max(30, int(abs(end_deg - start_deg) / 2))
    pts: list[tuple[float, float]] = []
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    for i in range(len(pts) - 1):
        pdf.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])


# -------------------------------------------------------------------
# Page 2: Executive Summary with bar chart
# -------------------------------------------------------------------

def _render_summary(pdf: BrandedPDF, data: AuditResponse) -> None:
    pdf.add_page()
    pdf._section_title("Executive Summary")

    errors = sum(1 for c in data.categories for i in c.issues if i.severity == "error")
    warnings = sum(1 for c in data.categories for i in c.issues if i.severity == "warning")
    infos = sum(1 for c in data.categories for i in c.issues if i.severity == "info")
    passes = sum(1 for c in data.categories for i in c.issues if i.severity == "pass")
    total = errors + warnings + infos + passes

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BRAND_DARK)
    pdf.set_x(15)
    pdf.cell(0, 5, f"Total findings: {total}  |  {errors} errors  |  {warnings} warnings  |  {infos} info  |  {passes} passed",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(pdf.get_y() + 3)

    # --- Donut chart for issue distribution ---
    chart_cx = 45
    chart_cy = pdf.get_y() + 25
    chart_r = 18
    chart_inner_r = 11

    slices = [
        (errors, RED, "Errors"),
        (warnings, YELLOW, "Warnings"),
        (infos, BLUE, "Info"),
        (passes, GREEN, "Passed"),
    ]
    total_issues = sum(s[0] for s in slices)
    if total_issues > 0:
        start = -90
        for count, color, label in slices:
            if count == 0:
                continue
            sweep_deg = 360 * count / total_issues
            _draw_donut_slice(pdf, chart_cx, chart_cy, chart_r, chart_inner_r, start, start + sweep_deg, color)
            start += sweep_deg

    # Center text
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*BRAND_DARK)
    tw = pdf.get_string_width(str(total_issues))
    pdf.set_xy(chart_cx - tw / 2, chart_cy - 5)
    pdf.cell(tw, 6, str(total_issues))
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(*GREY)
    tw2 = pdf.get_string_width("findings")
    pdf.set_xy(chart_cx - tw2 / 2, chart_cy + 2)
    pdf.cell(tw2, 4, "findings")

    # Legend
    legend_x = 72
    legend_y = chart_cy - 14
    for count, color, label in slices:
        pdf.set_fill_color(*color)
        pdf.rect(legend_x, legend_y + 1.5, 3, 3, "F")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*BRAND_DARK)
        pdf.set_xy(legend_x + 5, legend_y)
        pdf.cell(30, 6, f"{label}: {count}")
        legend_y += 7

    # --- Horizontal bar chart ---
    bar_start_y = chart_cy + 35
    pdf.set_y(bar_start_y - 8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*BRAND_DARK)
    pdf.set_x(15)
    pdf.cell(0, 7, "Category Scores", new_x="LMARGIN", new_y="NEXT")

    bar_x = 62
    bar_max_w = pdf.w - bar_x - 28
    y = bar_start_y

    sorted_cats = sorted(data.categories, key=lambda c: CATEGORY_WEIGHTS.get(c.name, 0), reverse=True)

    for cat in sorted_cats:
        label = CATEGORY_LABELS.get(cat.name, cat.name)
        weight = CATEGORY_WEIGHTS.get(cat.name, 0)
        color = _score_color(cat.score)

        # Label
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*BRAND_DARK)
        pdf.set_xy(15, y)
        pdf.cell(bar_x - 17, 5, label, align="R")

        # Bar background
        pdf.set_fill_color(*BRAND_LINE)
        pdf.rect(bar_x, y + 1, bar_max_w, 3, "F")

        # Bar fill
        fill_w = bar_max_w * cat.score / 100
        if fill_w > 0:
            pdf.set_fill_color(*color)
            pdf.rect(bar_x, y + 1, fill_w, 3, "F")

        # Score
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*color)
        pdf.set_xy(bar_x + bar_max_w + 2, y)
        pdf.cell(12, 5, str(cat.score))

        # Weight
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(*GREY)
        pdf.set_xy(bar_x + bar_max_w + 14, y + 0.5)
        pdf.cell(10, 4, f"{int(weight * 100)}%")

        y += 7.5


def _draw_donut_slice(pdf: BrandedPDF, cx: float, cy: float,
                      outer_r: float, inner_r: float,
                      start_deg: float, end_deg: float,
                      color: tuple[int, int, int]) -> None:
    """Draw a filled donut slice using filled triangles."""
    pdf.set_fill_color(*color)
    steps = max(10, int(abs(end_deg - start_deg) / 3))
    for i in range(steps):
        a1 = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        a2 = math.radians(start_deg + (end_deg - start_deg) * (i + 1) / steps)
        # Outer arc segment
        x1 = cx + outer_r * math.cos(a1)
        y1 = cy + outer_r * math.sin(a1)
        x2 = cx + outer_r * math.cos(a2)
        y2 = cy + outer_r * math.sin(a2)
        # Inner arc segment
        x3 = cx + inner_r * math.cos(a2)
        y3 = cy + inner_r * math.sin(a2)
        x4 = cx + inner_r * math.cos(a1)
        y4 = cy + inner_r * math.sin(a1)
        # Draw as polygon (quad)
        pdf.polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], style="F")


# -------------------------------------------------------------------
# Page 3: Score radar / grade cards
# -------------------------------------------------------------------

def _render_scorecard(pdf: BrandedPDF, data: AuditResponse) -> None:
    pdf.add_page()
    pdf._section_title("Category Scorecards")

    sorted_cats = sorted(data.categories, key=lambda c: CATEGORY_WEIGHTS.get(c.name, 0), reverse=True)

    card_w = (pdf.w - 30 - 8) / 3  # 3 columns
    card_h = 24
    margin = 3
    x_start = 15
    y_start = pdf.get_y() + 2
    col = 0
    row_y = y_start

    for cat in sorted_cats:
        # Page break if needed for a new row
        if col == 0 and row_y + card_h > pdf._bottom:
            pdf.add_page()
            pdf.set_y(20)
            row_y = 20

        x = x_start + col * (card_w + margin)
        color = _score_color(cat.score)
        label = CATEGORY_LABELS.get(cat.name, cat.name)
        grade = _score_grade(cat.score)
        weight = CATEGORY_WEIGHTS.get(cat.name, 0)

        errs = sum(1 for i in cat.issues if i.severity == "error")
        warns = sum(1 for i in cat.issues if i.severity == "warning")

        # Card
        pdf._card(x, row_y, card_w, card_h)

        # Left colour accent
        pdf.set_fill_color(*color)
        pdf.rect(x, row_y, 2, card_h, "F")

        # Category name
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*BRAND_DARK)
        pdf.set_xy(x + 5, row_y + 1.5)
        pdf.cell(card_w - 22, 4, label)

        # Grade circle
        gcx = x + card_w - 9
        gcy = row_y + 8
        pdf.set_fill_color(*color)
        pdf.ellipse(gcx - 4.5, gcy - 4.5, 9, 9, "F")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*WHITE)
        gw = pdf.get_string_width(grade)
        pdf.set_xy(gcx - gw / 2, gcy - 2.5)
        pdf.cell(gw, 5, grade)

        # Score number
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*color)
        pdf.set_xy(x + 5, row_y + 7)
        pdf.cell(20, 6, str(cat.score))

        pdf.set_font("Helvetica", "", 5.5)
        pdf.set_text_color(*GREY)
        pdf.set_xy(x + 5, row_y + 14)
        pdf.cell(20, 3, f"/ 100  ({int(weight*100)}% weight)")

        # Error/warning badges
        badge_y = row_y + 18.5
        if errs:
            pdf.set_font("Helvetica", "", 5.5)
            pdf.set_text_color(*RED)
            pdf.set_xy(x + 5, badge_y)
            pdf.cell(15, 3, f"{errs} error{'s' if errs > 1 else ''}")
        if warns:
            pdf.set_font("Helvetica", "", 5.5)
            pdf.set_text_color(*YELLOW)
            pdf.set_xy(x + 22 if errs else x + 5, badge_y)
            pdf.cell(15, 3, f"{warns} warning{'s' if warns > 1 else ''}")

        col += 1
        if col >= 3:
            col = 0
            row_y += card_h + margin

    # Handle last incomplete row — no extra gap, let next section flow naturally
    if col > 0:
        # Incomplete row — advance past it
        pdf.set_y(row_y + card_h + 2)
    else:
        pdf.set_y(row_y + 2)


# -------------------------------------------------------------------
# Category detail pages
# -------------------------------------------------------------------

def _estimate_issue_height(pdf: BrandedPDF, message: str) -> float:
    """Estimate how tall an issue row will be."""
    pdf.set_font("Helvetica", "", 7.5)
    badge_w = 22  # approx badge width
    text_x = 17 + badge_w + 3
    text_w = pdf.w - text_x - 17
    lines = max(1, math.ceil(pdf.get_string_width(_safe(message)) / text_w))
    return max(5.5, lines * 4) + 1


def _render_category_detail(pdf: BrandedPDF, cat: CategoryResult) -> None:
    label = CATEGORY_LABELS.get(cat.name, cat.name)
    weight = CATEGORY_WEIGHTS.get(cat.name, 0)
    color = _score_color(cat.score)
    desc = CATEGORY_DESCRIPTIONS.get(cat.name, "")

    # Need at least header (16) + desc (6) + one issue row (7) = ~30mm
    min_needed = 30
    if pdf.get_y() + min_needed > pdf._bottom:
        pdf.add_page()
        pdf.set_y(20)

    y = pdf.get_y()

    # Category header card
    header_h = 14
    pdf._card(15, y, pdf.w - 30, header_h)

    # Left color bar
    pdf.set_fill_color(*color)
    pdf.rect(15, y, 2.5, header_h, "F")

    # Name
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BRAND_DARK)
    pdf.set_xy(20, y + 1.5)
    pdf.cell(80, 5, label)

    # Score
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*color)
    pdf.set_xy(pdf.w - 55, y + 1)
    pdf.cell(15, 6, str(cat.score), align="R")

    # Weight
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GREY)
    pdf.set_xy(pdf.w - 37, y + 2.5)
    pdf.cell(15, 5, f"({int(weight*100)}% weight)")

    # Progress bar
    bar_y = y + 9.5
    bar_w = pdf.w - 40
    pdf.set_fill_color(*BRAND_LINE)
    pdf.rect(20, bar_y, bar_w, 2, "F")
    fill_w = bar_w * cat.score / 100
    if fill_w > 0:
        pdf.set_fill_color(*color)
        pdf.rect(20, bar_y, fill_w, 2, "F")

    pdf.set_y(y + header_h + 1)

    # Description
    if desc:
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*GREY)
        pdf.set_x(17)
        pdf.cell(0, 3.5, _safe(desc), new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(pdf.get_y() + 1)

    # Issues
    if not cat.issues:
        pdf.set_font("Helvetica", "I", 7.5)
        pdf.set_text_color(*GREEN)
        pdf.set_x(17)
        pdf.cell(0, 4.5, "No issues found.", new_x="LMARGIN", new_y="NEXT")
    else:
        for issue in cat.issues:
            row_h = _estimate_issue_height(pdf, issue.message)
            iy = pdf.get_y()

            # Check if badge + text fits; if not, break BEFORE drawing badge
            if iy + row_h > pdf._bottom:
                pdf.add_page()
                pdf.set_y(20)
                iy = 20

            badge_w = pdf._severity_badge(17, iy + 0.5, issue.severity)

            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*BRAND_DARK)
            text_x = 17 + badge_w + 3
            text_w = pdf.w - text_x - 17
            pdf.set_xy(text_x, iy)
            pdf.multi_cell(text_w, 4, _safe(issue.message))
            if pdf.get_y() < iy + 5.5:
                pdf.set_y(iy + 5.5)
            pdf.set_y(pdf.get_y() + 0.3)

    pdf.set_y(pdf.get_y() + 3)


# -------------------------------------------------------------------
# AIOSEO Additional Findings
# -------------------------------------------------------------------

def _render_aioseo_findings(pdf: BrandedPDF) -> None:
    # Start on same page if enough room for title + at least a few findings
    if pdf.get_y() + 30 > pdf._bottom:
        pdf.add_page()
    pdf._section_title("Additional Findings (AIOSEO Audit)")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GREY)
    pdf.set_x(15)
    pdf.cell(0, 5, "Key findings from the AIOSEO analysis report, integrated for comprehensive coverage.",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(pdf.get_y() + 3)

    current_cat = ""
    for finding in AIOSEO_FINDINGS:
        cat = finding["category"]
        # Estimate row height
        row_h = _estimate_issue_height(pdf, finding["finding"])
        cat_header_h = 7 if cat != current_cat else 0
        needed = cat_header_h + row_h

        if pdf.get_y() + needed > pdf._bottom:
            pdf.add_page()
            pdf.set_y(20)

        if cat != current_cat:
            current_cat = cat
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*BRAND_ACCENT)
            pdf.set_x(15)
            pdf.cell(0, 5, cat, new_x="LMARGIN", new_y="NEXT")
            pdf.set_y(pdf.get_y() + 1)

        iy = pdf.get_y()
        badge_w = pdf._severity_badge(20, iy + 0.5, finding["severity"])

        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*BRAND_DARK)
        text_x = 20 + badge_w + 3
        text_w = pdf.w - text_x - 17
        pdf.set_xy(text_x, iy)
        pdf.multi_cell(text_w, 4, _safe(finding["finding"]))
        if pdf.get_y() < iy + 5.5:
            pdf.set_y(iy + 5.5)
        pdf.set_y(pdf.get_y() + 1)


# -------------------------------------------------------------------
# Recommendations page
# -------------------------------------------------------------------

def _render_recommendations(pdf: BrandedPDF, data: AuditResponse) -> None:
    # Flow from previous section if room
    if pdf.get_y() + 40 > pdf._bottom:
        pdf.add_page()
    pdf._section_title("Top Priority Fixes")

    sorted_cats = sorted(data.categories, key=lambda c: CATEGORY_WEIGHTS.get(c.name, 0), reverse=True)

    # Errors
    has_errors = False
    priority = 1
    for cat in sorted_cats:
        errors = [i for i in cat.issues if i.severity == "error"]
        if not errors:
            continue
        has_errors = True
        label = CATEGORY_LABELS.get(cat.name, cat.name)

        if pdf.get_y() + 12 > pdf._bottom:
            pdf.add_page()
            pdf.set_y(20)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*RED)
        pdf.set_x(15)
        pdf.cell(0, 5, f"{label}", new_x="LMARGIN", new_y="NEXT")

        for issue in errors:
            row_h = _estimate_issue_height(pdf, f"{priority}. {issue.message}")
            if pdf.get_y() + row_h > pdf._bottom:
                pdf.add_page()
                pdf.set_y(20)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*BRAND_DARK)
            pdf.set_x(20)
            pdf.multi_cell(pdf.w - 40, 4, _safe(f"{priority}. {issue.message}"))
            priority += 1
        pdf.set_y(pdf.get_y() + 2)

    if not has_errors:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREEN)
        pdf.set_x(15)
        pdf.cell(0, 5, "No critical errors found.", new_x="LMARGIN", new_y="NEXT")

    # AIOSEO errors
    aioseo_errors = [f for f in AIOSEO_FINDINGS if f["severity"] == "error"]
    if aioseo_errors:
        pdf.set_y(pdf.get_y() + 2)
        if pdf.get_y() + 12 > pdf._bottom:
            pdf.add_page()
            pdf.set_y(20)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*RED)
        pdf.set_x(15)
        pdf.cell(0, 5, "Additional Critical Issues (AIOSEO)", new_x="LMARGIN", new_y="NEXT")
        for f in aioseo_errors:
            msg = f"{priority}. [{f['category']}] {f['finding']}"
            row_h = _estimate_issue_height(pdf, msg)
            if pdf.get_y() + row_h > pdf._bottom:
                pdf.add_page()
                pdf.set_y(20)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*BRAND_DARK)
            pdf.set_x(20)
            pdf.multi_cell(pdf.w - 40, 4, _safe(msg))
            priority += 1

    # Warnings
    pdf.set_y(pdf.get_y() + 4)
    if pdf.get_y() + 15 > pdf._bottom:
        pdf.add_page()
        pdf.set_y(20)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*YELLOW)
    pdf.set_x(15)
    pdf.cell(0, 6, "Warnings", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(pdf.get_y() + 1)

    has_warnings = False
    for cat in sorted_cats:
        warns = [i for i in cat.issues if i.severity == "warning"]
        if not warns:
            continue
        has_warnings = True
        label = CATEGORY_LABELS.get(cat.name, cat.name)

        if pdf.get_y() + 12 > pdf._bottom:
            pdf.add_page()
            pdf.set_y(20)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*YELLOW)
        pdf.set_x(15)
        pdf.cell(0, 5, label, new_x="LMARGIN", new_y="NEXT")

        for issue in warns:
            msg = f"- {issue.message}"
            row_h = _estimate_issue_height(pdf, msg)
            if pdf.get_y() + row_h > pdf._bottom:
                pdf.add_page()
                pdf.set_y(20)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*BRAND_DARK)
            pdf.set_x(20)
            pdf.multi_cell(pdf.w - 40, 4, _safe(msg))
        pdf.set_y(pdf.get_y() + 1.5)

    # AIOSEO warnings
    aioseo_warns = [f for f in AIOSEO_FINDINGS if f["severity"] == "warning"]
    if aioseo_warns:
        pdf.set_y(pdf.get_y() + 2)
        if pdf.get_y() + 12 > pdf._bottom:
            pdf.add_page()
            pdf.set_y(20)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*YELLOW)
        pdf.set_x(15)
        pdf.cell(0, 5, "Additional Warnings (AIOSEO)", new_x="LMARGIN", new_y="NEXT")
        for f in aioseo_warns:
            msg = f"- [{f['category']}] {f['finding']}"
            row_h = _estimate_issue_height(pdf, msg)
            if pdf.get_y() + row_h > pdf._bottom:
                pdf.add_page()
                pdf.set_y(20)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*BRAND_DARK)
            pdf.set_x(20)
            pdf.multi_cell(pdf.w - 40, 4, _safe(msg))

    if not has_warnings and not aioseo_warns:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREEN)
        pdf.set_x(15)
        pdf.cell(0, 5, "No warnings found.", new_x="LMARGIN", new_y="NEXT")


# -------------------------------------------------------------------
# Final summary page
# -------------------------------------------------------------------

def _render_closing(pdf: BrandedPDF, data: AuditResponse) -> None:
    # Only start new page if not enough room for the section (~90mm needed)
    if pdf.get_y() + 90 > pdf._bottom:
        pdf.add_page()
    pdf._section_title("Summary & Next Steps")

    score = data.overall_score
    color = _score_color(score)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BRAND_DARK)
    pdf.set_x(15)

    if score >= 80:
        summary = "The site demonstrates strong SEO fundamentals. Focus on addressing the remaining warnings to push the score higher."
    elif score >= 60:
        summary = "The site has a solid foundation but several areas need attention. Prioritize fixing errors first, then address warnings."
    else:
        summary = "The site needs significant SEO improvements. Address critical errors immediately and create an action plan for warnings."

    pdf.multi_cell(pdf.w - 30, 5, _safe(summary))
    pdf.set_y(pdf.get_y() + 6)

    # Action items summary
    items = [
        ("Immediate Action", "Fix all error-severity issues listed in the Priority Fixes section.", RED),
        ("Short Term", "Address warning-severity items, especially meta tags, image alt text, and performance.", YELLOW),
        ("Ongoing", "Monitor crawl stats, keep content fresh, maintain sitemap accuracy.", BLUE),
        ("Best Practice", "Regular audits recommended quarterly. Track score progression over time.", GREEN),
    ]

    for title, desc, clr in items:
        y = pdf.get_y()
        if y + 12 > pdf._bottom:
            pdf.add_page()
            pdf.set_y(20)
            y = 20

        pdf._card(15, y, pdf.w - 30, 12)
        pdf.set_fill_color(*clr)
        pdf.rect(15, y, 2, 12, "F")

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*clr)
        pdf.set_xy(20, y + 1)
        pdf.cell(30, 4, title)

        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*BRAND_DARK)
        pdf.set_xy(20, y + 5.5)
        pdf.cell(pdf.w - 40, 4, _safe(desc))

        pdf.set_y(y + 14)

    # Footer branding — placed right after action items
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_draw_color(*BRAND_WARM)
    pdf.set_line_width(0.3)
    pdf.line(15, pdf.get_y(), pdf.w - 15, pdf.get_y())
    pdf.set_y(pdf.get_y() + 5)

    if pdf.logo_path:
        try:
            pdf.image(pdf.logo_path, (pdf.w - 40) / 2, pdf.get_y(), w=40)
            pdf.set_y(pdf.get_y() + 14)
        except Exception:
            pass

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*BRAND_ACCENT)
    pdf.set_x(15)
    pdf.cell(0, 5, "Prepared for Rikumo  |  Japanese Life Store", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*GREY)
    pdf.set_x(15)
    pdf.cell(0, 4, "Confidential  -  For internal use only", align="C")


# ===================================================================
# Public API
# ===================================================================

def generate_branded_pdf(data: AuditResponse, logo_path: str | None = None) -> bytes:
    pdf = BrandedPDF(logo_path=logo_path)

    _render_cover(pdf, data)
    _render_summary(pdf, data)
    _render_scorecard(pdf, data)

    # Category details — flow from scorecard if room
    if pdf.get_y() + 40 > pdf._bottom:
        pdf.add_page()
    pdf._section_title("Category Details")

    sorted_cats = sorted(data.categories, key=lambda c: CATEGORY_WEIGHTS.get(c.name, 0), reverse=True)
    for cat in sorted_cats:
        _render_category_detail(pdf, cat)

    _render_aioseo_findings(pdf)
    _render_recommendations(pdf, data)
    _render_closing(pdf, data)

    return bytes(pdf.output())

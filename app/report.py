from __future__ import annotations

import math
from datetime import datetime, timezone
from io import BytesIO

from fpdf import FPDF

from app.config import CATEGORY_WEIGHTS
from app.models import AuditResponse, CategoryResult

# ---------------------------------------------------------------------------
# Colour constants (RGB tuples)
# ---------------------------------------------------------------------------
GREEN = (34, 197, 94)
YELLOW = (245, 158, 11)
RED = (239, 68, 68)
BLUE = (59, 130, 246)
DARK_BG = (30, 41, 59)
LIGHT_TEXT = (226, 232, 240)
WHITE = (255, 255, 255)
GREY = (148, 163, 184)
DARK_CARD = (51, 65, 85)

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
    "tracking": "Tracking & Pixels",
    "semantic": "Semantic Structure",
}

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "meta_tags": "Title tag, meta description, canonical URL, Open Graph and Twitter Card tags.",
    "headings": "H1 presence, heading hierarchy, structure and length.",
    "images": "Alt text, dimensions, lazy loading attributes.",
    "links": "Internal/external link counts, empty hrefs, nofollow usage.",
    "performance": "Response time, page size, HTTPS, render-blocking scripts.",
    "mobile": "Viewport meta tag, responsive design, fixed-width elements.",
    "structured_data": "JSON-LD, Microdata, RDFa structured markup.",
    "sitemap": "Sitemap.xml accessibility, URL entries, freshness.",
    "robots": "Robots.txt rules, sitemap reference, crawl permissions.",
    "tracking": "Analytics (GA4), Tag Manager, verification tags, marketing pixels.",
    "semantic": "HTML5 semantic elements, ARIA roles, content-to-HTML ratio.",
}

SEVERITY_COLORS: dict[str, tuple[int, int, int]] = {
    "error": RED,
    "warning": YELLOW,
    "info": BLUE,
    "pass": GREEN,
}


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


# ===================================================================
# PDF class
# ===================================================================

class SEOReportPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_color(self, rgb: tuple[int, int, int]) -> None:
        self.set_text_color(*rgb)

    def _draw_rounded_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        r: float,
        fill_color: tuple[int, int, int],
    ) -> None:
        self.set_fill_color(*fill_color)
        self.rect(x + r, y, w - 2 * r, h, "F")
        self.rect(x, y + r, w, h - 2 * r, "F")
        # corners
        for cx, cy in [
            (x + r, y + r),
            (x + w - r, y + r),
            (x + r, y + h - r),
            (x + w - r, y + h - r),
        ]:
            self.ellipse(cx - r, cy - r, 2 * r, 2 * r, "F")

    def _severity_badge(self, x: float, y: float, severity: str) -> float:
        color = SEVERITY_COLORS.get(severity, GREY)
        label = severity.upper()
        badge_w = self.get_string_width(label) + 6
        badge_h = 5.5
        # Background with reduced opacity effect (lighter tint)
        tint = tuple(min(255, c + 140) for c in color)
        self._draw_rounded_rect(x, y, badge_w, badge_h, 1.5, tint)  # type: ignore[arg-type]
        self.set_font("Helvetica", "B", 6.5)
        self._set_color(color)
        self.set_xy(x, y + 0.3)
        self.cell(badge_w, badge_h, label, align="C")
        return badge_w


# ===================================================================
# Page renderers
# ===================================================================

def _render_cover(pdf: SEOReportPDF, data: AuditResponse) -> None:
    pdf.add_page()
    page_w = pdf.w

    # Background fill
    pdf.set_fill_color(*DARK_BG)
    pdf.rect(0, 0, page_w, pdf.h, "F")

    # Title
    pdf.set_font("Helvetica", "B", 32)
    pdf._set_color(WHITE)
    pdf.set_y(50)
    pdf.cell(0, 14, "SEO Audit Report", align="C", new_x="LMARGIN", new_y="NEXT")

    # URL
    pdf.set_font("Helvetica", "", 13)
    pdf._set_color(GREY)
    pdf.set_y(72)
    pdf.cell(0, 8, data.url, align="C", new_x="LMARGIN", new_y="NEXT")

    # Date
    now = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_y(84)
    pdf.cell(0, 6, f"Generated {now}", align="C", new_x="LMARGIN", new_y="NEXT")

    # --- Score gauge (arc drawn with line segments) ---
    cx, cy = page_w / 2, 145
    radius = 38
    score = data.overall_score
    color = _score_color(score)

    # Background arc (270 degrees, from 135 to 405)
    start_angle = 135
    sweep = 270
    pdf.set_draw_color(80, 90, 110)
    pdf.set_line_width(3.5)
    _draw_arc(pdf, cx, cy, radius, start_angle, start_angle + sweep)

    # Foreground arc
    fg_sweep = sweep * score / 100
    if fg_sweep > 0:
        pdf.set_draw_color(*color)
        pdf.set_line_width(3.5)
        _draw_arc(pdf, cx, cy, radius, start_angle, start_angle + fg_sweep)

    # Score number
    pdf.set_font("Helvetica", "B", 36)
    pdf._set_color(color)
    score_str = str(score)
    tw = pdf.get_string_width(score_str)
    pdf.set_xy(cx - tw / 2, cy - 12)
    pdf.cell(tw, 14, score_str)

    # Label
    label = _score_label(score)
    pdf.set_font("Helvetica", "", 12)
    pdf._set_color(GREY)
    lw = pdf.get_string_width(label)
    pdf.set_xy(cx - lw / 2, cy + 6)
    pdf.cell(lw, 6, label)

    # "out of 100"
    pdf.set_font("Helvetica", "", 9)
    ow = pdf.get_string_width("out of 100")
    pdf.set_xy(cx - ow / 2, cy + 15)
    pdf.cell(ow, 5, "out of 100")

    # Issue summary counts at bottom
    errors = sum(1 for c in data.categories for i in c.issues if i.severity == "error")
    warnings = sum(1 for c in data.categories for i in c.issues if i.severity == "warning")
    infos = sum(1 for c in data.categories for i in c.issues if i.severity == "info")
    passes = sum(1 for c in data.categories for i in c.issues if i.severity == "pass")

    pdf.set_y(210)
    pdf.set_font("Helvetica", "", 11)
    summary_parts = [
        (f"{errors} Errors", RED),
        (f"{warnings} Warnings", YELLOW),
        (f"{infos} Info", BLUE),
        (f"{passes} Passed", GREEN),
    ]
    total_w = sum(pdf.get_string_width(t) + 18 for t, _ in summary_parts)
    x = (page_w - total_w) / 2
    for text, clr in summary_parts:
        pdf._set_color(clr)
        pdf.set_xy(x, 210)
        w = pdf.get_string_width(text) + 18
        pdf.cell(w, 8, text, align="C")
        x += w


def _draw_arc(
    pdf: SEOReportPDF,
    cx: float,
    cy: float,
    r: float,
    start_deg: float,
    end_deg: float,
) -> None:
    """Draw an arc as small line segments."""
    steps = max(30, int(abs(end_deg - start_deg) / 2))
    pts: list[tuple[float, float]] = []
    for i in range(steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * i / steps)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    for i in range(len(pts) - 1):
        pdf.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])


# -------------------------------------------------------------------

def _render_summary(pdf: SEOReportPDF, data: AuditResponse) -> None:
    pdf.add_page()
    pdf.set_fill_color(*DARK_BG)
    pdf.rect(0, 0, pdf.w, pdf.h, "F")

    pdf.set_font("Helvetica", "B", 20)
    pdf._set_color(WHITE)
    pdf.set_xy(15, 15)
    pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")

    # Horizontal separator
    pdf.set_draw_color(*GREY)
    pdf.set_line_width(0.3)
    pdf.line(15, 28, pdf.w - 15, 28)

    # Issue totals
    errors = sum(1 for c in data.categories for i in c.issues if i.severity == "error")
    warnings = sum(1 for c in data.categories for i in c.issues if i.severity == "warning")
    infos = sum(1 for c in data.categories for i in c.issues if i.severity == "info")
    passes = sum(1 for c in data.categories for i in c.issues if i.severity == "pass")
    total = errors + warnings + infos + passes

    pdf.set_y(33)
    pdf.set_font("Helvetica", "", 10)
    pdf._set_color(LIGHT_TEXT)
    pdf.set_x(15)
    pdf.cell(0, 6, f"Total findings: {total}  |  {errors} errors  |  {warnings} warnings  |  {infos} info  |  {passes} passed", new_x="LMARGIN", new_y="NEXT")

    # Bar chart of category scores
    pdf.set_y(46)
    pdf.set_font("Helvetica", "B", 13)
    pdf._set_color(WHITE)
    pdf.set_x(15)
    pdf.cell(0, 8, "Category Scores", new_x="LMARGIN", new_y="NEXT")

    bar_x = 60
    bar_max_w = pdf.w - bar_x - 25
    y = 60

    # Sort by weight descending
    sorted_cats = sorted(
        data.categories,
        key=lambda c: CATEGORY_WEIGHTS.get(c.name, 0),
        reverse=True,
    )

    for cat in sorted_cats:
        label = CATEGORY_LABELS.get(cat.name, cat.name)
        weight = CATEGORY_WEIGHTS.get(cat.name, 0)
        color = _score_color(cat.score)

        # Label
        pdf.set_font("Helvetica", "", 9)
        pdf._set_color(LIGHT_TEXT)
        pdf.set_xy(15, y)
        pdf.cell(bar_x - 17, 6, label, align="R")

        # Bar background
        pdf.set_fill_color(80, 90, 110)
        pdf.rect(bar_x, y + 1, bar_max_w, 4, "F")

        # Bar fill
        fill_w = bar_max_w * cat.score / 100
        if fill_w > 0:
            pdf.set_fill_color(*color)
            pdf.rect(bar_x, y + 1, fill_w, 4, "F")

        # Score + weight text
        pdf.set_font("Helvetica", "B", 9)
        pdf._set_color(color)
        pdf.set_xy(bar_x + bar_max_w + 2, y)
        pdf.cell(20, 6, f"{cat.score}")

        pdf.set_font("Helvetica", "", 7)
        pdf._set_color(GREY)
        pdf.set_xy(bar_x + bar_max_w + 12, y + 0.5)
        pdf.cell(12, 5, f"{int(weight * 100)}%")

        y += 10

        if y > pdf.h - 25:
            pdf.add_page()
            pdf.set_fill_color(*DARK_BG)
            pdf.rect(0, 0, pdf.w, pdf.h, "F")
            y = 20


# -------------------------------------------------------------------

def _render_category_detail(pdf: SEOReportPDF, cat: CategoryResult) -> None:
    label = CATEGORY_LABELS.get(cat.name, cat.name)
    weight = CATEGORY_WEIGHTS.get(cat.name, 0)
    color = _score_color(cat.score)
    desc = CATEGORY_DESCRIPTIONS.get(cat.name, "")

    # Check if we need a new page (need at least 60mm)
    if pdf.get_y() > pdf.h - 60:
        pdf.add_page()
        pdf.set_fill_color(*DARK_BG)
        pdf.rect(0, 0, pdf.w, pdf.h, "F")
        pdf.set_y(15)

    y = pdf.get_y()

    # Category header background
    pdf.set_fill_color(*DARK_CARD)
    pdf.rect(15, y, pdf.w - 30, 18, "F")

    # Category name
    pdf.set_font("Helvetica", "B", 12)
    pdf._set_color(WHITE)
    pdf.set_xy(19, y + 2)
    pdf.cell(80, 7, label)

    # Score
    pdf.set_font("Helvetica", "B", 14)
    pdf._set_color(color)
    pdf.set_xy(pdf.w - 60, y + 1)
    pdf.cell(15, 8, str(cat.score), align="R")

    # Weight
    pdf.set_font("Helvetica", "", 8)
    pdf._set_color(GREY)
    pdf.set_xy(pdf.w - 42, y + 3)
    pdf.cell(15, 6, f"({int(weight * 100)}% weight)")

    # Progress bar
    bar_y = y + 12
    bar_w = pdf.w - 34
    pdf.set_fill_color(80, 90, 110)
    pdf.rect(17, bar_y, bar_w, 3, "F")
    fill_w = bar_w * cat.score / 100
    if fill_w > 0:
        pdf.set_fill_color(*color)
        pdf.rect(17, bar_y, fill_w, 3, "F")

    pdf.set_y(y + 20)

    # Description
    if desc:
        pdf.set_font("Helvetica", "I", 8)
        pdf._set_color(GREY)
        pdf.set_x(17)
        pdf.cell(0, 5, desc, new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(pdf.get_y() + 2)

    # Issues table
    if not cat.issues:
        pdf.set_font("Helvetica", "I", 9)
        pdf._set_color(GREEN)
        pdf.set_x(17)
        pdf.cell(0, 6, "No issues found.", new_x="LMARGIN", new_y="NEXT")
    else:
        for issue in cat.issues:
            iy = pdf.get_y()
            if iy > pdf.h - 20:
                pdf.add_page()
                pdf.set_fill_color(*DARK_BG)
                pdf.rect(0, 0, pdf.w, pdf.h, "F")
                pdf.set_y(15)
                iy = 15

            # Badge
            badge_w = pdf._severity_badge(17, iy + 0.5, issue.severity)

            # Message text (wrapped)
            pdf.set_font("Helvetica", "", 8)
            pdf._set_color(LIGHT_TEXT)
            text_x = 17 + badge_w + 3
            text_w = pdf.w - text_x - 17
            pdf.set_xy(text_x, iy)
            pdf.multi_cell(text_w, 4.5, issue.message)
            # Ensure minimum row height
            if pdf.get_y() < iy + 6:
                pdf.set_y(iy + 6)
            pdf.set_y(pdf.get_y() + 1)

    pdf.set_y(pdf.get_y() + 6)


# -------------------------------------------------------------------

def _render_recommendations(pdf: SEOReportPDF, data: AuditResponse) -> None:
    pdf.add_page()
    pdf.set_fill_color(*DARK_BG)
    pdf.rect(0, 0, pdf.w, pdf.h, "F")

    pdf.set_font("Helvetica", "B", 20)
    pdf._set_color(WHITE)
    pdf.set_xy(15, 15)
    pdf.cell(0, 10, "Top Priority Fixes", new_x="LMARGIN", new_y="NEXT")

    pdf.set_draw_color(*GREY)
    pdf.set_line_width(0.3)
    pdf.line(15, 28, pdf.w - 15, 28)
    pdf.set_y(33)

    # Sort categories by weight desc
    sorted_cats = sorted(
        data.categories,
        key=lambda c: CATEGORY_WEIGHTS.get(c.name, 0),
        reverse=True,
    )

    # Errors first
    has_errors = False
    for cat in sorted_cats:
        errors = [i for i in cat.issues if i.severity == "error"]
        if not errors:
            continue
        has_errors = True
        label = CATEGORY_LABELS.get(cat.name, cat.name)

        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.set_fill_color(*DARK_BG)
            pdf.rect(0, 0, pdf.w, pdf.h, "F")
            pdf.set_y(15)

        pdf.set_font("Helvetica", "B", 10)
        pdf._set_color(RED)
        pdf.set_x(15)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")

        for issue in errors:
            if pdf.get_y() > pdf.h - 15:
                pdf.add_page()
                pdf.set_fill_color(*DARK_BG)
                pdf.rect(0, 0, pdf.w, pdf.h, "F")
                pdf.set_y(15)

            pdf.set_font("Helvetica", "", 8)
            pdf._set_color(LIGHT_TEXT)
            pdf.set_x(20)
            pdf.multi_cell(pdf.w - 40, 4.5, f"- {issue.message}")

        pdf.set_y(pdf.get_y() + 3)

    if not has_errors:
        pdf.set_font("Helvetica", "", 10)
        pdf._set_color(GREEN)
        pdf.set_x(15)
        pdf.cell(0, 6, "No critical errors found.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_y(pdf.get_y() + 4)

    # Warnings
    pdf.set_y(pdf.get_y() + 4)
    if pdf.get_y() > pdf.h - 30:
        pdf.add_page()
        pdf.set_fill_color(*DARK_BG)
        pdf.rect(0, 0, pdf.w, pdf.h, "F")
        pdf.set_y(15)

    pdf.set_font("Helvetica", "B", 13)
    pdf._set_color(YELLOW)
    pdf.set_x(15)
    pdf.cell(0, 8, "Warnings", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(pdf.get_y() + 2)

    has_warnings = False
    for cat in sorted_cats:
        warnings = [i for i in cat.issues if i.severity == "warning"]
        if not warnings:
            continue
        has_warnings = True
        label = CATEGORY_LABELS.get(cat.name, cat.name)

        if pdf.get_y() > pdf.h - 25:
            pdf.add_page()
            pdf.set_fill_color(*DARK_BG)
            pdf.rect(0, 0, pdf.w, pdf.h, "F")
            pdf.set_y(15)

        pdf.set_font("Helvetica", "B", 10)
        pdf._set_color(YELLOW)
        pdf.set_x(15)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")

        for issue in warnings:
            if pdf.get_y() > pdf.h - 15:
                pdf.add_page()
                pdf.set_fill_color(*DARK_BG)
                pdf.rect(0, 0, pdf.w, pdf.h, "F")
                pdf.set_y(15)

            pdf.set_font("Helvetica", "", 8)
            pdf._set_color(LIGHT_TEXT)
            pdf.set_x(20)
            pdf.multi_cell(pdf.w - 40, 4.5, f"- {issue.message}")

        pdf.set_y(pdf.get_y() + 3)

    if not has_warnings:
        pdf.set_font("Helvetica", "", 10)
        pdf._set_color(GREEN)
        pdf.set_x(15)
        pdf.cell(0, 6, "No warnings found.", new_x="LMARGIN", new_y="NEXT")


# ===================================================================
# Public API
# ===================================================================

def generate_pdf(data: AuditResponse) -> bytes:
    """Generate a professional PDF report and return raw bytes."""
    pdf = SEOReportPDF()

    _render_cover(pdf, data)
    _render_summary(pdf, data)

    # Category detail pages
    pdf.add_page()
    pdf.set_fill_color(*DARK_BG)
    pdf.rect(0, 0, pdf.w, pdf.h, "F")

    pdf.set_font("Helvetica", "B", 20)
    pdf._set_color(WHITE)
    pdf.set_xy(15, 15)
    pdf.cell(0, 10, "Category Details", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*GREY)
    pdf.set_line_width(0.3)
    pdf.line(15, 28, pdf.w - 15, 28)
    pdf.set_y(33)

    # Sort by weight descending
    sorted_cats = sorted(
        data.categories,
        key=lambda c: CATEGORY_WEIGHTS.get(c.name, 0),
        reverse=True,
    )
    for cat in sorted_cats:
        _render_category_detail(pdf, cat)

    _render_recommendations(pdf, data)

    return pdf.output()

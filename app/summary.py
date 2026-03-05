"""Executive summary + quick wins generator.

Converts category issues into sales-friendly summaries with prioritized
quick wins and narrative sections.
"""

from __future__ import annotations

from typing import Any, Optional

from app.config import CATEGORY_WEIGHTS

# Business relevance ranking (higher = more important for sales narrative)
_BUSINESS_RELEVANCE = {
    "meta_tags": 9,
    "performance": 9,
    "tracking": 8,
    "accessibility": 8,
    "mobile": 7,
    "structured_data": 7,
    "serp_features": 7,
    "images": 6,
    "links": 6,
    "ads_quality": 6,
    "headings": 5,
    "sitemap": 5,
    "semantic": 4,
    "robots": 4,
}

CATEGORY_FRIENDLY = {
    "meta_tags": "Meta Tags & SEO Titles",
    "headings": "Heading Structure",
    "images": "Image Optimization",
    "links": "Link Health",
    "performance": "Page Performance",
    "mobile": "Mobile Experience",
    "structured_data": "Structured Data",
    "sitemap": "Sitemap",
    "robots": "Robots & Crawlability",
    "tracking": "Analytics & Tracking",
    "semantic": "Semantic HTML",
    "ads_quality": "Ads Landing Quality",
    "serp_features": "SERP Features",
    "accessibility": "Accessibility",
}

_SEVERITY_RANK = {"error": 3, "warning": 2, "info": 1, "pass": 0}
_IMPACT_RANK = {"high": 3, "medium": 2, "low": 1}

# Quick-win action templates keyed by category
_QUICK_WIN_TEMPLATES = {
    "meta_tags": {
        "why": "Search engines use titles and descriptions to rank and display your pages.",
        "effort": "Low",
    },
    "headings": {
        "why": "Clear heading hierarchy helps search engines understand page structure.",
        "effort": "Low",
    },
    "images": {
        "why": "Missing alt text hurts accessibility and image search rankings.",
        "effort": "Low-Medium",
    },
    "links": {
        "why": "Broken or poorly structured links waste crawl budget and frustrate users.",
        "effort": "Medium",
    },
    "performance": {
        "why": "Page speed directly affects rankings, bounce rate, and conversions.",
        "effort": "Medium-High",
    },
    "mobile": {
        "why": "Google uses mobile-first indexing; poor mobile UX hurts all rankings.",
        "effort": "Medium",
    },
    "structured_data": {
        "why": "Rich snippets can increase CTR by 20-30% in search results.",
        "effort": "Medium",
    },
    "sitemap": {
        "why": "A correct sitemap ensures all important pages get discovered and indexed.",
        "effort": "Low",
    },
    "robots": {
        "why": "Incorrect robots.txt rules can block search engines from indexing key pages.",
        "effort": "Low",
    },
    "tracking": {
        "why": "Without proper analytics, you can't measure ROI or optimize campaigns.",
        "effort": "Low",
    },
    "semantic": {
        "why": "Semantic markup helps search engines understand content meaning and context.",
        "effort": "Low-Medium",
    },
    "ads_quality": {
        "why": "Google Ads Quality Score impacts ad costs and landing page rankings.",
        "effort": "Medium",
    },
    "serp_features": {
        "why": "SERP features like FAQs and sitelinks dramatically increase visibility.",
        "effort": "Medium",
    },
    "accessibility": {
        "why": "WCAG compliance is a legal requirement in many jurisdictions and expands reach.",
        "effort": "Medium-High",
    },
}


def _priority_score(issue: dict, category_name: str) -> float:
    """Higher = higher priority."""
    sev = _SEVERITY_RANK.get(issue.get("severity", "info"), 1)
    imp = _IMPACT_RANK.get(issue.get("impact", "low"), 1)
    biz = _BUSINESS_RELEVANCE.get(category_name, 3)
    return sev * 4 + imp * 2 + biz * 0.5


def generate_executive_summary(
    categories: list[dict],
    brand_name: Optional[str] = None,
    brand_description: Optional[str] = None,
    overall_score: int = 0,
) -> dict[str, Any]:
    """Generate sales-friendly executive summary from category results.

    Args:
        categories: list of CategoryResult dicts (name, score, issues, metrics)
        brand_name: optional brand name for one-liner
        brand_description: optional brand description
        overall_score: overall audit score

    Returns:
        summary_json with brand_one_liner, top_opportunities,
        per_category_quick_wins, and sales_narrative sections.
    """
    # Flatten all issues with their category context
    all_issues: list[tuple[dict, str, int]] = []  # (issue, cat_name, cat_score)
    for cat in categories:
        cat_name = cat.get("name", "")
        cat_score = cat.get("score", 0)
        for issue in cat.get("issues", []):
            if isinstance(issue, dict):
                all_issues.append((issue, cat_name, cat_score))

    # Sort by priority
    all_issues.sort(key=lambda x: _priority_score(x[0], x[1]), reverse=True)

    # --- Brand one-liner ---
    if brand_description:
        brand_one_liner = brand_description[:200]
    elif brand_name:
        brand_one_liner = f"{brand_name} — SEO audit and growth analysis."
    else:
        brand_one_liner = "Comprehensive SEO audit and growth analysis."

    # --- Top opportunities (5-8 bullets) ---
    top_opportunities = []
    seen_messages = set()
    for issue, cat_name, cat_score in all_issues:
        if issue.get("severity") == "pass":
            continue
        msg = issue.get("message", "")
        if msg in seen_messages:
            continue
        seen_messages.add(msg)

        friendly_cat = CATEGORY_FRIENDLY.get(cat_name, cat_name)
        rec = issue.get("recommendation") or ""
        impact = issue.get("impact") or "medium"

        top_opportunities.append({
            "category": friendly_cat,
            "issue": msg[:200],
            "recommendation": rec[:300] if rec else f"Address this {issue.get('severity', 'issue')} in {friendly_cat}.",
            "impact": impact or "medium",
            "severity": issue.get("severity", "info"),
        })
        if len(top_opportunities) >= 8:
            break

    # --- Per-category quick wins ---
    per_category_quick_wins: dict[str, list[dict]] = {}
    for cat in categories:
        cat_name = cat.get("name", "")
        cat_score = cat.get("score", 0)
        issues = cat.get("issues", [])
        template = _QUICK_WIN_TEMPLATES.get(cat_name, {})

        # Get top 3 non-pass issues for this category
        actionable = [
            i for i in issues
            if isinstance(i, dict) and i.get("severity") != "pass"
        ]
        actionable.sort(key=lambda i: _priority_score(i, cat_name), reverse=True)

        wins = []
        for issue in actionable[:3]:
            wins.append({
                "title": issue.get("message", "")[:150],
                "why_it_matters": template.get("why", "Improving this area can help search performance."),
                "action": (issue.get("recommendation") or "Review and fix this issue.")[:200],
                "expected_impact": _expected_impact_phrase(issue, cat_name),
                "effort": template.get("effort", "Medium"),
            })

        if wins:
            per_category_quick_wins[cat_name] = wins

    # --- Sales narrative ---
    sales_narrative = _build_sales_narrative(categories, all_issues, overall_score)

    return {
        "brand_one_liner": brand_one_liner,
        "overall_score": overall_score,
        "top_opportunities": top_opportunities,
        "per_category_quick_wins": per_category_quick_wins,
        "sales_narrative": sales_narrative,
    }


def _expected_impact_phrase(issue: dict, cat_name: str) -> str:
    """Generate a conservative impact phrase."""
    sev = issue.get("severity", "info")
    impact = issue.get("impact", "medium")

    if sev == "error" and impact == "high":
        return "Fixing this can help significantly improve search visibility and user experience."
    elif sev == "error":
        return "Addressing this issue is likely to improve rankings and reduce bounce rate."
    elif sev == "warning" and impact in ("high", "medium"):
        return "This improvement can help enhance performance and search positioning."
    else:
        return "This optimization can contribute to better overall SEO health."


def _build_sales_narrative(
    categories: list[dict],
    all_issues: list[tuple[dict, str, int]],
    overall_score: int,
) -> dict[str, str]:
    """Build the 4-section sales narrative."""

    # Count severity distribution
    error_count = sum(1 for i, _, _ in all_issues if i.get("severity") == "error")
    warning_count = sum(1 for i, _, _ in all_issues if i.get("severity") == "warning")

    # Identify weakest categories
    weak_cats = sorted(categories, key=lambda c: c.get("score", 100))[:3]
    weak_names = [CATEGORY_FRIENDLY.get(c.get("name", ""), c.get("name", "")) for c in weak_cats]

    # --- What's holding growth back ---
    if error_count > 5:
        holding_back = (
            f"The site has {error_count} critical issues and {warning_count} warnings "
            f"that are likely limiting search visibility. The weakest areas are "
            f"{', '.join(weak_names)}. These issues can reduce organic traffic, "
            f"increase bounce rates, and hurt ad campaign effectiveness."
        )
    elif error_count > 0:
        holding_back = (
            f"There are {error_count} critical issues to address, primarily in "
            f"{', '.join(weak_names[:2])}. While the site has a solid foundation, "
            f"these gaps are likely preventing it from reaching its full search potential."
        )
    else:
        holding_back = (
            f"The site is in relatively good shape with no critical errors, but "
            f"{warning_count} warnings in areas like {', '.join(weak_names[:2])} "
            f"represent missed opportunities for growth."
        )

    # --- 30-day fixes ---
    immediate_fixes = []
    for issue, cat_name, _ in all_issues[:5]:
        if issue.get("severity") in ("error", "warning"):
            friendly = CATEGORY_FRIENDLY.get(cat_name, cat_name)
            immediate_fixes.append(f"  - {friendly}: {issue.get('message', '')[:100]}")

    fix_30_days = "Within the first 30 days, we recommend addressing these high-impact items:\n"
    fix_30_days += "\n".join(immediate_fixes[:5]) if immediate_fixes else "  - Continue monitoring and optimizing current performance."

    # --- Next quarter ---
    fix_next_quarter = (
        "Over the following quarter, focus on:\n"
        "  - Comprehensive content optimization and keyword targeting\n"
        "  - Technical improvements in "
        + (weak_names[0] if weak_names else "performance")
        + " and "
        + (weak_names[1] if len(weak_names) > 1 else "user experience")
        + "\n"
        "  - Building structured data and SERP feature eligibility\n"
        "  - Ongoing accessibility compliance improvements"
    )

    # --- Expected outcomes ---
    if overall_score < 50:
        outcomes = (
            "By addressing the identified issues, the site can likely see:\n"
            "  - Improved search engine rankings for target keywords\n"
            "  - Reduced page load times, which can help lower bounce rates\n"
            "  - Better mobile experience for the majority of users\n"
            "  - Increased crawl efficiency and indexation coverage\n"
            "Note: Results vary based on competition, content quality, and market conditions."
        )
    elif overall_score < 80:
        outcomes = (
            "Fixing the identified issues can help achieve:\n"
            "  - Higher click-through rates from improved SERP presentation\n"
            "  - Better conversion rates from faster, more accessible pages\n"
            "  - Expanded organic visibility in target markets\n"
            "  - Stronger foundation for paid campaign landing pages\n"
            "Note: Actual results depend on competitive landscape and implementation quality."
        )
    else:
        outcomes = (
            "The site has strong fundamentals. Continued optimization can help:\n"
            "  - Maintain and defend current rankings against competitors\n"
            "  - Capture additional SERP features and rich snippets\n"
            "  - Improve conversion rates through micro-optimizations\n"
            "  - Stay ahead of algorithm updates with proactive compliance\n"
            "Note: Focus on competitive differentiation and content strategy."
        )

    return {
        "whats_holding_growth_back": holding_back,
        "fix_in_30_days": fix_30_days,
        "fix_next_quarter": fix_next_quarter,
        "expected_outcomes": outcomes,
    }

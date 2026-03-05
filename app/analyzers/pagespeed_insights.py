"""PageSpeed Insights analyzer — runs mobile + desktop audits in parallel."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.models import Issue, PageSpeedResult, PageSpeedStrategy
from app.providers.pagespeed import psi_provider


def _extract_strategy(raw: dict) -> PageSpeedStrategy:
    """Extract metrics from raw PSI API response for one strategy."""
    lhr = raw.get("lighthouseResult", {})
    categories = lhr.get("categories", {})
    perf = categories.get("performance", {})
    score = int((perf.get("score") or 0) * 100)

    audits = lhr.get("audits", {})

    def _metric_ms(audit_id: str) -> Optional[float]:
        audit = audits.get(audit_id, {})
        val = audit.get("numericValue")
        return round(val, 1) if val is not None else None

    def _metric_raw(audit_id: str) -> Optional[float]:
        audit = audits.get(audit_id, {})
        val = audit.get("numericValue")
        return round(val, 4) if val is not None else None

    # Opportunities
    opportunities = []
    for key, audit in audits.items():
        details = audit.get("details", {})
        if details.get("type") == "opportunity" and audit.get("score") is not None and audit["score"] < 1:
            savings = details.get("overallSavingsMs")
            opportunities.append({
                "id": key,
                "title": audit.get("title", key),
                "savings_ms": round(savings, 0) if savings else None,
                "description": audit.get("description", "")[:200],
            })
    opportunities.sort(key=lambda x: -(x.get("savings_ms") or 0))

    # Diagnostics
    diagnostics = []
    for key, audit in audits.items():
        details = audit.get("details", {})
        if details.get("type") == "table" and audit.get("score") is not None and audit["score"] < 1:
            if key not in {o["id"] for o in opportunities}:
                diagnostics.append({
                    "id": key,
                    "title": audit.get("title", key),
                    "description": audit.get("description", "")[:200],
                })

    return PageSpeedStrategy(
        score=score,
        fcp_ms=_metric_ms("first-contentful-paint"),
        lcp_ms=_metric_ms("largest-contentful-paint"),
        cls=_metric_raw("cumulative-layout-shift"),
        tbt_ms=_metric_ms("total-blocking-time"),
        si_ms=_metric_ms("speed-index"),
        opportunities=opportunities[:10],
        diagnostics=diagnostics[:10],
    )


def _generate_issues(mobile: Optional[PageSpeedStrategy], desktop: Optional[PageSpeedStrategy]) -> list[Issue]:
    """Generate issues from PSI results."""
    issues: list[Issue] = []

    for label, strategy in [("Mobile", mobile), ("Desktop", desktop)]:
        if strategy is None:
            continue

        if strategy.score >= 90:
            issues.append(Issue(severity="pass", message=f"{label} performance score: {strategy.score}/100"))
        elif strategy.score >= 50:
            issues.append(Issue(
                severity="warning",
                message=f"{label} performance score: {strategy.score}/100",
                impact="medium",
                recommendation=f"Improve {label.lower()} performance. Target 90+ score.",
            ))
        else:
            issues.append(Issue(
                severity="error",
                message=f"{label} performance score: {strategy.score}/100",
                impact="high",
                recommendation=f"Critical: {label.lower()} performance needs immediate attention.",
            ))

        # LCP
        if strategy.lcp_ms is not None:
            if strategy.lcp_ms > 4000:
                issues.append(Issue(
                    severity="error",
                    message=f"{label} LCP: {strategy.lcp_ms:.0f}ms (poor, >4s)",
                    impact="high",
                    recommendation="Optimize largest contentful paint. Target < 2.5s.",
                ))
            elif strategy.lcp_ms > 2500:
                issues.append(Issue(
                    severity="warning",
                    message=f"{label} LCP: {strategy.lcp_ms:.0f}ms (needs improvement)",
                    impact="medium",
                    recommendation="LCP should be under 2.5s for good user experience.",
                ))

        # CLS
        if strategy.cls is not None and strategy.cls > 0.25:
            issues.append(Issue(
                severity="error",
                message=f"{label} CLS: {strategy.cls:.3f} (poor, >0.25)",
                impact="high",
                recommendation="Fix layout shifts. Add dimensions to images/embeds.",
            ))
        elif strategy.cls is not None and strategy.cls > 0.1:
            issues.append(Issue(
                severity="warning",
                message=f"{label} CLS: {strategy.cls:.3f} (needs improvement)",
                impact="medium",
                recommendation="CLS should be under 0.1 for good experience.",
            ))

        # TBT
        if strategy.tbt_ms is not None and strategy.tbt_ms > 600:
            issues.append(Issue(
                severity="error",
                message=f"{label} TBT: {strategy.tbt_ms:.0f}ms (poor, >600ms)",
                impact="high",
                recommendation="Reduce JavaScript execution time and main thread blocking.",
            ))

        # Top opportunities
        for opp in strategy.opportunities[:3]:
            savings = opp.get("savings_ms")
            if savings and savings > 100:
                issues.append(Issue(
                    severity="info",
                    message=f"{label}: {opp['title']} — save ~{savings:.0f}ms",
                    impact="medium" if savings > 500 else "low",
                    recommendation=opp.get("description", "")[:200],
                ))

    return issues


def analyze_pagespeed(url: str) -> PageSpeedResult:
    """Run PageSpeed Insights for mobile + desktop. Returns PageSpeedResult."""
    start = time.perf_counter()

    if not psi_provider.api_key:
        # PSI API works without a key but with lower rate limits
        pass

    mobile_result: Optional[PageSpeedStrategy] = None
    desktop_result: Optional[PageSpeedStrategy] = None
    cached = False
    errors = []

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(psi_provider.run_audit, url, "mobile"): "mobile",
                executor.submit(psi_provider.run_audit, url, "desktop"): "desktop",
            }
            for future in as_completed(futures, timeout=60):
                strategy_name = futures[future]
                try:
                    raw = future.result()
                    strategy = _extract_strategy(raw)
                    if raw.get("_cached"):
                        cached = True
                    if strategy_name == "mobile":
                        mobile_result = strategy
                    else:
                        desktop_result = strategy
                except Exception as exc:
                    errors.append(f"{strategy_name}: {str(exc)[:100]}")

    except Exception as exc:
        errors.append(str(exc)[:100])

    elapsed = int((time.perf_counter() - start) * 1000)

    if mobile_result is None and desktop_result is None:
        return PageSpeedResult(
            status="error",
            error_message="; ".join(errors) if errors else "PSI audit failed",
            duration_ms=elapsed,
            data_source="google_pagespeed_insights",
        )

    issues = _generate_issues(mobile_result, desktop_result)

    metrics = {}
    if mobile_result:
        metrics["mobile_score"] = mobile_result.score
        metrics["mobile_lcp_ms"] = mobile_result.lcp_ms
        metrics["mobile_cls"] = mobile_result.cls
        metrics["mobile_tbt_ms"] = mobile_result.tbt_ms
    if desktop_result:
        metrics["desktop_score"] = desktop_result.score
        metrics["desktop_lcp_ms"] = desktop_result.lcp_ms
        metrics["desktop_cls"] = desktop_result.cls
        metrics["desktop_tbt_ms"] = desktop_result.tbt_ms

    return PageSpeedResult(
        status="ok",
        data_source="google_pagespeed_insights",
        duration_ms=elapsed,
        cached=cached,
        mobile=mobile_result,
        desktop=desktop_result,
        issues=issues,
        metrics=metrics,
    )

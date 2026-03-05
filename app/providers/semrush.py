from __future__ import annotations

import csv
import io
from typing import Any

from app.providers.base import BaseProvider, ProviderError


class SemrushProvider(BaseProvider):
    """Client for the SEMrush API.

    Docs: https://developer.semrush.com/api/
    Requires SEMRUSH_API_KEY environment variable.

    SEMrush API returns semicolon-separated CSV by default.
    """

    BASE_URL = "https://api.semrush.com"

    def _api_params(self, report_type: str, domain: str, **extra) -> dict[str, str]:
        params = {
            "type": report_type,
            "key": self.api_key,
            "domain": domain,
            "database": "us",
            "export_columns": "",
        }
        params.update(extra)
        return params

    def _parse_csv(self, text: str, delimiter: str = ";") -> list[dict[str, str]]:
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return list(reader)

    def _get_report(self, report_type: str, domain: str, columns: str, **extra) -> list[dict[str, str]]:
        params = self._api_params(report_type, domain, **extra)
        params["export_columns"] = columns
        resp = self._get(self.BASE_URL, params=params)
        text = resp.text.strip()
        if text.startswith("ERROR"):
            raise ProviderError(f"SEMrush error: {text[:200]}")
        return self._parse_csv(text)

    def fetch_domain_data(self, domain: str) -> dict[str, Any]:
        """Fetch organic keywords, backlink overview, and competitors."""
        data: dict[str, Any] = {}
        errors: list[str] = []

        # --- Domain overview (organic) ---
        try:
            rows = self._get_report(
                "domain_ranks", domain,
                columns="Ot,Or,Oc,Ad,At",
                display_limit="1",
            )
            data["domain_overview"] = rows[0] if rows else {}
        except ProviderError as e:
            errors.append(f"domain_overview: {e}")
            data["domain_overview"] = {}

        # --- Top organic keywords ---
        try:
            data["organic_keywords"] = self._get_report(
                "domain_organic", domain,
                columns="Ph,Po,Ur,Nq,Td",
                display_limit="20",
                display_sort="nq_desc",
            )
        except ProviderError as e:
            errors.append(f"organic_keywords: {e}")
            data["organic_keywords"] = []

        # --- Backlinks overview ---
        try:
            data["backlinks_overview"] = self._get_report(
                "backlinks_overview", domain,
                columns="total,domains_num,urls_num,follows_num,nofollows_num",
                display_limit="1",
            )
        except ProviderError as e:
            errors.append(f"backlinks_overview: {e}")
            data["backlinks_overview"] = []

        # --- Top backlinks ---
        try:
            data["top_backlinks"] = self._get_report(
                "backlinks", domain,
                columns="source_url,target_url,anchor",
                display_limit="10",
                display_sort="source_size_desc",
            )
        except ProviderError as e:
            errors.append(f"top_backlinks: {e}")
            data["top_backlinks"] = []

        # --- Organic competitors ---
        try:
            data["organic_competitors"] = self._get_report(
                "domain_organic_organic", domain,
                columns="Dn,Cr",
                display_limit="10",
                display_sort="cr_desc",
            )
        except ProviderError as e:
            errors.append(f"organic_competitors: {e}")
            data["organic_competitors"] = []

        data["_errors"] = errors
        return data


def map_semrush_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Map raw SEMrush API response to our internal schema dict."""
    result: dict[str, Any] = {}

    # --- Organic traffic estimate ---
    overview = raw.get("domain_overview", {})
    if overview:
        ot = overview.get("Ot") or overview.get("Or")
        if ot is not None:
            try:
                val = float(ot)
                result["estimated_organic_traffic"] = {
                    "value": val,
                    "display": _format_number(val),
                }
            except (TypeError, ValueError):
                pass

    # --- Organic keywords ---
    kw_rows = raw.get("organic_keywords", [])
    keywords = []
    buckets = {"1-3": 0, "4-10": 0, "11-20": 0, "21-100": 0}
    for row in kw_rows:
        pos_str = row.get("Po", "")
        vol_str = row.get("Nq", "")
        try:
            pos = int(pos_str)
        except (ValueError, TypeError):
            pos = None
        try:
            vol = int(vol_str)
        except (ValueError, TypeError):
            vol = None
        keywords.append({
            "keyword": row.get("Ph", ""),
            "position": pos,
            "url": row.get("Ur", ""),
            "volume": vol,
        })
        if pos is not None:
            if pos <= 3:
                buckets["1-3"] += 1
            elif pos <= 10:
                buckets["4-10"] += 1
            elif pos <= 20:
                buckets["11-20"] += 1
            elif pos <= 100:
                buckets["21-100"] += 1

    if keywords:
        result["organic_keywords"] = keywords
    result["keyword_distribution"] = [
        {"range": r, "count": c} for r, c in buckets.items()
    ]

    # --- Backlink summary ---
    bl_overview = raw.get("backlinks_overview", [])
    if bl_overview:
        bl = bl_overview[0] if isinstance(bl_overview, list) and bl_overview else bl_overview
        if isinstance(bl, dict):
            def _int(key):
                try:
                    return int(bl.get(key, 0))
                except (ValueError, TypeError):
                    return None
            result["backlink_summary"] = {
                "total_backlinks": _int("total"),
                "referring_domains": _int("domains_num"),
                "follow_count": _int("follows_num"),
                "nofollow_count": _int("nofollows_num"),
            }

    # --- Top backlinks ---
    top_bl = raw.get("top_backlinks", [])
    if top_bl:
        result["top_backlinks"] = [
            {
                "source_url": r.get("source_url", ""),
                "target_url": r.get("target_url"),
                "anchor": r.get("anchor"),
            }
            for r in top_bl[:10]
        ]

    # --- Top referring domains ---
    if bl_overview:
        bl_data = bl_overview[0] if isinstance(bl_overview, list) and bl_overview else bl_overview
        # Referring domains from backlinks_overview don't include per-domain list;
        # we derive from top_backlinks
        seen_domains: dict[str, int] = {}
        for bl_row in top_bl:
            src = bl_row.get("source_url", "")
            if "://" in src:
                from urllib.parse import urlparse
                d = urlparse(src).hostname or src
            else:
                d = src
            seen_domains[d] = seen_domains.get(d, 0) + 1
        if seen_domains:
            result["top_referring_domains"] = [
                {"domain": d, "share": None}
                for d, _ in sorted(seen_domains.items(), key=lambda x: -x[1])[:10]
            ]

    # --- Organic competitors ---
    comp = raw.get("organic_competitors", [])
    if comp:
        result["organic_competitors"] = [
            {
                "domain": r.get("Dn", ""),
                "affinity": float(r["Cr"]) if r.get("Cr") else None,
            }
            for r in comp[:10]
        ]

    return result


def _format_number(n) -> str:
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:.0f}"

from __future__ import annotations

from typing import Any

from app.providers.base import BaseProvider, ProviderError


class SimilarwebProvider(BaseProvider):
    """Client for the Similarweb Digital Data API.

    Docs: https://developers.similarweb.com/docs
    Requires SIMILARWEB_API_KEY environment variable.
    """

    BASE_URL = "https://api.similarweb.com/v1/website"

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    def _api_params(self) -> dict[str, str]:
        return {"api_key": self.api_key, "main_domain_only": "false"}

    def _get_endpoint(self, domain: str, path: str) -> Any:
        url = f"{self.BASE_URL}/{domain}/{path}"
        resp = self._get(url, params=self._api_params())
        try:
            return resp.json()
        except ValueError:
            raise ProviderError("Invalid JSON from Similarweb API")

    def fetch_domain_data(self, domain: str) -> dict[str, Any]:
        """Fetch traffic, engagement, channels, geo, and similar sites."""
        data: dict[str, Any] = {}
        errors: list[str] = []

        # Each endpoint is fetched independently — partial failures are OK
        endpoints = {
            "total_visits": f"total-traffic-and-engagement/visits",
            "engagement": f"total-traffic-and-engagement/average-visit-duration",
            "pages_per_visit": f"total-traffic-and-engagement/pages-per-visit",
            "bounce_rate": f"total-traffic-and-engagement/bounce-rate",
            "traffic_sources": f"traffic-sources/overview",
            "geo": f"geo/traffic-by-country",
            "referrals": f"traffic-sources/referrals",
            "outgoing": f"traffic-sources/outgoing-referrals",
            "similar_sites": f"similar-sites/similarsites",
        }

        for key, path in endpoints.items():
            try:
                data[key] = self._get_endpoint(domain, path)
            except ProviderError as e:
                errors.append(f"{key}: {e}")
                data[key] = None

        data["_errors"] = errors
        return data


def map_similarweb_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Map raw Similarweb API response to our internal schema dict.

    Returns a dict suitable for constructing SimilarwebInsights.
    """
    result: dict[str, Any] = {}

    # --- Visits ---
    visits_data = raw.get("total_visits")
    if isinstance(visits_data, dict) and visits_data.get("visits"):
        # API returns list of monthly values; take most recent
        visits_list = visits_data["visits"]
        if isinstance(visits_list, list) and visits_list:
            last = visits_list[-1] if isinstance(visits_list[-1], dict) else {}
            val = last.get("visits", visits_list[-1] if isinstance(visits_list[-1], (int, float)) else None)
            if val is not None:
                result["estimated_monthly_visits"] = {
                    "value": float(val),
                    "display": _format_number(val),
                }

    # --- Engagement metrics ---
    for key, field in [
        ("engagement", "visit_duration"),
        ("pages_per_visit", "pages_per_visit"),
        ("bounce_rate", "bounce_rate"),
    ]:
        raw_val = raw.get(key)
        if isinstance(raw_val, dict):
            # Try common response shapes
            val = raw_val.get(field) or raw_val.get("value")
            if isinstance(val, list) and val:
                val = val[-1].get(field, val[-1]) if isinstance(val[-1], dict) else val[-1]
            if val is not None:
                display = f"{val:.2f}" if isinstance(val, float) else str(val)
                if key == "bounce_rate" and isinstance(val, (int, float)):
                    display = f"{val * 100:.1f}%"
                elif key == "engagement" and isinstance(val, (int, float)):
                    mins, secs = divmod(int(val), 60)
                    display = f"{mins}m {secs}s"
                result[field] = {"value": float(val) if val else None, "display": display}

    # --- Traffic sources ---
    sources = raw.get("traffic_sources")
    if isinstance(sources, dict):
        channels = []
        channel_map = {
            "Direct": "direct", "Search": "search", "Social": "social",
            "Referrals": "referrals", "Mail": "email", "Display Ads": "display",
        }
        overview = sources.get("overview") or sources
        for api_name, internal_name in channel_map.items():
            val = overview.get(api_name) or overview.get(internal_name) or overview.get(api_name.lower())
            if val is not None:
                channels.append({"channel": internal_name, "share": float(val)})
        if channels:
            result["traffic_channels"] = channels

    # --- Geo ---
    geo = raw.get("geo")
    if isinstance(geo, dict):
        records = geo.get("records") or geo.get("countries") or []
        if isinstance(records, list):
            countries = []
            for rec in records[:10]:
                if isinstance(rec, dict):
                    country = rec.get("country") or rec.get("country_name") or "Unknown"
                    share = rec.get("share") or rec.get("traffic_share") or 0
                    countries.append({"country": str(country), "share": float(share)})
            if countries:
                result["top_countries"] = countries

    # --- Referrals ---
    refs = raw.get("referrals")
    if isinstance(refs, dict):
        records = refs.get("referrals") or refs.get("records") or []
        if isinstance(records, list):
            result["top_referring_sites"] = [
                {"domain": r.get("site") or r.get("domain", ""), "share": r.get("share")}
                for r in records[:10] if isinstance(r, dict)
            ]

    # --- Outgoing ---
    outgoing = raw.get("outgoing")
    if isinstance(outgoing, dict):
        records = outgoing.get("referrals") or outgoing.get("records") or []
        if isinstance(records, list):
            result["top_destination_sites"] = [
                {"domain": r.get("site") or r.get("domain", ""), "share": r.get("share")}
                for r in records[:10] if isinstance(r, dict)
            ]

    # --- Similar sites ---
    similar = raw.get("similar_sites")
    if isinstance(similar, dict):
        sites = similar.get("similar_sites") or similar.get("records") or []
        if isinstance(sites, list):
            result["similar_sites"] = [
                {"domain": s.get("url") or s.get("domain", ""), "affinity": s.get("affinity")}
                for s in sites[:10] if isinstance(s, dict)
            ]

    return result


def _format_number(n) -> str:
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:.0f}"

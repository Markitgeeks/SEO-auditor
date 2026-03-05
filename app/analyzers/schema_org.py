"""Deep Schema.org analyzer using extruct for rich snippet validation."""

from __future__ import annotations

import json

from app.models import CategoryResult, Issue
from app.fetcher import FetchResult

# Rich snippet required properties per schema type
RICH_SNIPPET_REQUIREMENTS: dict[str, list[str]] = {
    "Product": ["name", "image", "offers"],
    "FAQPage": ["mainEntity"],
    "BreadcrumbList": ["itemListElement"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Article": ["headline", "image", "datePublished", "author"],
    "NewsArticle": ["headline", "image", "datePublished", "author"],
    "BlogPosting": ["headline", "image", "datePublished", "author"],
    "Review": ["itemReviewed", "reviewRating", "author"],
    "Recipe": ["name", "image", "recipeIngredient"],
    "VideoObject": ["name", "description", "thumbnailUrl", "uploadDate"],
    "Event": ["name", "startDate", "location"],
    "HowTo": ["name", "step"],
}

SCHEMA_TYPE_LABELS: dict[str, str] = {
    "Product": "Product Rich Snippet",
    "FAQPage": "FAQ Rich Result",
    "BreadcrumbList": "Breadcrumb Trail",
    "LocalBusiness": "Local Business / Map Pack",
    "Article": "Article Rich Result",
    "Review": "Review Snippet",
    "Recipe": "Recipe Rich Result",
    "VideoObject": "Video Rich Result",
    "Event": "Event Rich Result",
    "HowTo": "How-To Rich Result",
}


def _extract_with_extruct(html: str, url: str) -> dict:
    """Use extruct to extract all structured data formats."""
    try:
        import extruct
        return extruct.extract(html, base_url=url, errors="ignore",
                               syntaxes=["json-ld", "microdata", "rdfa", "opengraph", "dublincore"])
    except ImportError:
        return {}


def _extract_jsonld_fallback(soup) -> list[dict]:
    """Fallback JSON-LD parsing if extruct is unavailable."""
    results = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                results.append(data)
            elif isinstance(data, list):
                results.extend(d for d in data if isinstance(d, dict))
        except (json.JSONDecodeError, TypeError):
            pass
    return results


def _get_schema_type(item: dict) -> str:
    """Extract @type from a JSON-LD item, handling lists."""
    t = item.get("@type", "")
    if isinstance(t, list):
        return t[0] if t else ""
    return t


def _validate_rich_snippets(schema_items: list[dict], issues: list[Issue]) -> int:
    """Validate rich snippet requirements. Returns penalty points."""
    penalty = 0
    validated_types: set[str] = set()

    for item in schema_items:
        schema_type = _get_schema_type(item)
        if not schema_type or schema_type in validated_types:
            continue

        requirements = RICH_SNIPPET_REQUIREMENTS.get(schema_type)
        if not requirements:
            continue

        validated_types.add(schema_type)
        missing = [prop for prop in requirements if prop not in item]

        if missing:
            label = SCHEMA_TYPE_LABELS.get(schema_type, schema_type)
            issues.append(Issue(
                severity="warning",
                message=f"{label}: missing required properties: {', '.join(missing)}",
                impact="medium",
                recommendation=f"Add the missing properties ({', '.join(missing)}) to your {schema_type} schema for rich snippet eligibility.",
                evidence=f"Schema type: {schema_type}, missing: {', '.join(missing)}",
            ))
            penalty += 5 * len(missing)
        else:
            label = SCHEMA_TYPE_LABELS.get(schema_type, schema_type)
            issues.append(Issue(
                severity="pass",
                message=f"{label}: all required properties present"
            ))

    return penalty


def _flatten_graph(items: list[dict]) -> list[dict]:
    """Flatten @graph arrays in JSON-LD."""
    flat = []
    for item in items:
        if "@graph" in item:
            graph = item["@graph"]
            if isinstance(graph, list):
                flat.extend(d for d in graph if isinstance(d, dict))
        else:
            flat.append(item)
    return flat


def analyze_structured_data(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    html = page.response.text

    jsonld_count = 0
    jsonld_types: list[str] = []
    microdata_count = 0
    has_opengraph = False
    rich_snippets_eligible = False

    # Try extruct first, fall back to manual parsing
    extracted = _extract_with_extruct(html, page.url)

    if extracted:
        # --- JSON-LD ---
        jsonld_items = extracted.get("json-ld", [])
        jsonld_count = len(jsonld_items)
        if jsonld_items:
            flat_items = _flatten_graph(jsonld_items)
            jsonld_types = [_get_schema_type(i) for i in flat_items if _get_schema_type(i)]
            issues.append(Issue(
                severity="pass",
                message=f"{jsonld_count} JSON-LD block(s) found -- types: {', '.join(jsonld_types) or 'N/A'}"
            ))
            penalty = _validate_rich_snippets(flat_items, issues)
            score -= penalty
            if penalty == 0 and any(_get_schema_type(i) in RICH_SNIPPET_REQUIREMENTS for i in flat_items):
                rich_snippets_eligible = True
        else:
            issues.append(Issue(severity="warning", message="No JSON-LD structured data found",
                                impact="high", recommendation="Add JSON-LD structured data to improve search result appearance."))
            score -= 25

        # --- Microdata ---
        microdata = extracted.get("microdata", [])
        microdata_count = len(microdata)
        if microdata:
            types = [m.get("type", "unknown") for m in microdata]
            issues.append(Issue(
                severity="pass",
                message=f"{microdata_count} microdata element(s) found -- types: {', '.join(types[:5])}"
            ))
        elif not jsonld_items:
            issues.append(Issue(severity="warning", message="No microdata found either",
                                impact="medium", recommendation="Add either JSON-LD or microdata structured markup."))
            score -= 10

        # --- RDFa ---
        rdfa = extracted.get("rdfa", [])
        if rdfa:
            issues.append(Issue(severity="info", message=f"{len(rdfa)} RDFa element(s) detected"))

        # --- OpenGraph ---
        opengraph = extracted.get("opengraph", [])
        has_opengraph = bool(opengraph)
        if opengraph:
            og_props = []
            for og in opengraph:
                og_props.extend(og.keys())
            issues.append(Issue(severity="pass", message=f"Open Graph tags found ({len(og_props)} properties)"))
        else:
            issues.append(Issue(severity="info", message="No Open Graph meta tags detected"))

        # --- Dublin Core ---
        dublincore = extracted.get("dublincore", [])
        if dublincore:
            issues.append(Issue(severity="info", message=f"Dublin Core metadata found ({len(dublincore)} element(s))"))

        # No structured data at all
        if not jsonld_items and not microdata:
            issues.append(Issue(severity="error", message="No structured data found -- add JSON-LD or microdata",
                                impact="high", recommendation="Implement JSON-LD schema markup to enable rich results in search."))
            score -= 15

    else:
        # Fallback: manual JSON-LD parsing
        jsonld_items = _extract_jsonld_fallback(page.soup)
        jsonld_count = len(jsonld_items)
        if jsonld_items:
            flat_items = _flatten_graph(jsonld_items)
            jsonld_types = [_get_schema_type(i) for i in flat_items if _get_schema_type(i)]
            issues.append(Issue(
                severity="pass",
                message=f"{jsonld_count} JSON-LD block(s) found -- types: {', '.join(jsonld_types) or 'N/A'}"
            ))
            penalty = _validate_rich_snippets(flat_items, issues)
            score -= penalty
            if penalty == 0 and any(_get_schema_type(i) in RICH_SNIPPET_REQUIREMENTS for i in flat_items):
                rich_snippets_eligible = True
        else:
            issues.append(Issue(severity="warning", message="No JSON-LD structured data found",
                                impact="high", recommendation="Add JSON-LD structured data for rich search results."))
            score -= 30

        microdata_elements = page.soup.find_all(attrs={"itemscope": True})
        microdata_count = len(microdata_elements)
        if microdata_elements:
            types = [el.get("itemtype", "unknown") for el in microdata_elements]
            issues.append(Issue(
                severity="pass",
                message=f"{microdata_count} microdata element(s) found -- types: {', '.join(types[:5])}"
            ))
        elif not jsonld_items:
            issues.append(Issue(severity="warning", message="No microdata found either"))
            score -= 15

        rdfa = page.soup.find_all(attrs={"vocab": True}) or page.soup.find_all(attrs={"typeof": True})
        if rdfa:
            issues.append(Issue(severity="info", message=f"{len(rdfa)} RDFa element(s) detected"))

        if not jsonld_items and not microdata_elements:
            issues.append(Issue(severity="error", message="No structured data found -- add JSON-LD or microdata",
                                impact="high", recommendation="Implement JSON-LD schema markup to enable rich results."))

        issues.append(Issue(severity="info", message="Install 'extruct' for deeper structured data analysis"))

    metrics = {
        "jsonld_count": jsonld_count,
        "jsonld_types": jsonld_types,
        "microdata_count": microdata_count,
        "has_opengraph": has_opengraph,
        "rich_snippets_eligible": rich_snippets_eligible,
    }

    return CategoryResult(name="structured_data", score=max(0, min(100, score)), issues=issues, metrics=metrics)

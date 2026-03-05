"""Deep schema markup validation against schema.org definitions.

Extracts JSON-LD, microdata, and RDFa entities from a page and validates
each entity's @type and properties against the schema.org type system.
"""

from __future__ import annotations

import json
import re
import time
from typing import Optional

from app.fetcher import FetchResult
from app.models import Issue, SchemaEntity, SchemaValidationResult
from app.schema_defs import is_valid_type, get_valid_properties


def _extract_jsonld(soup) -> list[tuple[dict, str]]:
    """Extract JSON-LD blocks. Returns list of (data, raw_snippet)."""
    results = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or ""
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                results.append((data, raw[:500]))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        results.append((item, raw[:500]))
        except (json.JSONDecodeError, TypeError):
            results.append(({"_parse_error": True, "_raw": raw[:300]}, raw[:300]))
    return results


def _flatten_graph(items: list[tuple[dict, str]]) -> list[tuple[dict, str]]:
    """Flatten @graph arrays."""
    flat = []
    for data, snippet in items:
        if "@graph" in data and isinstance(data["@graph"], list):
            for item in data["@graph"]:
                if isinstance(item, dict):
                    flat.append((item, snippet))
        else:
            flat.append((data, snippet))
    return flat


def _extract_microdata(soup) -> list[tuple[dict, str]]:
    """Extract microdata entities (itemscope/itemtype/itemprop)."""
    results = []
    for el in soup.find_all(attrs={"itemscope": True}):
        itemtype = el.get("itemtype", "")
        # Extract type name from URL like https://schema.org/Product
        type_name = itemtype.rstrip("/").rsplit("/", 1)[-1] if itemtype else ""
        props = []
        for prop_el in el.find_all(attrs={"itemprop": True}):
            prop_name = prop_el.get("itemprop", "")
            if prop_name:
                props.append(prop_name)
        entity = {
            "@type": type_name,
            "_source": "microdata",
            "_properties": props,
            "_itemtype_url": itemtype,
        }
        snippet = str(el)[:300]
        results.append((entity, snippet))
    return results


def _extract_rdfa(soup) -> list[tuple[dict, str]]:
    """Extract RDFa entities (vocab/typeof/property)."""
    results = []
    for el in soup.find_all(attrs={"typeof": True}):
        vocab = ""
        parent = el
        while parent:
            v = parent.get("vocab", "")
            if v:
                vocab = v
                break
            parent = parent.parent if hasattr(parent, "parent") else None

        type_name = el.get("typeof", "")
        props = []
        for prop_el in el.find_all(attrs={"property": True}):
            prop_name = prop_el.get("property", "")
            if prop_name:
                # Strip prefix like "schema:" if present
                if ":" in prop_name:
                    prop_name = prop_name.split(":", 1)[1]
                props.append(prop_name)
        entity = {
            "@type": type_name,
            "_source": "rdfa",
            "_properties": props,
            "_vocab": vocab,
        }
        snippet = str(el)[:300]
        results.append((entity, snippet))
    return results


def _get_type_name(data: dict) -> str:
    """Extract @type from an entity dict."""
    t = data.get("@type", "")
    if isinstance(t, list):
        return t[0] if t else ""
    return str(t)


def _is_schema_org_context(data: dict) -> bool:
    """Check if @context references schema.org."""
    ctx = data.get("@context", "")
    if isinstance(ctx, str):
        return "schema.org" in ctx
    if isinstance(ctx, list):
        return any("schema.org" in str(c) for c in ctx)
    if isinstance(ctx, dict):
        return "schema.org" in str(ctx.get("@vocab", ""))
    return False


def _validate_entity(
    data: dict,
    snippet: str,
    source: str,
    issues: list[Issue],
) -> SchemaEntity:
    """Validate a single entity. Returns SchemaEntity + appends issues."""
    type_name = _get_type_name(data)
    entity_id = data.get("@id")

    # Determine properties present
    if source == "jsonld":
        props_found = [k for k in data.keys() if not k.startswith("@") and not k.startswith("_")]
    else:
        props_found = data.get("_properties", [])

    entity = SchemaEntity(
        entity_type=type_name or "Unknown",
        entity_id=entity_id,
        source=source,
        properties_found=props_found,
        valid=True,
    )

    # Parse error
    if data.get("_parse_error"):
        issues.append(Issue(
            severity="error",
            message="JSON-LD syntax error: invalid JSON",
            impact="high",
            recommendation="Fix the JSON-LD block to be valid JSON.",
            evidence=snippet[:200],
        ))
        entity.valid = False
        return entity

    # Context validation (JSON-LD only)
    if source == "jsonld" and not _is_schema_org_context(data):
        issues.append(Issue(
            severity="warning",
            message=f"JSON-LD entity missing schema.org @context",
            impact="medium",
            recommendation='Add "@context": "https://schema.org" to your JSON-LD.',
            evidence=snippet[:200],
        ))

    # Type validation
    if not type_name:
        issues.append(Issue(
            severity="error",
            message=f"Entity missing @type",
            impact="high",
            recommendation="Every schema.org entity must declare an @type.",
            evidence=snippet[:200],
        ))
        entity.valid = False
        return entity

    if not is_valid_type(type_name):
        issues.append(Issue(
            severity="error",
            message=f"Unknown schema.org type: {type_name}",
            impact="high",
            recommendation=f"Use a valid schema.org type. Check https://schema.org/{type_name}",
            evidence=snippet[:200],
        ))
        entity.valid = False
        return entity

    # Property validation
    valid_props = get_valid_properties(type_name)
    if valid_props:
        unknown_props = [p for p in props_found if p not in valid_props]
        if unknown_props:
            issues.append(Issue(
                severity="warning",
                message=f"{type_name}: unknown properties: {', '.join(unknown_props[:5])}",
                impact="low",
                recommendation=f"Check property names against https://schema.org/{type_name}",
                evidence=f"Type: {type_name}, unknown: {', '.join(unknown_props[:10])}",
            ))

    # Recommended properties check
    if "name" not in props_found and type_name not in ("ListItem", "HowToStep", "PostalAddress", "GeoCoordinates", "Offer"):
        issues.append(Issue(
            severity="info",
            message=f"{type_name}: missing recommended 'name' property",
            impact="low",
            recommendation=f"Add a 'name' property to your {type_name} entity.",
        ))

    if "description" not in props_found and type_name not in (
        "ListItem", "HowToStep", "PostalAddress", "GeoCoordinates",
        "Offer", "BreadcrumbList", "ItemList", "SearchAction",
        "AggregateRating", "Rating", "ContactPoint",
    ):
        issues.append(Issue(
            severity="info",
            message=f"{type_name}: missing recommended 'description' property",
            impact="low",
            recommendation=f"Add a 'description' property to your {type_name} entity.",
        ))

    return entity


def analyze_schema_validation(page: FetchResult) -> SchemaValidationResult:
    """Run deep schema validation on a fetched page."""
    start = time.perf_counter()
    issues: list[Issue] = []
    entities: list[SchemaEntity] = []

    try:
        # Extract all formats
        jsonld_raw = _extract_jsonld(page.soup)
        jsonld_items = _flatten_graph(jsonld_raw)
        microdata_items = _extract_microdata(page.soup)
        rdfa_items = _extract_rdfa(page.soup)

        syntax_errors = 0
        type_errors = 0
        property_warnings = 0

        # Validate JSON-LD entities
        for data, snippet in jsonld_items:
            entity = _validate_entity(data, snippet, "jsonld", issues)
            entities.append(entity)
            if data.get("_parse_error"):
                syntax_errors += 1
            if not entity.valid:
                type_errors += 1

        # Validate microdata entities
        for data, snippet in microdata_items:
            entity = _validate_entity(data, snippet, "microdata", issues)
            entities.append(entity)
            if not entity.valid:
                type_errors += 1

        # Validate RDFa entities
        for data, snippet in rdfa_items:
            # Check if vocab is schema.org
            vocab = data.get("_vocab", "")
            if vocab and "schema.org" not in vocab:
                issues.append(Issue(
                    severity="info",
                    message=f"RDFa entity uses non-schema.org vocab: {vocab}",
                    impact="low",
                ))
            entity = _validate_entity(data, snippet, "rdfa", issues)
            entities.append(entity)
            if not entity.valid:
                type_errors += 1

        # Count property warnings
        property_warnings = sum(1 for i in issues if i.severity == "warning" and "unknown properties" in i.message)

        total = len(entities)
        valid_count = sum(1 for e in entities if e.valid)
        valid_pct = round(valid_count / total * 100) if total > 0 else 100

        if total == 0:
            issues.append(Issue(
                severity="warning",
                message="No schema markup entities found on this page",
                impact="high",
                recommendation="Add JSON-LD structured data to improve search visibility.",
            ))

        # Summary pass issues
        if total > 0 and type_errors == 0 and syntax_errors == 0:
            issues.append(Issue(
                severity="pass",
                message=f"All {total} schema entities are valid",
            ))

        metrics = {
            "entities_found": total,
            "jsonld_count": len(jsonld_items),
            "microdata_count": len(microdata_items),
            "rdfa_count": len(rdfa_items),
            "syntax_errors": syntax_errors,
            "type_errors": type_errors,
            "property_warnings": property_warnings,
            "valid_entities_pct": valid_pct,
        }

        elapsed = int((time.perf_counter() - start) * 1000)

        return SchemaValidationResult(
            status="ok",
            duration_ms=elapsed,
            entities=entities,
            issues=issues,
            metrics=metrics,
        )

    except Exception as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        return SchemaValidationResult(
            status="error",
            error_message=str(exc)[:200],
            duration_ms=elapsed,
            issues=issues,
            entities=entities,
        )

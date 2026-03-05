"""Schema.org type hierarchy loader.

Provides a mapping of schema.org types to their valid properties (including inherited).
Uses a curated built-in snapshot covering the most common types. If the full
schema.org JSONLD file is available at app/data/schemaorg-current-https.jsonld,
it will be loaded instead.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Optional

# --- Built-in curated type definitions ---
# Maps type name -> set of valid property names (including inherited from Thing)

_THING_PROPS = {
    "name", "description", "url", "image", "identifier", "sameAs",
    "alternateName", "disambiguatingDescription", "mainEntityOfPage",
    "potentialAction", "subjectOf", "additionalType",
}

_BUILTIN_TYPES: dict[str, set[str]] = {
    "Thing": _THING_PROPS,
    "CreativeWork": _THING_PROPS | {
        "author", "datePublished", "dateModified", "headline", "text",
        "publisher", "keywords", "inLanguage", "license", "copyrightYear",
        "copyrightHolder", "isPartOf", "hasPart", "about", "abstract",
        "accessMode", "citation", "comment", "contentLocation",
        "contributor", "creator", "editor", "genre", "thumbnailUrl",
        "video", "audio", "encoding", "associatedMedia",
    },
    "Article": _THING_PROPS | {
        "author", "datePublished", "dateModified", "headline", "image",
        "publisher", "articleBody", "articleSection", "wordCount",
        "backstory", "speakable",
    },
    "NewsArticle": _THING_PROPS | {
        "author", "datePublished", "dateModified", "headline", "image",
        "publisher", "articleBody", "dateline", "printColumn", "printEdition",
    },
    "BlogPosting": _THING_PROPS | {
        "author", "datePublished", "dateModified", "headline", "image",
        "publisher", "articleBody", "wordCount",
    },
    "WebPage": _THING_PROPS | {
        "breadcrumb", "lastReviewed", "mainContentOfPage", "primaryImageOfPage",
        "relatedLink", "significantLink", "speakable", "specialty",
    },
    "WebSite": _THING_PROPS | {
        "issn", "potentialAction",
    },
    "Product": _THING_PROPS | {
        "brand", "offers", "sku", "gtin", "gtin13", "gtin14", "gtin8",
        "mpn", "model", "color", "material", "weight", "width", "height",
        "depth", "aggregateRating", "review", "category", "productID",
        "releaseDate", "manufacturer", "logo",
    },
    "Offer": _THING_PROPS | {
        "price", "priceCurrency", "availability", "itemCondition",
        "validFrom", "validThrough", "seller", "itemOffered",
        "priceValidUntil", "sku",
    },
    "Organization": _THING_PROPS | {
        "address", "telephone", "email", "logo", "foundingDate",
        "founder", "employee", "numberOfEmployees", "contactPoint",
        "areaServed", "brand", "department", "parentOrganization",
        "legalName", "taxID", "vatID",
    },
    "LocalBusiness": _THING_PROPS | {
        "address", "telephone", "email", "logo", "openingHours",
        "openingHoursSpecification", "geo", "priceRange", "currenciesAccepted",
        "paymentAccepted", "areaServed", "hasMap", "aggregateRating",
        "review",
    },
    "Person": _THING_PROPS | {
        "givenName", "familyName", "email", "telephone", "birthDate",
        "gender", "jobTitle", "worksFor", "affiliation", "alumniOf",
        "nationality", "address", "knows",
    },
    "Event": _THING_PROPS | {
        "startDate", "endDate", "location", "organizer", "performer",
        "eventStatus", "eventAttendanceMode", "offers", "doorTime",
        "duration", "inLanguage",
    },
    "FAQPage": _THING_PROPS | {"mainEntity"},
    "Question": _THING_PROPS | {
        "acceptedAnswer", "suggestedAnswer", "answerCount", "text",
    },
    "Answer": _THING_PROPS | {"text", "upvoteCount", "dateCreated"},
    "BreadcrumbList": _THING_PROPS | {"itemListElement", "numberOfItems"},
    "ListItem": _THING_PROPS | {"item", "position", "nextItem", "previousItem"},
    "Review": _THING_PROPS | {
        "itemReviewed", "reviewRating", "author", "reviewBody", "datePublished",
    },
    "AggregateRating": _THING_PROPS | {
        "ratingValue", "bestRating", "worstRating", "ratingCount", "reviewCount",
        "itemReviewed",
    },
    "Rating": _THING_PROPS | {
        "ratingValue", "bestRating", "worstRating", "author",
    },
    "Recipe": _THING_PROPS | {
        "recipeIngredient", "recipeInstructions", "cookTime", "prepTime",
        "totalTime", "recipeYield", "recipeCategory", "recipeCuisine",
        "nutrition", "author", "datePublished", "aggregateRating",
        "video",
    },
    "VideoObject": _THING_PROPS | {
        "thumbnailUrl", "uploadDate", "duration", "contentUrl",
        "embedUrl", "interactionStatistic", "transcript", "width",
        "height", "publisher",
    },
    "ImageObject": _THING_PROPS | {
        "contentUrl", "width", "height", "caption", "thumbnail",
        "representativeOfPage",
    },
    "HowTo": _THING_PROPS | {
        "step", "totalTime", "estimatedCost", "supply", "tool", "yield",
    },
    "HowToStep": _THING_PROPS | {"text", "itemListElement", "position"},
    "SearchAction": _THING_PROPS | {
        "query", "query-input", "target",
    },
    "PostalAddress": _THING_PROPS | {
        "streetAddress", "addressLocality", "addressRegion", "postalCode",
        "addressCountry",
    },
    "GeoCoordinates": _THING_PROPS | {"latitude", "longitude", "elevation"},
    "ContactPoint": _THING_PROPS | {
        "telephone", "contactType", "email", "areaServed", "availableLanguage",
    },
    "ItemList": _THING_PROPS | {"itemListElement", "numberOfItems", "itemListOrder"},
    "SoftwareApplication": _THING_PROPS | {
        "applicationCategory", "operatingSystem", "offers", "aggregateRating",
        "softwareVersion", "downloadUrl",
    },
    "MedicalCondition": _THING_PROPS | {
        "associatedAnatomy", "cause", "differentialDiagnosis", "drug",
        "possibleTreatment", "riskFactor", "signOrSymptom",
    },
    "Course": _THING_PROPS | {
        "provider", "courseCode", "hasCourseInstance", "coursePrerequisites",
    },
    "JobPosting": _THING_PROPS | {
        "datePosted", "validThrough", "hiringOrganization", "jobLocation",
        "title", "baseSalary", "employmentType", "industry",
    },
    "Book": _THING_PROPS | {
        "author", "isbn", "numberOfPages", "bookEdition", "bookFormat",
        "illustrator",
    },
}

# --- Singleton loader ---

_schema_types: Optional[dict[str, set[str]]] = None
_load_lock = threading.Lock()


def _load_from_jsonld(path: str) -> dict[str, set[str]]:
    """Parse the full schema.org JSONLD file into type->properties mapping."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = data.get("@graph", [])

    # Build type hierarchy: type -> parent types
    type_parents: dict[str, list[str]] = {}
    # type -> direct properties
    type_direct_props: dict[str, set[str]] = {}

    for node in graph:
        node_id = node.get("@id", "")
        node_type = node.get("@type", "")

        if not node_id.startswith("schema:") and not node_id.startswith("https://schema.org/"):
            continue

        name = node_id.split("/")[-1].split(":")[-1]

        if node_type == "rdfs:Class" or (isinstance(node_type, list) and "rdfs:Class" in node_type):
            parents = node.get("rdfs:subClassOf", [])
            if isinstance(parents, dict):
                parents = [parents]
            parent_names = []
            for p in parents:
                if isinstance(p, dict):
                    pid = p.get("@id", "")
                    parent_names.append(pid.split("/")[-1].split(":")[-1])
            type_parents[name] = parent_names
            if name not in type_direct_props:
                type_direct_props[name] = set()

        elif node_type == "rdf:Property" or (isinstance(node_type, list) and "rdf:Property" in node_type):
            domain = node.get("schema:domainIncludes", [])
            if isinstance(domain, dict):
                domain = [domain]
            for d in domain:
                if isinstance(d, dict):
                    dtype = d.get("@id", "").split("/")[-1].split(":")[-1]
                    if dtype:
                        type_direct_props.setdefault(dtype, set()).add(name)

    # Resolve inheritance
    result: dict[str, set[str]] = {}

    def resolve(t: str, visited: set) -> set[str]:
        if t in result:
            return result[t]
        if t in visited:
            return set()
        visited.add(t)
        props = set(type_direct_props.get(t, set()))
        for parent in type_parents.get(t, []):
            props |= resolve(parent, visited)
        result[t] = props
        return props

    for t in type_parents:
        resolve(t, set())

    return result


def get_schema_types() -> dict[str, set[str]]:
    """Get schema.org type->properties mapping. Thread-safe singleton."""
    global _schema_types
    if _schema_types is not None:
        return _schema_types

    with _load_lock:
        if _schema_types is not None:
            return _schema_types

        # Try loading full JSONLD file
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data", "schemaorg-current-https.jsonld"
        )
        if os.path.isfile(data_path):
            try:
                _schema_types = _load_from_jsonld(data_path)
                return _schema_types
            except Exception:
                pass

        # Fall back to built-in curated definitions
        _schema_types = _BUILTIN_TYPES
        return _schema_types


def is_valid_type(type_name: str) -> bool:
    """Check if a type name exists in the schema.org definitions."""
    return type_name in get_schema_types()


def get_valid_properties(type_name: str) -> set[str]:
    """Get valid properties for a schema.org type."""
    return get_schema_types().get(type_name, set())

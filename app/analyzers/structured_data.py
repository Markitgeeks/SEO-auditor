import json

from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_structured_data(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup

    # JSON-LD
    jsonld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    schema_types = []
    if jsonld_scripts:
        for script in jsonld_scripts:
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    t = data.get("@type", "unknown")
                    schema_types.append(t)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_types.append(item.get("@type", "unknown"))
            except (json.JSONDecodeError, TypeError):
                issues.append(Issue(severity="warning", message="Invalid JSON-LD block found"))
                score -= 10

        issues.append(Issue(
            severity="pass",
            message=f"{len(jsonld_scripts)} JSON-LD block(s) found — types: {', '.join(schema_types) or 'N/A'}"
        ))
    else:
        issues.append(Issue(severity="warning", message="No JSON-LD structured data found"))
        score -= 30

    # Microdata
    microdata_elements = soup.find_all(attrs={"itemscope": True})
    if microdata_elements:
        types = [el.get("itemtype", "unknown") for el in microdata_elements]
        issues.append(Issue(
            severity="pass",
            message=f"{len(microdata_elements)} microdata element(s) found — types: {', '.join(types[:5])}"
        ))
    else:
        if not jsonld_scripts:
            issues.append(Issue(severity="warning", message="No microdata found either"))
            score -= 15
        else:
            issues.append(Issue(severity="info", message="No microdata found (JSON-LD is present)"))

    # RDFa (basic check)
    rdfa = soup.find_all(attrs={"vocab": True}) or soup.find_all(attrs={"typeof": True})
    if rdfa:
        issues.append(Issue(severity="info", message=f"{len(rdfa)} RDFa element(s) detected"))

    if not jsonld_scripts and not microdata_elements:
        issues.append(Issue(severity="error", message="No structured data found — add JSON-LD or microdata"))

    return CategoryResult(name="structured_data", score=max(0, score), issues=issues)

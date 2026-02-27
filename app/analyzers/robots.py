import requests
from urllib.parse import urlparse

from app.models import CategoryResult, Issue
from app.config import REQUEST_TIMEOUT, USER_AGENT
from app.fetcher import FetchResult


def analyze_robots(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    base = page.base_url
    robots_url = f"{base}/robots.txt"

    try:
        resp = requests.get(
            robots_url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code == 200 and resp.text.strip():
            issues.append(Issue(severity="pass", message=f"robots.txt found at {robots_url}"))
            lines = resp.text.strip().splitlines()

            disallow_rules = [l.strip() for l in lines if l.strip().lower().startswith("disallow:")]
            allow_rules = [l.strip() for l in lines if l.strip().lower().startswith("allow:")]
            sitemap_refs = [l.strip() for l in lines if l.strip().lower().startswith("sitemap:")]

            issues.append(Issue(severity="info", message=f"Rules: {len(disallow_rules)} disallow, {len(allow_rules)} allow"))

            if sitemap_refs:
                issues.append(Issue(severity="pass", message=f"Sitemap referenced in robots.txt"))
            else:
                issues.append(Issue(severity="warning", message="No Sitemap directive in robots.txt"))
                score -= 10

            # Check if current URL path is disallowed
            path = urlparse(page.url).path or "/"
            blocked = False
            for rule in disallow_rules:
                pattern = rule.split(":", 1)[1].strip()
                if pattern and path.startswith(pattern):
                    blocked = True
                    break

            if blocked:
                issues.append(Issue(severity="error", message=f"Current URL path ({path}) appears to be disallowed"))
                score -= 25
            else:
                issues.append(Issue(severity="pass", message="Current URL is not blocked by robots.txt"))

            # Check for Disallow: /
            full_block = any(
                rule.split(":", 1)[1].strip() == "/"
                for rule in disallow_rules
            )
            if full_block:
                issues.append(Issue(severity="error", message="robots.txt contains 'Disallow: /' — entire site may be blocked"))
                score -= 25

        elif resp.status_code == 200:
            issues.append(Issue(severity="warning", message="robots.txt exists but is empty"))
            score -= 20
        else:
            issues.append(Issue(severity="warning", message=f"robots.txt not found (HTTP {resp.status_code})"))
            score -= 20
    except requests.RequestException as e:
        issues.append(Issue(severity="warning", message=f"Could not fetch robots.txt: {str(e)[:100]}"))
        score -= 20

    return CategoryResult(name="robots", score=max(0, score), issues=issues)

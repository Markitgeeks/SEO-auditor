import re
from app.models import CategoryResult, Issue
from app.fetcher import FetchResult


def analyze_tracking(page: FetchResult) -> CategoryResult:
    issues: list[Issue] = []
    score = 100
    soup = page.soup
    html = page.response.text

    # Collect all script src attributes and inline script content
    scripts = soup.find_all("script")
    script_srcs = [s.get("src", "") for s in scripts if s.get("src")]
    inline_js = " ".join(s.get_text() for s in scripts if not s.get("src"))

    # --- Google Search Console verification ---
    gsc_meta = soup.find("meta", attrs={"name": "google-site-verification"})
    if gsc_meta and gsc_meta.get("content"):
        issues.append(Issue(severity="pass", message="Google Search Console verification meta tag found"))
    else:
        issues.append(Issue(severity="error", message="No Google Search Console verification meta tag",
                            impact="high", recommendation="Add a google-site-verification meta tag to verify site ownership in Search Console."))
        score -= 25

    # --- Google Analytics (GA4 / legacy UA) ---
    ga4 = any("gtag(" in inline_js and "G-" in inline_js for _ in [1]) or any(
        "googletagmanager.com/gtag" in src for src in script_srcs
    )
    ua_legacy = bool(re.search(r"UA-\d{4,10}-\d{1,4}", html))

    if ga4:
        issues.append(Issue(severity="pass", message="Google Analytics 4 (GA4) detected"))
    elif ua_legacy:
        issues.append(Issue(severity="warning", message="Legacy Universal Analytics (UA-) detected; consider migrating to GA4",
                            impact="medium", recommendation="Migrate to Google Analytics 4 as Universal Analytics has been sunset."))

    # --- Google Tag Manager ---
    gtm_script = any("gtm.js" in src or "googletagmanager.com" in src for src in script_srcs)
    gtm_inline = bool(re.search(r"GTM-[A-Z0-9]+", html))
    gtm = gtm_script or gtm_inline
    if gtm:
        container = re.search(r"(GTM-[A-Z0-9]+)", html)
        cid = container.group(1) if container else ""
        issues.append(Issue(severity="pass", message=f"Google Tag Manager detected{' (' + cid + ')' if cid else ''}"))
    else:
        issues.append(Issue(severity="warning", message="No Google Tag Manager detected",
                            impact="medium", recommendation="Set up Google Tag Manager for centralized tag management."))
        score -= 15

    # --- Facebook Pixel ---
    fb = any("connect.facebook.net" in src for src in script_srcs) or "fbq(" in inline_js
    if fb:
        issues.append(Issue(severity="info", message="Facebook Pixel detected"))

    # --- LinkedIn Insight ---
    li = any("snap.licdn.com" in src for src in script_srcs) or "_linkedin_partner_id" in inline_js
    if li:
        issues.append(Issue(severity="info", message="LinkedIn Insight Tag detected"))

    # --- TikTok Pixel ---
    tt = any("analytics.tiktok.com" in src for src in script_srcs) or "ttq.load" in inline_js
    if tt:
        issues.append(Issue(severity="info", message="TikTok Pixel detected"))

    # --- Pinterest Tag ---
    pin = any("s.pinimg.com" in src for src in script_srcs) or "pintrk" in inline_js
    if pin:
        issues.append(Issue(severity="info", message="Pinterest Tag detected"))

    # --- Microsoft / Bing UET ---
    bing = any("bat.bing.com" in src for src in script_srcs) or "bat.bing.com" in inline_js
    if bing:
        issues.append(Issue(severity="info", message="Microsoft/Bing UET Tag detected"))

    # --- Hotjar ---
    hotjar = any("hotjar.com" in src for src in script_srcs) or "hotjar.com" in inline_js
    if hotjar:
        issues.append(Issue(severity="info", message="Hotjar detected"))

    # --- Microsoft Clarity ---
    clarity = any("clarity.ms" in src for src in script_srcs) or "clarity.ms" in inline_js
    if clarity:
        issues.append(Issue(severity="info", message="Microsoft Clarity detected"))

    # --- No analytics at all ---
    if not ga4 and not ua_legacy:
        any_analytics = any([fb, li, tt, pin, bing, hotjar, clarity])
        if not any_analytics:
            issues.append(Issue(severity="error", message="No analytics or tracking pixels detected",
                                impact="high", recommendation="Install Google Analytics 4 or another analytics platform to track site performance."))
            score -= 30
        else:
            issues.append(Issue(severity="warning", message="No Google Analytics detected, but other tracking pixels found",
                                impact="medium", recommendation="Consider adding Google Analytics 4 for comprehensive traffic analysis."))
            score -= 15

    metrics = {
        "ga4": ga4,
        "gtm": gtm,
        "facebook_pixel": fb,
        "linkedin": li,
        "tiktok": tt,
        "pinterest": pin,
        "bing": bing,
        "hotjar": hotjar,
        "clarity": clarity,
    }

    return CategoryResult(name="tracking", score=max(0, score), issues=issues, metrics=metrics)

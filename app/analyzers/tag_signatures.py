"""Tag/pixel detection signature library for vendor identification."""

import re
from dataclasses import dataclass, field


@dataclass
class TagSignature:
    vendor: str
    vendor_short: str
    category: str  # tag_manager | analytics | advertising | heatmap | crm | social
    id_pattern: re.Pattern
    url_patterns: list[str] = field(default_factory=list)
    inline_patterns: list[str] = field(default_factory=list)
    noscript_patterns: list[str] = field(default_factory=list)
    is_essential: bool = False
    load_impact: str = "medium"  # high | medium | low
    notes: str = ""


TAG_SIGNATURES: list[TagSignature] = [
    TagSignature(
        vendor="Google Tag Manager",
        vendor_short="GTM",
        category="tag_manager",
        id_pattern=re.compile(r"GTM-[A-Z0-9]{4,8}"),
        url_patterns=["googletagmanager.com/gtm.js"],
        inline_patterns=["GTM-"],
        noscript_patterns=["googletagmanager.com/ns.html"],
        is_essential=True,
        load_impact="low",
    ),
    TagSignature(
        vendor="Google Analytics 4",
        vendor_short="GA4",
        category="analytics",
        id_pattern=re.compile(r"G-[A-Z0-9]{8,12}"),
        url_patterns=["googletagmanager.com/gtag/js"],
        inline_patterns=["gtag(", "G-"],
        is_essential=True,
        load_impact="low",
    ),
    TagSignature(
        vendor="Google Analytics UA",
        vendor_short="UA",
        category="analytics",
        id_pattern=re.compile(r"UA-\d{4,10}-\d{1,4}"),
        url_patterns=["google-analytics.com/analytics.js"],
        inline_patterns=["UA-"],
        load_impact="low",
        notes="Legacy - sunset July 2023",
    ),
    TagSignature(
        vendor="Google Ads",
        vendor_short="GAds",
        category="advertising",
        id_pattern=re.compile(r"AW-\d{8,12}"),
        url_patterns=["googleadservices.com"],
        inline_patterns=["AW-"],
        load_impact="medium",
    ),
    TagSignature(
        vendor="Meta Pixel",
        vendor_short="FBP",
        category="advertising",
        id_pattern=re.compile(r"\d{15,16}"),
        url_patterns=["connect.facebook.net"],
        inline_patterns=["fbq("],
        load_impact="medium",
    ),
    TagSignature(
        vendor="TikTok Pixel",
        vendor_short="TTP",
        category="advertising",
        id_pattern=re.compile(r"[A-Z0-9]{18,22}"),
        url_patterns=["analytics.tiktok.com"],
        inline_patterns=["ttq.load"],
        load_impact="medium",
    ),
    TagSignature(
        vendor="Pinterest Tag",
        vendor_short="PIN",
        category="advertising",
        id_pattern=re.compile(r"\d{13}"),
        url_patterns=["s.pinimg.com"],
        inline_patterns=["pintrk"],
        load_impact="low",
    ),
    TagSignature(
        vendor="Snapchat Pixel",
        vendor_short="SNAP",
        category="advertising",
        id_pattern=re.compile(r"[a-f0-9-]{36}"),
        url_patterns=["sc-static.net/scevent"],
        inline_patterns=["snaptr("],
        load_impact="low",
    ),
    TagSignature(
        vendor="LinkedIn Insight",
        vendor_short="LI",
        category="advertising",
        id_pattern=re.compile(r"\d{5,8}"),
        url_patterns=["snap.licdn.com"],
        inline_patterns=["_linkedin_partner_id"],
        load_impact="low",
    ),
    TagSignature(
        vendor="Microsoft/Bing UET",
        vendor_short="UET",
        category="advertising",
        id_pattern=re.compile(r"\d{7,9}"),
        url_patterns=["bat.bing.com"],
        inline_patterns=["uetq"],
        load_impact="low",
    ),
    TagSignature(
        vendor="Microsoft Clarity",
        vendor_short="CLAR",
        category="heatmap",
        id_pattern=re.compile(r"[a-z0-9]{8,12}"),
        url_patterns=["clarity.ms"],
        inline_patterns=["clarity("],
        load_impact="low",
    ),
    TagSignature(
        vendor="Hotjar",
        vendor_short="HJ",
        category="heatmap",
        id_pattern=re.compile(r"\d{6,8}"),
        url_patterns=["hotjar.com"],
        inline_patterns=["hj(", "_hjSettings"],
        load_impact="medium",
    ),
    TagSignature(
        vendor="Segment",
        vendor_short="SEG",
        category="analytics",
        id_pattern=re.compile(r"[a-zA-Z0-9]{20,32}"),
        url_patterns=["cdn.segment.com"],
        inline_patterns=["analytics.load"],
        load_impact="medium",
    ),
    TagSignature(
        vendor="Klaviyo",
        vendor_short="KLAV",
        category="crm",
        id_pattern=re.compile(r"[A-Za-z0-9]{6}"),
        url_patterns=["static.klaviyo.com"],
        inline_patterns=["_learnq"],
        load_impact="low",
    ),
    TagSignature(
        vendor="Intercom",
        vendor_short="ICOM",
        category="crm",
        id_pattern=re.compile(r"[a-z0-9]{8}"),
        url_patterns=["widget.intercom.io"],
        inline_patterns=["Intercom("],
        load_impact="medium",
    ),
    TagSignature(
        vendor="Heap Analytics",
        vendor_short="HEAP",
        category="analytics",
        id_pattern=re.compile(r"\d{8,12}"),
        url_patterns=["heapanalytics.com"],
        inline_patterns=["heap.load"],
        load_impact="medium",
    ),
    TagSignature(
        vendor="Mixpanel",
        vendor_short="MXP",
        category="analytics",
        id_pattern=re.compile(r"[a-f0-9]{32}"),
        url_patterns=["cdn.mxpnl.com"],
        inline_patterns=["mixpanel.init"],
        load_impact="medium",
    ),
    TagSignature(
        vendor="Shopify Analytics",
        vendor_short="SHOP",
        category="analytics",
        id_pattern=re.compile(r"trekkie"),
        url_patterns=["cdn.shopify.com/s/trekkie"],
        inline_patterns=["ShopifyAnalytics"],
        load_impact="low",
        notes="Built-in on Shopify stores",
    ),
    TagSignature(
        vendor="Lucky Orange",
        vendor_short="LO",
        category="heatmap",
        id_pattern=re.compile(r"\d{5,8}"),
        url_patterns=["luckyorange.com"],
        inline_patterns=["__lo_site_id"],
        load_impact="medium",
    ),
]

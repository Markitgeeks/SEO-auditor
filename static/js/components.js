/* ============================================================
   Pure Render Functions — Shopify Admin Panel Style
   ============================================================ */

// --- Helpers ---

function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function scoreColor(score) {
    if (score >= 80) return 'var(--score-success)';
    if (score >= 50) return 'var(--score-warning)';
    return 'var(--score-critical)';
}

function scoreColorRaw(score) {
    if (score >= 80) return '#008060';
    if (score >= 50) return '#b98900';
    return '#d72c0d';
}

function scoreTone(score) {
    if (score >= 80) return 'success';
    if (score >= 50) return 'warning';
    return 'critical';
}

function severityIcon(severity) {
    const symbols = { error: '!', warning: '!', info: 'i', pass: '\u2713' };
    return `<span class="severity-icon severity-${severity}">${symbols[severity] || '?'}</span>`;
}

function worstSeverity(issues) {
    if (issues.some(i => i.severity === 'error')) return 'error';
    if (issues.some(i => i.severity === 'warning')) return 'warning';
    if (issues.some(i => i.severity === 'info')) return 'info';
    return 'pass';
}

function renderIntelKPI(label, value, source) {
    return `<div class="kpi-card">
        <div class="kpi-card__value">${escapeHtml(String(value))}</div>
        <div class="kpi-card__label">${escapeHtml(label)}</div>
        ${source ? `<div class="kpi-card__source Polaris-Text--bodySm Polaris-Text--subdued">${escapeHtml(source)}</div>` : ''}
    </div>`;
}

const ISSUES_PER_PAGE = 50;

// --- Category metadata ---

const CATEGORY_LABELS = {
    meta_tags: 'Meta Tags',
    headings: 'Headings',
    images: 'Images',
    links: 'Links',
    performance: 'Performance',
    mobile: 'Mobile',
    structured_data: 'Structured Data',
    sitemap: 'Sitemap',
    robots: 'Robots.txt',
    tracking: 'Tracking & Pixels',
    semantic: 'Semantic Structure',
    ads_quality: 'Ads Landing Page',
    serp_features: 'SERP Features',
    accessibility: 'Accessibility',
    pagespeed_insights: 'Performance Lab',
    schema_validation: 'Schema Validation',
    keyword_research: 'Keyword Research',
};

const CATEGORY_ICONS = {
    meta_tags: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"/></svg>',
    headings: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h8m-8 6h16"/></svg>',
    images: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
    links: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>',
    performance: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
    mobile: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>',
    structured_data: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
    sitemap: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 20l-5.447-2.724A2 2 0 013 15.382V5.618a2 2 0 011.553-1.894L9 2m0 18l6-3m-6 3V2m6 15l5.447-2.724A2 2 0 0021 12.382V5.618a2 2 0 00-1.553-1.894L15 2m0 15V2m0 0L9 2"/></svg>',
    robots: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>',
    tracking: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>',
    semantic: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>',
    ads_quality: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/><path stroke-linecap="round" stroke-linejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/></svg>',
    serp_features: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>',
    accessibility: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
    pagespeed_insights: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
    schema_validation: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>',
    keyword_research: '<svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>',
};

// --- KPI formatting helpers ---

const METRIC_LABELS = {
    response_time_ms: { label: 'Response Time', unit: 'ms', good: v => v < 800 },
    page_size_kb: { label: 'Page Size', unit: 'KB', good: v => v < 1500 },
    is_https: { label: 'HTTPS', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    blocking_scripts_count: { label: 'Blocking Scripts', unit: '', good: v => v === 0 },
    title_length: { label: 'Title Length', unit: 'chars', good: v => v >= 30 && v <= 60 },
    description_length: { label: 'Description', unit: 'chars', good: v => v >= 70 && v <= 160 },
    has_canonical: { label: 'Canonical', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    og_tags_count: { label: 'OG Tags', unit: '', good: v => v >= 4 },
    has_lang: { label: 'Lang Attr', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    h1_count: { label: 'H1 Count', unit: '', good: v => v === 1 },
    total_headings: { label: 'Total Headings', unit: '', good: v => v > 0 },
    hierarchy_valid: { label: 'Hierarchy', unit: '', format: v => v ? 'Valid' : 'Broken', good: v => v },
    total_images: { label: 'Total Images', unit: '' },
    missing_alt_count: { label: 'Missing Alt', unit: '', good: v => v === 0 },
    missing_alt_pct: { label: 'Missing Alt', unit: '%', good: v => v === 0 },
    lazy_loading_pct: { label: 'Lazy Loading', unit: '%', good: v => v >= 50 },
    missing_dimensions_count: { label: 'Missing Dims', unit: '', good: v => v === 0 },
    total_links: { label: 'Total Links', unit: '' },
    internal_links: { label: 'Internal Links', unit: '', good: v => v > 0 },
    external_links: { label: 'External Links', unit: '' },
    empty_invalid: { label: 'Empty/Invalid', unit: '', good: v => v === 0 },
    nofollow_internal: { label: 'Nofollow Internal', unit: '', good: v => v === 0 },
    has_viewport: { label: 'Viewport', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    zoom_disabled: { label: 'Zoom Disabled', unit: '', format: v => v ? 'Yes' : 'No', good: v => !v },
    fixed_width_elements: { label: 'Fixed Width', unit: '', good: v => v === 0 },
    has_media_queries: { label: 'Media Queries', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    jsonld_count: { label: 'JSON-LD Blocks', unit: '', good: v => v > 0 },
    microdata_count: { label: 'Microdata', unit: '' },
    has_opengraph: { label: 'OpenGraph', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    rich_snippets_eligible: { label: 'Rich Snippets', unit: '', format: v => v ? 'Eligible' : 'No', good: v => v },
    accessible: { label: 'Accessible', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    url_count: { label: 'URLs in Sitemap', unit: '' },
    stale_entries: { label: 'Stale Entries', unit: '', good: v => v === 0 },
    current_url_in_sitemap: { label: 'URL in Sitemap', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    present: { label: 'Present', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    disallow_count: { label: 'Disallow Rules', unit: '' },
    allow_count: { label: 'Allow Rules', unit: '' },
    sitemap_referenced: { label: 'Sitemap Ref', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    current_url_blocked: { label: 'URL Blocked', unit: '', format: v => v ? 'Yes' : 'No', good: v => !v },
    ga4: { label: 'GA4', unit: '', format: v => v ? 'Detected' : 'No', good: v => v },
    gtm: { label: 'GTM', unit: '', format: v => v ? 'Detected' : 'No', good: v => v },
    facebook_pixel: { label: 'Facebook', unit: '', format: v => v ? 'Detected' : 'No' },
    linkedin: { label: 'LinkedIn', unit: '', format: v => v ? 'Detected' : 'No' },
    tiktok: { label: 'TikTok', unit: '', format: v => v ? 'Detected' : 'No' },
    pinterest: { label: 'Pinterest', unit: '', format: v => v ? 'Detected' : 'No' },
    bing: { label: 'Bing UET', unit: '', format: v => v ? 'Detected' : 'No' },
    hotjar: { label: 'Hotjar', unit: '', format: v => v ? 'Detected' : 'No' },
    clarity: { label: 'Clarity', unit: '', format: v => v ? 'Detected' : 'No' },
    semantic_elements: { label: 'Semantic Elements', unit: '', good: v => v >= 4 },
    aria_roles: { label: 'ARIA Roles', unit: '' },
    content_to_html_ratio: { label: 'Content Ratio', unit: '%', good: v => v >= 25 },
    main_count: { label: '<main> Count', unit: '', good: v => v === 1 },
    https_compliant: { label: 'HTTPS', unit: '', format: v => v ? 'Yes' : 'No', good: v => v },
    load_speed_ms: { label: 'Load Speed', unit: 'ms', good: v => v < 1000 },
    word_count: { label: 'Word Count', unit: '', good: v => v >= 300 },
    cta_count: { label: 'CTAs Found', unit: '', good: v => v > 0 },
    eligible_count: { label: 'Eligible Features', unit: '', good: v => v >= 3 },
    sitelinks_eligible: { label: 'Sitelinks', unit: '', format: v => v ? 'Eligible' : 'No', good: v => v },
    image_pack_eligible: { label: 'Image Pack', unit: '', format: v => v ? 'Eligible' : 'No', good: v => v },
    error_count: { label: 'Errors', unit: '', good: v => v === 0 },
    contrast_issues: { label: 'Contrast Issues', unit: '', good: v => v === 0 },
    alert_count: { label: 'Alerts', unit: '', good: v => v === 0 },
    feature_count: { label: 'Features', unit: '' },
    aria_count: { label: 'ARIA Attrs', unit: '' },
    // PSI metrics
    mobile_score: { label: 'Mobile Score', unit: '', good: v => v >= 90 },
    desktop_score: { label: 'Desktop Score', unit: '', good: v => v >= 90 },
    mobile_lcp_ms: { label: 'Mobile LCP', unit: 'ms', good: v => v < 2500 },
    desktop_lcp_ms: { label: 'Desktop LCP', unit: 'ms', good: v => v < 2500 },
    mobile_cls: { label: 'Mobile CLS', unit: '', good: v => v < 0.1 },
    desktop_cls: { label: 'Desktop CLS', unit: '', good: v => v < 0.1 },
    mobile_tbt_ms: { label: 'Mobile TBT', unit: 'ms', good: v => v < 300 },
    desktop_tbt_ms: { label: 'Desktop TBT', unit: 'ms', good: v => v < 300 },
    // Schema validation metrics
    entities_found: { label: 'Entities', unit: '' },
    syntax_errors: { label: 'Syntax Errors', unit: '', good: v => v === 0 },
    type_errors: { label: 'Type Errors', unit: '', good: v => v === 0 },
    property_warnings: { label: 'Prop Warnings', unit: '', good: v => v === 0 },
    valid_entities_pct: { label: 'Valid Entities', unit: '%', good: v => v === 100 },
    rdfa_count: { label: 'RDFa', unit: '' },
};


// ============================================================
// Render: Sidebar
// ============================================================

function renderSidebar(categories, selected, auditData) {
    if (!categories || !categories.length) return '';

    const overallScore = auditData ? auditData.overall_score : 0;
    const overallTone = scoreTone(overallScore);
    const overallColor = scoreColorRaw(overallScore);

    // Navigation bar: back to brand / home
    const brand = Store.get('selectedBrand');
    let html = `<div class="sidebar-back-nav">
        <a class="sidebar-back-link" data-nav="home">
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1m-2 0h2"/></svg>
            Home
        </a>
        ${brand ? `<a class="sidebar-back-link" data-nav="brand-detail">
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
            ${escapeHtml(brand.name)}
        </a>` : ''}
    </div>`;

    html += `
        <div class="sidebar-score">
            <div class="sidebar-score__gauge">
                <svg width="80" height="80" viewBox="0 0 80 80">
                    <circle class="bg-ring" cx="40" cy="40" r="34" fill="none" stroke-width="6"/>
                    <circle class="fg-ring sidebar-score-ring" cx="40" cy="40" r="34" fill="none" stroke-width="6"
                        stroke-dasharray="213.6" stroke-dashoffset="${213.6 - (overallScore / 100) * 213.6}" stroke-linecap="round"
                        style="stroke:${overallColor};transform:rotate(-90deg);transform-origin:center"/>
                </svg>
                <div class="sidebar-score__value" style="color:${overallColor}">${overallScore}</div>
            </div>
            <div class="Polaris-Text--bodySm Polaris-Text--subdued">Overall Score</div>
        </div>
        <div class="sidebar-nav">
            <button class="sidebar-item ${selected === 'overview' ? 'sidebar-item--selected' : ''}" data-category="overview">
                <span class="sidebar-item__icon"><svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1m-2 0h2"/></svg></span>
                <span class="sidebar-item__label">Overview</span>
            </button>`;

    for (const cat of categories) {
        const label = CATEGORY_LABELS[cat.name] || cat.name;
        const isSelected = selected === cat.name;
        const worst = cat.status === 'error' ? 'error' : worstSeverity(cat.issues || []);
        const dotColors = { error: '#d72c0d', warning: '#b98900', info: '#0073b0', pass: '#008060' };
        const dotColor = dotColors[worst] || '#8c9196';
        const errorCount = cat.summary ? cat.summary.error_count + cat.summary.warning_count : 0;
        const icon = CATEGORY_ICONS[cat.name] || '';

        html += `
            <button class="sidebar-item ${isSelected ? 'sidebar-item--selected' : ''}" data-category="${escapeHtml(cat.name)}">
                <span class="sidebar-item__icon" style="color:${dotColor}">${icon}</span>
                <span class="sidebar-item__label">${escapeHtml(label)}</span>
                <span class="sidebar-item__score" style="color:${scoreColorRaw(cat.score)}">${cat.score}</span>
                ${errorCount > 0 ? `<span class="sidebar-item__badge">${errorCount}</span>` : ''}
            </button>`;
    }

    // --- New module sidebar items (divider + PSI + Schema) ---
    const hasNewModules = (auditData && auditData.pagespeed_insights) || (auditData && auditData.schema_validation);
    if (hasNewModules || (Store.get('keywordEnabled'))) {
        html += '<div class="sidebar-divider"></div>';
    }

    if (auditData && auditData.pagespeed_insights && auditData.pagespeed_insights.status !== 'not_configured') {
        const psi = auditData.pagespeed_insights;
        const psiScore = psi.mobile ? psi.mobile.score : (psi.desktop ? psi.desktop.score : 0);
        const isSelected = selected === 'pagespeed';
        html += `<button class="sidebar-item ${isSelected ? 'sidebar-item--selected' : ''}" data-category="pagespeed">
            <span class="sidebar-item__icon" style="color:${scoreColorRaw(psiScore)}">${CATEGORY_ICONS.pagespeed_insights}</span>
            <span class="sidebar-item__label">Performance Lab</span>
            <span class="sidebar-item__score" style="color:${scoreColorRaw(psiScore)}">${psiScore}</span>
        </button>`;
    }

    if (auditData && auditData.schema_validation) {
        const sv = auditData.schema_validation;
        const svValid = sv.metrics ? sv.metrics.valid_entities_pct : 100;
        const svColor = svValid === 100 ? '#008060' : svValid >= 50 ? '#b98900' : '#d72c0d';
        const isSelected = selected === 'schema_validation';
        html += `<button class="sidebar-item ${isSelected ? 'sidebar-item--selected' : ''}" data-category="schema_validation">
            <span class="sidebar-item__icon" style="color:${svColor}">${CATEGORY_ICONS.schema_validation}</span>
            <span class="sidebar-item__label">Schema Validation</span>
        </button>`;
    }

    if (Store.get('keywordEnabled')) {
        const isSelected = selected === 'keyword_research';
        html += `<button class="sidebar-item ${isSelected ? 'sidebar-item--selected' : ''}" data-category="keyword_research">
            <span class="sidebar-item__icon" style="color:#005bd3">${CATEGORY_ICONS.keyword_research}</span>
            <span class="sidebar-item__label">Keyword Research</span>
        </button>`;
    }

    // Crawl & Intel sidebar items
    if (auditData && auditData.crawl_results) {
        const isSelected = selected === 'crawl';
        html += `<button class="sidebar-item ${isSelected ? 'sidebar-item--selected' : ''}" data-category="crawl">
            <span class="sidebar-item__icon" style="color:${scoreColorRaw(auditData.crawl_results.score)}"><svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9"/></svg></span>
            <span class="sidebar-item__label">Site Crawl</span>
            <span class="sidebar-item__score" style="color:${scoreColorRaw(auditData.crawl_results.score)}">${auditData.crawl_results.score}</span>
        </button>`;
    }
    if (auditData && auditData.external_insights) {
        const isSelected = selected === 'intel';
        html += `<button class="sidebar-item ${isSelected ? 'sidebar-item--selected' : ''}" data-category="intel">
            <span class="sidebar-item__icon" style="color:#005bd3"><svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg></span>
            <span class="sidebar-item__label">Market Intel</span>
        </button>`;
    }

    html += '</div>';
    return html;
}


// ============================================================
// Render: KPI Card
// ============================================================

function renderKPICard(key, value) {
    const meta = METRIC_LABELS[key] || { label: key, unit: '' };
    let displayVal;
    if (meta.format) {
        displayVal = meta.format(value);
    } else if (typeof value === 'number') {
        displayVal = value.toLocaleString();
    } else if (Array.isArray(value)) {
        displayVal = value.length ? value.join(', ') : 'None';
    } else {
        displayVal = String(value ?? 'N/A');
    }

    let colorClass = '';
    if (meta.good) {
        colorClass = meta.good(value) ? 'kpi-card--good' : 'kpi-card--bad';
    }

    return `<div class="kpi-card ${colorClass}">
        <p class="kpi-card__label">${escapeHtml(meta.label)}</p>
        <p class="kpi-card__value">${escapeHtml(displayVal)}</p>
        ${meta.unit ? `<p class="kpi-card__unit">${escapeHtml(meta.unit)}</p>` : ''}
    </div>`;
}


// ============================================================
// Render: Category Header
// ============================================================

function renderCategoryHeader(category) {
    const label = CATEGORY_LABELS[category.name] || category.name;
    const icon = CATEGORY_ICONS[category.name] || '';
    const color = scoreColorRaw(category.score);
    const tone = scoreTone(category.score);

    let statusBanner = '';
    if (category.status === 'error') {
        statusBanner = `<div class="Polaris-Banner Polaris-Banner--warning mb-400">
            <span>Module Error: ${escapeHtml(category.error_message || 'Unknown error')}. Try re-running the audit.</span>
        </div>`;
    } else if (category.summary && category.summary.error_count === 0 && category.summary.warning_count === 0) {
        statusBanner = `<div class="Polaris-Banner Polaris-Banner--success mb-400">
            <span>All checks passed</span>
        </div>`;
    }

    return `
        <div class="category-header">
            <div class="category-header__title">
                <span class="category-header__icon" style="color:${color}">${icon}</span>
                <h2 class="Polaris-Text--headingLg">${escapeHtml(label)}</h2>
                <span class="Polaris-Badge Polaris-Badge--${tone}" style="margin-left:var(--p-space-200)">${category.score}/100</span>
            </div>
            ${category.duration_ms != null ? `<span class="Polaris-Text--bodySm Polaris-Text--subdued">${category.duration_ms}ms</span>` : ''}
        </div>
        ${statusBanner}
        <div class="Polaris-ProgressBar mb-400">
            <div class="Polaris-ProgressBar__Fill Polaris-ProgressBar__Fill--${tone}" style="width:${category.score}%"></div>
        </div>`;
}


// ============================================================
// Render: Category Tabs
// ============================================================

function renderCategoryTabs(activeTab) {
    const tabs = [
        { id: 'summary', label: 'Summary' },
        { id: 'issues', label: 'Issues' },
        { id: 'evidence', label: 'Evidence' },
        { id: 'recommendations', label: 'Recommendations' },
    ];
    return `<div class="Polaris-Tabs mb-400">${tabs.map(t =>
        `<button class="Polaris-Tabs__Tab ${activeTab === t.id ? 'Polaris-Tabs__Tab--selected' : ''}" data-tab="${t.id}">${t.label}</button>`
    ).join('')}</div>`;
}


// ============================================================
// Render: Summary Tab (KPI cards + severity bar)
// ============================================================

function renderSummaryTab(category) {
    if (!category.metrics) {
        return `<div class="Polaris-Banner Polaris-Banner--info"><span>Metrics not available for this category.</span></div>`;
    }

    // KPI cards
    let html = '<div class="kpi-grid">';
    for (const [key, value] of Object.entries(category.metrics)) {
        if (key === 'jsonld_types' || key === 'eligible_features' || key === 'conversion_trackers' || key === 'heading_counts' || key === 'h1_text') continue;
        html += renderKPICard(key, value);
    }
    html += '</div>';

    // Severity distribution bar
    if (category.summary) {
        const s = category.summary;
        const total = s.error_count + s.warning_count + s.info_count + s.pass_count;
        if (total > 0) {
            html += `<div class="severity-bar-container mt-400">
                <p class="Polaris-Text--bodySm Polaris-Text--subdued mb-200">Issue Distribution</p>
                <div class="severity-bar">
                    ${s.error_count ? `<div class="severity-bar__segment severity-bar__segment--error" style="width:${(s.error_count/total*100)}%" title="${s.error_count} errors"></div>` : ''}
                    ${s.warning_count ? `<div class="severity-bar__segment severity-bar__segment--warning" style="width:${(s.warning_count/total*100)}%" title="${s.warning_count} warnings"></div>` : ''}
                    ${s.info_count ? `<div class="severity-bar__segment severity-bar__segment--info" style="width:${(s.info_count/total*100)}%" title="${s.info_count} info"></div>` : ''}
                    ${s.pass_count ? `<div class="severity-bar__segment severity-bar__segment--pass" style="width:${(s.pass_count/total*100)}%" title="${s.pass_count} passed"></div>` : ''}
                </div>
                <div class="severity-bar__legend">
                    ${s.error_count ? `<span class="severity-bar__legend-item"><span class="severity-bar__dot severity-bar__dot--error"></span>${s.error_count} Error</span>` : ''}
                    ${s.warning_count ? `<span class="severity-bar__legend-item"><span class="severity-bar__dot severity-bar__dot--warning"></span>${s.warning_count} Warning</span>` : ''}
                    ${s.info_count ? `<span class="severity-bar__legend-item"><span class="severity-bar__dot severity-bar__dot--info"></span>${s.info_count} Info</span>` : ''}
                    ${s.pass_count ? `<span class="severity-bar__legend-item"><span class="severity-bar__dot severity-bar__dot--pass"></span>${s.pass_count} Pass</span>` : ''}
                </div>
            </div>`;
        }
    }

    // Special: show lists like jsonld_types, eligible_features
    const listKeys = { jsonld_types: 'JSON-LD Types', eligible_features: 'Eligible Features', conversion_trackers: 'Conversion Trackers' };
    for (const [key, label] of Object.entries(listKeys)) {
        const val = category.metrics[key];
        if (val && Array.isArray(val) && val.length) {
            html += `<div class="mt-400"><p class="Polaris-Text--headingSm mb-200">${label}</p><div style="display:flex;flex-wrap:wrap;gap:var(--p-space-100)">`;
            val.forEach(v => { html += `<span class="Polaris-Badge Polaris-Badge--info">${escapeHtml(v)}</span>`; });
            html += '</div></div>';
        }
    }

    // Heading counts
    if (category.metrics.heading_counts) {
        html += `<div class="mt-400"><p class="Polaris-Text--headingSm mb-200">Heading Distribution</p><div class="kpi-grid">`;
        for (const [h, count] of Object.entries(category.metrics.heading_counts)) {
            html += `<div class="kpi-card"><p class="kpi-card__label">${escapeHtml(h.toUpperCase())}</p><p class="kpi-card__value">${count}</p></div>`;
        }
        html += '</div></div>';
    }

    // H1 text
    if (category.metrics.h1_text) {
        html += `<div class="mt-400"><p class="Polaris-Text--headingSm mb-100">H1 Text</p><p class="Polaris-Text--bodyMd">"${escapeHtml(category.metrics.h1_text)}"</p></div>`;
    }

    return html;
}


// ============================================================
// Render: Issue List (with filter, search, sort, pagination)
// ============================================================

function renderIssueList(issues, filter, sort, page, search) {
    if (!issues || !issues.length) {
        return `<div class="Polaris-Banner Polaris-Banner--success"><span>No issues found.</span></div>`;
    }

    // Filter
    let filtered = issues;
    if (filter && filter !== 'all') {
        filtered = filtered.filter(i => i.severity === filter);
    }
    if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter(i => i.message.toLowerCase().includes(q) || (i.evidence && i.evidence.toLowerCase().includes(q)));
    }

    // Sort
    const severityOrder = { error: 0, warning: 1, info: 2, pass: 3 };
    const impactOrder = { high: 0, medium: 1, low: 2 };
    if (sort === 'impact') {
        filtered.sort((a, b) => (impactOrder[a.impact] ?? 3) - (impactOrder[b.impact] ?? 3));
    } else {
        filtered.sort((a, b) => (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3));
    }

    // Paginate
    const totalPages = Math.ceil(filtered.length / ISSUES_PER_PAGE);
    const currentPage = Math.min(page || 0, totalPages - 1);
    const pageItems = filtered.slice(currentPage * ISSUES_PER_PAGE, (currentPage + 1) * ISSUES_PER_PAGE);

    // Filter bar
    const counts = { all: issues.length, error: 0, warning: 0, info: 0, pass: 0 };
    issues.forEach(i => counts[i.severity]++);

    let html = `<div class="filter-bar">
        ${['all', 'error', 'warning', 'info', 'pass'].map(f =>
            `<button class="filter-pill ${filter === f ? 'filter-pill--active' : ''} ${f !== 'all' ? 'filter-pill--' + f : ''}" data-filter="${f}">${f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)} (${counts[f]})</button>`
        ).join('')}
        <div class="filter-sort">
            <button class="filter-pill ${sort === 'severity' ? 'filter-pill--active' : ''}" data-sort="severity" title="Sort by severity">Severity</button>
            <button class="filter-pill ${sort === 'impact' ? 'filter-pill--active' : ''}" data-sort="impact" title="Sort by impact">Impact</button>
        </div>
        <div class="filter-search">
            <input type="text" class="filter-search__input" placeholder="Search issues..." value="${escapeHtml(search || '')}" data-action="search-issues">
        </div>
    </div>`;

    // Issue rows
    html += '<div class="issue-list">';
    pageItems.forEach((issue, idx) => {
        const rowId = `issue-${currentPage}-${idx}`;
        const hasDetails = issue.evidence || issue.recommendation;
        html += `<div class="issue-row" data-issue-id="${rowId}">
            <div class="issue-row__main ${hasDetails ? 'issue-row__main--expandable' : ''}">
                ${severityIcon(issue.severity)}
                <span class="issue-row__message">${escapeHtml(issue.message)}</span>
                ${issue.impact ? `<span class="Polaris-Badge Polaris-Badge--${issue.impact === 'high' ? 'critical' : issue.impact === 'medium' ? 'warning' : 'default'}">${escapeHtml(issue.impact)}</span>` : ''}
                ${hasDetails ? `<button class="issue-row__expand" data-toggle="${rowId}" aria-label="Expand">
                    <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor"><path d="M6 8l4 4 4-4"/></svg>
                </button>` : ''}
            </div>
            ${hasDetails ? `<div class="issue-row__details" id="${rowId}">
                ${issue.evidence ? `<div class="evidence-block"><strong>Evidence:</strong> ${escapeHtml(issue.evidence)}</div>` : ''}
                ${issue.recommendation ? `<div class="recommendation-block"><strong>Recommendation:</strong> ${escapeHtml(issue.recommendation)}</div>` : ''}
            </div>` : ''}
        </div>`;
    });
    html += '</div>';

    // Pagination
    if (totalPages > 1) {
        html += `<div class="pagination">
            <button class="Polaris-Button Polaris-Button--default" data-page="${currentPage - 1}" ${currentPage <= 0 ? 'disabled' : ''}>Prev</button>
            <span class="Polaris-Text--bodySm">Page ${currentPage + 1} of ${totalPages}</span>
            <button class="Polaris-Button Polaris-Button--default" data-page="${currentPage + 1}" ${currentPage >= totalPages - 1 ? 'disabled' : ''}>Next</button>
        </div>`;
    }

    return html;
}


// ============================================================
// Render: Evidence Tab
// ============================================================

function renderEvidenceTab(category) {
    const withEvidence = (category.issues || []).filter(i => i.evidence);
    if (!withEvidence.length) {
        return `<div class="Polaris-Banner Polaris-Banner--info"><span>No evidence data available for this category.</span></div>`;
    }

    let html = '';
    withEvidence.forEach(issue => {
        html += `<div class="evidence-item mb-300">
            <div style="display:flex;align-items:center;gap:var(--p-space-200);margin-bottom:var(--p-space-100)">
                ${severityIcon(issue.severity)}
                <span class="Polaris-Text--bodyMd" style="font-weight:var(--p-font-weight-medium)">${escapeHtml(issue.message)}</span>
            </div>
            <div class="evidence-block">${escapeHtml(issue.evidence)}</div>
        </div>`;
    });
    return html;
}


// ============================================================
// Render: Recommendations Tab
// ============================================================

function renderRecommendationsTab(category) {
    const withRec = (category.issues || []).filter(i => i.recommendation);
    if (!withRec.length) {
        return `<div class="Polaris-Banner Polaris-Banner--info"><span>No recommendations available for this category.</span></div>`;
    }

    // Group by impact
    const groups = { high: [], medium: [], low: [], none: [] };
    withRec.forEach(issue => {
        const impact = issue.impact || 'none';
        (groups[impact] || groups.none).push(issue);
    });

    const impactLabels = { high: 'High Impact', medium: 'Medium Impact', low: 'Low Impact', none: 'General' };
    const impactTones = { high: 'critical', medium: 'warning', low: 'info', none: 'default' };

    let html = '';
    for (const [impact, items] of Object.entries(groups)) {
        if (!items.length) continue;
        html += `<div class="mb-400">
            <h3 class="Polaris-Text--headingSm mb-200">
                <span class="Polaris-Badge Polaris-Badge--${impactTones[impact]}">${impactLabels[impact]}</span>
            </h3>`;
        items.forEach(issue => {
            html += `<div class="recommendation-item">
                ${severityIcon(issue.severity)}
                <div>
                    <p class="Polaris-Text--bodyMd" style="font-weight:var(--p-font-weight-medium)">${escapeHtml(issue.message)}</p>
                    <p class="Polaris-Text--bodySm Polaris-Text--subdued mt-100">${escapeHtml(issue.recommendation)}</p>
                </div>
            </div>`;
        });
        html += '</div>';
    }
    return html;
}


// ============================================================
// Render: Overview Panel
// ============================================================

function renderOverviewPanel(auditData, brand) {
    if (!auditData) return '';

    const score = auditData.overall_score;
    const color = scoreColorRaw(score);
    const tone = scoreTone(score);

    // Aggregate stats
    let totalErrors = 0, totalWarnings = 0, totalPasses = 0;
    auditData.categories.forEach(cat => {
        const s = cat.summary || {};
        totalErrors += s.error_count || 0;
        totalWarnings += s.warning_count || 0;
        totalPasses += s.pass_count || 0;
    });
    const totalCategories = auditData.categories.length;

    // === Hero Card: Score gauge LEFT + summary stats RIGHT ===
    let html = `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">
        <div class="overview-hero">
            <div class="overview-hero__gauge">
                <div class="score-gauge">
                    <svg width="140" height="140" viewBox="0 0 160 160">
                        <circle class="bg-ring" cx="80" cy="80" r="68" fill="none" stroke-width="10"/>
                        <circle class="fg-ring" cx="80" cy="80" r="68" fill="none" stroke-width="10"
                            stroke-dasharray="427" stroke-dashoffset="${427 - (score / 100) * 427}" stroke-linecap="round"
                            style="stroke:${color};transform:rotate(-90deg);transform-origin:center"/>
                    </svg>
                    <div class="score-text">
                        <span class="score-value" style="color:${color}">${score}</span>
                        <span class="score-label">Overall</span>
                    </div>
                </div>
                <p class="Polaris-Text--bodySm Polaris-Text--subdued mt-100">${escapeHtml(auditData.url)}</p>
            </div>
            <div class="overview-stats">
                <div class="overview-stat">
                    <span class="overview-stat__value" style="color:var(--p-color-text-critical)">${totalErrors}</span>
                    <span class="overview-stat__label">Errors</span>
                </div>
                <div class="overview-stat">
                    <span class="overview-stat__value" style="color:var(--p-color-text-warning)">${totalWarnings}</span>
                    <span class="overview-stat__label">Warnings</span>
                </div>
                <div class="overview-stat">
                    <span class="overview-stat__value" style="color:var(--p-color-text-success)">${totalPasses}</span>
                    <span class="overview-stat__label">Passed</span>
                </div>
                <div class="overview-stat">
                    <span class="overview-stat__value">${totalCategories}</span>
                    <span class="overview-stat__label">Categories</span>
                </div>
            </div>
        </div>
    </div></div>`;

    // === Brand Summary Card (if brand data available) ===
    if (brand) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Brand Profile</h3></div><div class="Polaris-Card__Section">
            <div class="kpi-grid">
                ${brand.industry ? renderIntelKPI('Industry', brand.industry, 'Auto-detected') : ''}
                ${brand.revenue_range ? renderIntelKPI('Revenue', brand.revenue_range, '') : ''}
                ${brand.persona ? renderIntelKPI('Persona', brand.persona, '') : ''}
                ${renderIntelKPI('Audits', String(brand.audit_count || 0), '')}
            </div>
            ${brand.description ? `<p class="Polaris-Text--bodyMd mt-200">${escapeHtml(brand.description)}</p>` : ''}
        </div></div>`;
    }

    // === Category Score Grid ===
    html += `<div class="category-grid mb-400">`;
    auditData.categories.forEach(cat => {
        const label = CATEGORY_LABELS[cat.name] || cat.name;
        const icon = CATEGORY_ICONS[cat.name] || '';
        const s = cat.summary || {};
        const catColor = scoreColorRaw(cat.score);
        const catTone = scoreTone(cat.score);
        const errCount = s.error_count || 0;
        const warnCount = s.warning_count || 0;
        html += `<div class="category-mini-card" data-category="${escapeHtml(cat.name)}" role="button" tabindex="0">
            <div class="category-mini-card__header">
                <span class="category-mini-card__icon">${icon}</span>
                <span class="Polaris-Badge Polaris-Badge--${catTone}" style="font-weight:var(--p-font-weight-semibold)">${cat.score}</span>
            </div>
            <div class="category-mini-card__label">${escapeHtml(label)}</div>
            <div class="category-mini-card__counts">
                ${errCount > 0 ? `<span class="Polaris-Text--bodySm" style="color:var(--p-color-text-critical)">${errCount} error${errCount !== 1 ? 's' : ''}</span>` : ''}
                ${warnCount > 0 ? `<span class="Polaris-Text--bodySm" style="color:var(--p-color-text-warning)">${warnCount} warning${warnCount !== 1 ? 's' : ''}</span>` : ''}
                ${errCount === 0 && warnCount === 0 ? '<span class="Polaris-Text--bodySm Polaris-Text--success">All clear</span>' : ''}
            </div>
        </div>`;
    });
    html += `</div>`;

    // === Top Issues Card ===
    const allIssues = [];
    auditData.categories.forEach(cat => {
        (cat.issues || []).forEach(issue => {
            if (issue.severity === 'error' || issue.severity === 'warning') {
                allIssues.push({ category: CATEGORY_LABELS[cat.name] || cat.name, categoryKey: cat.name, ...issue });
            }
        });
    });
    // Sort: errors first, then warnings
    allIssues.sort((a, b) => (a.severity === 'error' ? 0 : 1) - (b.severity === 'error' ? 0 : 1));

    if (allIssues.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Top Issues (${allIssues.length})</h3></div><div class="Polaris-Card__Section" style="display:flex;flex-direction:column;gap:var(--p-space-200)">`;
        allIssues.slice(0, 8).forEach(issue => {
            const borderColor = issue.severity === 'error' ? 'var(--score-critical)' : 'var(--score-warning)';
            const sevLabel = issue.severity === 'error' ? 'critical' : 'warning';
            html += `<div class="top-issue-card" style="border-left-color:${borderColor}">
                <div class="top-issue-card__header">
                    <span class="Polaris-Badge Polaris-Badge--${sevLabel}">${escapeHtml(issue.severity)}</span>
                    <span class="Polaris-Badge">${escapeHtml(issue.category)}</span>
                </div>
                <p class="Polaris-Text--bodyMd" style="font-weight:var(--p-font-weight-medium);margin:var(--p-space-100) 0 0">${escapeHtml(issue.message)}</p>
                ${issue.recommendation ? `<p class="Polaris-Text--bodySm Polaris-Text--subdued" style="margin-top:var(--p-space-050)">${escapeHtml(issue.recommendation).substring(0, 150)}${issue.recommendation.length > 150 ? '...' : ''}</p>` : ''}
            </div>`;
        });
        html += '</div></div>';
    }

    // === Audit Log Table ===
    html += `<div class="Polaris-Card"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Audit Log</h3></div>
        <div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x">
            <table class="Polaris-DataTable">
                <thead><tr><th>Category</th><th>Score</th><th>Status</th><th>Duration</th><th>Errors</th><th>Warnings</th></tr></thead>
                <tbody>`;
    auditData.categories.forEach(cat => {
        const label = CATEGORY_LABELS[cat.name] || cat.name;
        const s = cat.summary || {};
        const statusBadge = cat.status === 'error'
            ? '<span class="Polaris-Badge Polaris-Badge--warning">Error</span>'
            : '<span class="Polaris-Badge Polaris-Badge--success">OK</span>';
        html += `<tr>
            <td><button class="Polaris-Button--plain" data-category="${escapeHtml(cat.name)}" style="cursor:pointer;color:var(--p-color-text-interactive)">${escapeHtml(label)}</button></td>
            <td style="color:${scoreColorRaw(cat.score)};font-weight:var(--p-font-weight-semibold)">${cat.score}</td>
            <td>${statusBadge}</td>
            <td>${cat.duration_ms != null ? cat.duration_ms + 'ms' : '-'}</td>
            <td style="color:${(s.error_count || 0) > 0 ? 'var(--p-color-text-critical)' : ''}">${s.error_count || 0}</td>
            <td style="color:${(s.warning_count || 0) > 0 ? 'var(--p-color-text-warning)' : ''}">${s.warning_count || 0}</td>
        </tr>`;
    });
    html += '</tbody></table></div></div></div>';

    return html;
}


// ============================================================
// Render: Loading Skeletons
// ============================================================

function renderSidebarSkeleton() {
    let html = '<div class="sidebar-score"><div class="skeleton skeleton--circle" style="width:80px;height:80px"></div><div class="skeleton skeleton--text" style="width:80px;margin-top:8px"></div></div><div class="sidebar-nav">';
    for (let i = 0; i < 8; i++) {
        html += '<div class="skeleton skeleton--sidebar-item"></div>';
    }
    html += '</div>';
    return html;
}

function renderMainSkeleton() {
    return `<div class="skeleton-main">
        <div class="skeleton skeleton--text" style="width:200px;height:24px;margin-bottom:16px"></div>
        <div class="skeleton skeleton--bar" style="margin-bottom:24px"></div>
        <div class="kpi-grid">${'<div class="skeleton skeleton--card"></div>'.repeat(4)}</div>
    </div>`;
}


// ============================================================
// Render: PageSpeed Insights Panel
// ============================================================

function renderPageSpeedPanel(psiData) {
    if (!psiData) return '';

    let html = `<div class="category-header"><div class="category-header__title">
        <span class="category-header__icon" style="color:#005bd3">${CATEGORY_ICONS.pagespeed_insights}</span>
        <h2 class="Polaris-Text--headingLg">Performance Lab</h2>
    </div>
    ${psiData.duration_ms != null ? `<span class="Polaris-Text--bodySm Polaris-Text--subdued">${psiData.duration_ms}ms${psiData.cached ? ' (cached)' : ''}</span>` : ''}
    </div>`;

    if (psiData.status === 'error') {
        html += `<div class="Polaris-Banner Polaris-Banner--warning mb-400"><span>Error: ${escapeHtml(psiData.error_message || 'Unknown')}</span></div>`;
        return html;
    }

    // Dual score gauges
    html += '<div class="score-gauge-pair mb-400">';
    for (const [label, strategy] of [['Mobile', psiData.mobile], ['Desktop', psiData.desktop]]) {
        if (!strategy) continue;
        const s = strategy.score;
        const color = scoreColorRaw(s);
        const circumference = 213.6;
        const offset = circumference - (s / 100) * circumference;
        html += `<div class="score-gauge-mini">
            <svg width="100" height="100" viewBox="0 0 100 100">
                <circle class="bg-ring" cx="50" cy="50" r="34" fill="none" stroke-width="6"/>
                <circle cx="50" cy="50" r="34" fill="none" stroke-width="6"
                    stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" stroke-linecap="round"
                    style="stroke:${color};transform:rotate(-90deg);transform-origin:center;transition:stroke-dashoffset 1s ease"/>
            </svg>
            <div class="score-gauge-mini__value" style="color:${color}">${s}</div>
            <p class="Polaris-Text--bodySm Polaris-Text--subdued mt-100">${label}</p>
        </div>`;
    }
    html += '</div>';

    // KPI cards
    if (psiData.metrics) {
        html += '<div class="kpi-grid mb-400">';
        for (const [key, value] of Object.entries(psiData.metrics)) {
            if (value != null) html += renderKPICard(key, value);
        }
        html += '</div>';
    }

    // Opportunities
    for (const [label, strategy] of [['Mobile', psiData.mobile], ['Desktop', psiData.desktop]]) {
        if (!strategy || !strategy.opportunities || !strategy.opportunities.length) continue;
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">${label} Opportunities</h3></div>
            <div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Opportunity</th><th>Savings</th></tr></thead><tbody>`;
        strategy.opportunities.forEach(opp => {
            html += `<tr><td>${escapeHtml(opp.title)}</td><td style="text-align:right;white-space:nowrap">${opp.savings_ms != null ? opp.savings_ms + 'ms' : '-'}</td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }

    // Diagnostics
    for (const [label, strategy] of [['Mobile', psiData.mobile], ['Desktop', psiData.desktop]]) {
        if (!strategy || !strategy.diagnostics || !strategy.diagnostics.length) continue;
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">${label} Diagnostics</h3></div><div class="Polaris-Card__Section">`;
        strategy.diagnostics.forEach(d => {
            html += `<div class="issue-item"><span class="severity-icon severity-info">i</span><span>${escapeHtml(d.title)}</span></div>`;
        });
        html += '</div></div>';
    }

    // Issues
    if (psiData.issues && psiData.issues.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Issues</h3></div><div class="Polaris-Card__Section">`;
        psiData.issues.forEach(issue => {
            html += `<div class="issue-item">${severityIcon(issue.severity)}<div>
                <span>${escapeHtml(issue.message)}</span>
                ${issue.recommendation ? `<p class="Polaris-Text--bodySm Polaris-Text--subdued mt-100">${escapeHtml(issue.recommendation)}</p>` : ''}
            </div></div>`;
        });
        html += '</div></div>';
    }

    return html;
}


// ============================================================
// Render: Schema Validation Panel
// ============================================================

function renderSchemaValidationPanel(schemaData) {
    if (!schemaData) return '';

    let html = `<div class="category-header"><div class="category-header__title">
        <span class="category-header__icon" style="color:#005bd3">${CATEGORY_ICONS.schema_validation}</span>
        <h2 class="Polaris-Text--headingLg">Schema Validation</h2>
    </div>
    ${schemaData.duration_ms != null ? `<span class="Polaris-Text--bodySm Polaris-Text--subdued">${schemaData.duration_ms}ms</span>` : ''}
    </div>`;

    if (schemaData.status === 'error') {
        html += `<div class="Polaris-Banner Polaris-Banner--warning mb-400"><span>Error: ${escapeHtml(schemaData.error_message || 'Unknown')}</span></div>`;
    }

    // Metrics KPI cards
    if (schemaData.metrics) {
        html += '<div class="kpi-grid mb-400">';
        for (const [key, value] of Object.entries(schemaData.metrics)) {
            if (value != null) html += renderKPICard(key, value);
        }
        html += '</div>';
    }

    // Severity distribution
    if (schemaData.issues && schemaData.issues.length) {
        const counts = { error: 0, warning: 0, info: 0, pass: 0 };
        schemaData.issues.forEach(i => counts[i.severity]++);
        const total = schemaData.issues.length;
        html += `<div class="severity-bar-container mb-400">
            <p class="Polaris-Text--bodySm Polaris-Text--subdued mb-200">Issue Distribution</p>
            <div class="severity-bar">
                ${counts.error ? `<div class="severity-bar__segment severity-bar__segment--error" style="width:${(counts.error/total*100)}%"></div>` : ''}
                ${counts.warning ? `<div class="severity-bar__segment severity-bar__segment--warning" style="width:${(counts.warning/total*100)}%"></div>` : ''}
                ${counts.info ? `<div class="severity-bar__segment severity-bar__segment--info" style="width:${(counts.info/total*100)}%"></div>` : ''}
                ${counts.pass ? `<div class="severity-bar__segment severity-bar__segment--pass" style="width:${(counts.pass/total*100)}%"></div>` : ''}
            </div>
        </div>`;
    }

    // Entity list
    if (schemaData.entities && schemaData.entities.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Entities (${schemaData.entities.length})</h3></div><div class="Polaris-Card__Section"><div class="entity-card-grid">`;
        schemaData.entities.forEach(entity => {
            const badge = entity.valid
                ? '<span class="Polaris-Badge Polaris-Badge--success">Valid</span>'
                : '<span class="Polaris-Badge Polaris-Badge--critical">Invalid</span>';
            const sourceBadge = `<span class="Polaris-Badge Polaris-Badge--default">${escapeHtml(entity.source)}</span>`;
            html += `<div class="entity-card">
                <div style="display:flex;align-items:center;gap:var(--p-space-200);margin-bottom:var(--p-space-100)">
                    <strong class="Polaris-Text--bodyMd">${escapeHtml(entity.entity_type)}</strong>
                    ${badge} ${sourceBadge}
                </div>
                <p class="Polaris-Text--bodySm Polaris-Text--subdued">${entity.properties_found.length} properties</p>
            </div>`;
        });
        html += '</div></div></div>';
    }

    // Issues with evidence
    if (schemaData.issues && schemaData.issues.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Issues</h3></div><div class="Polaris-Card__Section">`;
        schemaData.issues.forEach(issue => {
            html += `<div class="issue-item">${severityIcon(issue.severity)}<div>
                <span>${escapeHtml(issue.message)}</span>
                ${issue.evidence ? `<div class="evidence-block mt-100" style="position:relative">${escapeHtml(issue.evidence)}<button class="copy-btn" title="Copy">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                </button></div>` : ''}
                ${issue.recommendation ? `<p class="Polaris-Text--bodySm Polaris-Text--subdued mt-100">${escapeHtml(issue.recommendation)}</p>` : ''}
            </div></div>`;
        });
        html += '</div></div>';
    }

    return html;
}


// ============================================================
// Render: Keyword Research Panel
// ============================================================

function renderKeywordPanel(keywordData) {
    if (!keywordData) return '';

    let html = `<div class="category-header"><div class="category-header__title">
        <span class="category-header__icon" style="color:#005bd3">${CATEGORY_ICONS.keyword_research}</span>
        <h2 class="Polaris-Text--headingLg">Keyword Research</h2>
    </div>
    ${keywordData.duration_ms != null ? `<span class="Polaris-Text--bodySm Polaris-Text--subdued">${keywordData.duration_ms}ms${keywordData.cached ? ' (cached)' : ''}</span>` : ''}
    </div>`;

    if (keywordData.status === 'not_configured') {
        html += `<div class="Polaris-Banner Polaris-Banner--info mb-400"><span>Google Ads API not configured. Set credentials to enable keyword suggestions.</span></div>`;
        return html;
    }

    if (keywordData.status === 'error') {
        html += `<div class="Polaris-Banner Polaris-Banner--warning mb-400"><span>Error: ${escapeHtml(keywordData.error_message || 'Unknown')}</span></div>`;
        return html;
    }

    // KPI cards
    if (keywordData.metrics_summary) {
        const ms = keywordData.metrics_summary;
        html += '<div class="kpi-grid mb-400">';
        html += renderIntelKPI('Total Ideas', String(ms.total_ideas || 0), 'Google Ads');
        html += renderIntelKPI('Avg Volume', ms.avg_volume != null ? ms.avg_volume.toLocaleString() : 'N/A', 'Google Ads');
        html += renderIntelKPI('Max Volume', ms.max_volume != null ? ms.max_volume.toLocaleString() : 'N/A', 'Google Ads');
        html += renderIntelKPI('Avg Competition', ms.avg_competition_index != null ? ms.avg_competition_index + '/100' : 'N/A', 'Google Ads');
        html += '</div>';
    }

    // Keyword table
    if (keywordData.ideas && keywordData.ideas.length) {
        // Sort ideas
        const kwSort = (typeof Store !== 'undefined' && Store.get('keywordSort')) || 'volume_desc';
        const sortedIdeas = [...keywordData.ideas];
        const [sortCol, sortDir] = kwSort.split('_');
        const dirMul = sortDir === 'asc' ? 1 : -1;
        sortedIdeas.sort((a, b) => {
            if (sortCol === 'keyword') return dirMul * (a.keyword || '').localeCompare(b.keyword || '');
            if (sortCol === 'volume') return dirMul * ((a.avg_monthly_searches || 0) - (b.avg_monthly_searches || 0));
            if (sortCol === 'competition') return dirMul * ((a.competition_index || 0) - (b.competition_index || 0));
            if (sortCol === 'cpc') return dirMul * ((a.high_cpc_micros || 0) - (b.high_cpc_micros || 0));
            return 0;
        });

        const arrow = (col) => {
            if (!kwSort.startsWith(col)) return '';
            return sortDir === 'asc' ? ' \u25B2' : ' \u25BC';
        };

        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Keyword Ideas (${keywordData.ideas.length})</h3></div>
            <div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable keyword-table">
            <thead><tr><th data-kw-sort="keyword">Keyword${arrow('keyword')}</th><th data-kw-sort="volume">Volume${arrow('volume')}</th><th data-kw-sort="competition">Competition${arrow('competition')}</th><th data-kw-sort="cpc">CPC Range${arrow('cpc')}</th></tr></thead><tbody>`;
        sortedIdeas.forEach(idea => {
            const lowCpc = idea.low_cpc_micros != null ? '$' + (idea.low_cpc_micros / 1000000).toFixed(2) : '-';
            const highCpc = idea.high_cpc_micros != null ? '$' + (idea.high_cpc_micros / 1000000).toFixed(2) : '-';
            html += `<tr>
                <td>${escapeHtml(idea.keyword)}</td>
                <td style="text-align:right">${idea.avg_monthly_searches != null ? idea.avg_monthly_searches.toLocaleString() : '-'}</td>
                <td style="text-align:center">${idea.competition || '-'} ${idea.competition_index != null ? `<span class="Polaris-Text--bodySm Polaris-Text--subdued">(${idea.competition_index})</span>` : ''}</td>
                <td style="text-align:right;white-space:nowrap">${lowCpc} - ${highCpc}</td>
            </tr>`;
        });
        html += '</tbody></table></div></div></div>';

        // Simple histogram (top 10 by volume)
        const sorted = [...keywordData.ideas].filter(i => i.avg_monthly_searches).sort((a, b) => b.avg_monthly_searches - a.avg_monthly_searches).slice(0, 10);
        if (sorted.length) {
            const maxVol = sorted[0].avg_monthly_searches;
            html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Top Keywords by Volume</h3></div><div class="Polaris-Card__Section">`;
            sorted.forEach(idea => {
                const pct = maxVol > 0 ? (idea.avg_monthly_searches / maxVol * 100) : 0;
                html += `<div class="keyword-bar-row">
                    <span class="keyword-bar-label">${escapeHtml(idea.keyword)}</span>
                    <div class="keyword-bar-track"><div class="keyword-bar-fill" style="width:${pct}%"></div></div>
                    <span class="keyword-bar-value">${idea.avg_monthly_searches.toLocaleString()}</span>
                </div>`;
            });
            html += '</div></div>';
        }
    }

    return html;
}


// ============================================================
// Multi-Brand Views
// ============================================================

function renderAppSidebar(state) {
    const view = state.currentView;
    const brand = state.selectedBrand;
    let html = '<nav class="app-nav">';

    html += `<a class="sidebar-item ${view === 'home' ? 'selected' : ''}" data-nav="home">
        <span class="sidebar-item__icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path d="M10 2L2 8v10h5v-5h6v5h5V8l-8-6z"/></svg></span>
        <span class="sidebar-item__label">Home</span>
    </a>`;

    html += `<a class="sidebar-item ${view === 'brands' ? 'selected' : ''}" data-nav="brands">
        <span class="sidebar-item__icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path d="M4 4h12v2H4V4zm0 5h12v2H4V9zm0 5h8v2H4v-2z"/></svg></span>
        <span class="sidebar-item__label">Brands</span>
    </a>`;

    if (brand) {
        html += '<div class="sidebar-divider"></div>';
        html += `<div class="sidebar-brand-name">${escapeHtml(brand.name)}</div>`;
        const subItems = [
            { id: 'brand-detail', label: 'Overview' },
            { id: 'brand-audits', label: 'Audits' },
            { id: 'audit-run', label: 'New Audit' },
            { id: 'reports', label: 'Reports' },
            { id: 'settings', label: 'Settings' },
        ];
        subItems.forEach(item => {
            html += `<a class="sidebar-item sidebar-item--sub ${view === item.id ? 'selected' : ''}" data-nav="${item.id}">
                <span class="sidebar-item__label">${item.label}</span>
            </a>`;
        });
    }

    html += '<div class="sidebar-divider"></div>';
    html += `<a class="sidebar-item ${view === 'quick-audit' ? 'selected' : ''}" data-nav="quick-audit">
        <span class="sidebar-item__icon"><svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path d="M10 2l8 5v6l-8 5-8-5V7l8-5z"/></svg></span>
        <span class="sidebar-item__label">Quick Audit</span>
    </a>`;

    html += '</nav>';
    return html;
}

function renderHomePage(state) {
    const brands = state.brands || [];
    const auditData = state.auditData;
    let html = '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">';
    html += '<h2 class="Polaris-Text--headingXl mb-200">Executive Summary</h2>';
    html += '<p class="Polaris-Text--bodySm Polaris-Text--subdued">Your SEO auditing dashboard. Select a brand or run a quick audit to get started.</p>';
    html += '</div></div>';

    if (brands.length) {
        html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Your Brands</h3></div><div class="Polaris-Card__Section"><div class="brand-card-grid">';
        brands.forEach(b => {
            const tone = b.latest_score != null ? scoreTone(b.latest_score) : 'default';
            const delta = (b.latest_score != null && b.previous_score != null) ? (b.latest_score - b.previous_score) : null;
            const deltaStr = delta != null ? (delta >= 0 ? `+${delta}` : `${delta}`) : '';
            const deltaClass = delta != null ? (delta >= 0 ? 'Polaris-Text--success' : 'Polaris-Text--critical') : '';
            html += `<div class="brand-card" data-brand-id="${escapeHtml(b.id)}">
                <div class="brand-card__header"><h4 class="Polaris-Text--headingSm">${escapeHtml(b.name)}</h4>
                    ${b.latest_score != null ? `<span class="Polaris-Badge Polaris-Badge--${tone}">${b.latest_score}</span>` : '<span class="Polaris-Badge Polaris-Badge--default">New</span>'}
                </div>
                <p class="Polaris-Text--bodySm Polaris-Text--subdued">${escapeHtml(b.primary_domain)}</p>
                <div class="brand-card__footer"><span>${b.audit_count || 0} audits</span>${deltaStr ? `<span class="${deltaClass}">${deltaStr} pts</span>` : ''}</div>
            </div>`;
        });
        html += '</div></div></div>';
    }

    if (auditData && auditData.executive_summary) {
        html += renderExecutiveSummarySection(auditData.executive_summary, auditData.overall_score);
    }

    html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">
        <div style="display:flex;gap:var(--p-space-300);flex-wrap:wrap">
            <button class="Polaris-Button Polaris-Button--primary" data-action="new-brand">+ New Brand</button>
            <button class="Polaris-Button Polaris-Button--default" data-nav="quick-audit">Quick Audit</button>
        </div>
    </div></div>`;
    return html;
}

function renderExecutiveSummarySection(summary, overallScore) {
    if (!summary) return '';
    let html = '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Quick Wins</h3></div><div class="Polaris-Card__Section">';
    if (summary.top_opportunities && summary.top_opportunities.length) {
        html += '<div class="quick-wins-grid">';
        summary.top_opportunities.slice(0, 6).forEach(opp => {
            const tone = opp.severity === 'error' ? 'critical' : (opp.severity === 'warning' ? 'warning' : 'info');
            html += `<div class="quick-win-card">
                <div class="quick-win-card__header"><span class="Polaris-Badge Polaris-Badge--${tone}">${escapeHtml(opp.severity)}</span>
                    <span class="Polaris-Text--bodySm Polaris-Text--subdued">${escapeHtml(opp.category)}</span></div>
                <p class="Polaris-Text--bodySm" style="margin:var(--p-space-100) 0">${escapeHtml(opp.issue)}</p>
                <p class="Polaris-Text--bodySm Polaris-Text--subdued">${escapeHtml(opp.recommendation)}</p>
            </div>`;
        });
        html += '</div>';
    }
    html += '</div></div>';

    if (summary.sales_narrative) {
        const sn = summary.sales_narrative;
        html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Growth Analysis</h3></div><div class="Polaris-Card__Section">';
        [
            { title: "What's Holding Growth Back", content: sn.whats_holding_growth_back, tone: 'critical' },
            { title: "Fix in 30 Days", content: sn.fix_in_30_days, tone: 'warning' },
            { title: "Fix Next Quarter", content: sn.fix_next_quarter, tone: 'info' },
            { title: "Expected Outcomes", content: sn.expected_outcomes, tone: 'success' },
        ].forEach(s => {
            if (!s.content) return;
            html += `<div class="narrative-section narrative-section--${s.tone}">
                <h4 class="Polaris-Text--headingSm">${escapeHtml(s.title)}</h4>
                <pre class="Polaris-Text--bodySm" style="white-space:pre-wrap;font-family:inherit;margin:var(--p-space-100) 0 var(--p-space-300)">${escapeHtml(s.content)}</pre>
            </div>`;
        });
        html += '</div></div>';
    }
    return html;
}

function renderBrandsList(brands) {
    let html = '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section" style="display:flex;justify-content:space-between;align-items:center">';
    html += '<h2 class="Polaris-Text--headingXl">Brands</h2>';
    html += '<button class="Polaris-Button Polaris-Button--primary" data-action="new-brand">+ New Brand</button>';
    html += '</div></div>';
    if (!brands.length) {
        return html + '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section text-center"><p class="Polaris-Text--bodySm Polaris-Text--subdued">No brands yet.</p></div></div>';
    }
    html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Brand</th><th>Domain</th><th>Industry</th><th>Score</th><th>Trend</th><th>Audits</th></tr></thead><tbody>';
    brands.forEach(b => {
        const delta = (b.latest_score != null && b.previous_score != null) ? (b.latest_score - b.previous_score) : null;
        const deltaStr = delta != null ? (delta >= 0 ? `+${delta}` : `${delta}`) : '-';
        const deltaClass = delta != null ? (delta >= 0 ? 'Polaris-Text--success' : 'Polaris-Text--critical') : '';
        html += `<tr class="brand-row" data-brand-id="${escapeHtml(b.id)}" style="cursor:pointer">
            <td><strong>${escapeHtml(b.name)}</strong></td><td>${escapeHtml(b.primary_domain)}</td>
            <td>${escapeHtml(b.industry || '-')}</td>
            <td>${b.latest_score != null ? `<span class="Polaris-Badge Polaris-Badge--${scoreTone(b.latest_score)}">${b.latest_score}</span>` : '-'}</td>
            <td><span class="${deltaClass}">${deltaStr}</span></td><td>${b.audit_count || 0}</td></tr>`;
    });
    html += '</tbody></table></div></div></div>';
    return html;
}

function renderBrandDetail(brand, audits) {
    if (!brand) return '<p>Brand not found</p>';
    let html = `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div><h2 class="Polaris-Text--headingXl">${escapeHtml(brand.name)}</h2>
                <p class="Polaris-Text--bodySm Polaris-Text--subdued">${escapeHtml(brand.primary_domain)}</p></div>
            <div>${brand.latest_score != null ? `<span class="Polaris-Badge Polaris-Badge--${scoreTone(brand.latest_score)}" style="font-size:1.2em;padding:6px 12px">${brand.latest_score}/100</span>` : ''}</div>
        </div>
    </div></div>`;
    html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Profile</h3></div><div class="Polaris-Card__Section"><div class="kpi-grid">';
    if (brand.industry) html += renderIntelKPI('Industry', brand.industry, '');
    if (brand.revenue_range) html += renderIntelKPI('Revenue', brand.revenue_range, 'Client provided');
    if (brand.persona) html += renderIntelKPI('Persona', brand.persona, '');
    html += renderIntelKPI('Audits', String(brand.audit_count || 0), '');
    html += '</div>';
    if (brand.description) html += `<p class="Polaris-Text--bodyMd mt-200">${escapeHtml(brand.description)}</p>`;
    html += '</div></div>';
    if (audits && audits.length) {
        html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Recent Audits</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Date</th><th>URL</th><th>Score</th><th>Change</th><th>Actions</th></tr></thead><tbody>';
        audits.slice(0, 5).forEach(a => {
            const date = a.created_at ? new Date(a.created_at).toLocaleDateString() : '-';
            const ds = a.score_delta != null ? (a.score_delta >= 0 ? `+${a.score_delta}` : `${a.score_delta}`) : '-';
            const dc = a.score_delta != null ? (a.score_delta >= 0 ? 'Polaris-Text--success' : 'Polaris-Text--critical') : '';
            html += `<tr><td>${date}</td><td class="break-all">${escapeHtml(a.audited_url)}</td><td><span class="Polaris-Badge Polaris-Badge--${scoreTone(a.overall_score)}">${a.overall_score}</span></td><td><span class="${dc}">${ds}</span></td><td><button class="Polaris-Button Polaris-Button--plain" data-view-audit="${escapeHtml(a.id)}">View</button> <button class="Polaris-Button Polaris-Button--plain" data-export-pdf="${escapeHtml(a.id)}">PDF</button></td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }
    return html;
}

function renderAuditHistoryTable(audits, brandName) {
    let html = `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section"><h2 class="Polaris-Text--headingXl">Audits${brandName ? ' - ' + escapeHtml(brandName) : ''}</h2></div></div>`;
    if (!audits || !audits.length) return html + '<div class="Polaris-Card"><div class="Polaris-Card__Section text-center"><p class="Polaris-Text--bodySm Polaris-Text--subdued">No audits yet.</p></div></div>';
    html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Date</th><th>URL</th><th>Score</th><th>Change</th><th>Duration</th><th>Actions</th></tr></thead><tbody>';
    audits.forEach(a => {
        const date = a.created_at ? new Date(a.created_at).toLocaleString() : '-';
        const ds = a.score_delta != null ? (a.score_delta >= 0 ? `+${a.score_delta}` : `${a.score_delta}`) : '-';
        const dc = a.score_delta != null ? (a.score_delta >= 0 ? 'Polaris-Text--success' : 'Polaris-Text--critical') : '';
        const dur = a.duration_ms ? `${(a.duration_ms / 1000).toFixed(1)}s` : '-';
        html += `<tr><td style="white-space:nowrap">${date}</td><td class="break-all">${escapeHtml(a.audited_url)}</td><td><span class="Polaris-Badge Polaris-Badge--${scoreTone(a.overall_score)}">${a.overall_score}</span></td><td><span class="${dc}">${ds}</span></td><td>${dur}</td><td><button class="Polaris-Button Polaris-Button--plain" data-view-audit="${escapeHtml(a.id)}">View</button> <button class="Polaris-Button Polaris-Button--plain" data-export-pdf="${escapeHtml(a.id)}">PDF</button></td></tr>`;
    });
    html += '</tbody></table></div></div></div>';
    return html;
}

function renderNewBrandForm() {
    return `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">
        <h2 class="Polaris-Text--headingXl mb-400">Create New Brand</h2>
        <p class="Polaris-Text--bodySm Polaris-Text--subdued mb-400">Just enter the domain — we'll auto-detect industry, description, and other details from the website.</p>
        <form id="brand-form" class="brand-form">
            <div class="form-field mb-300"><label class="Polaris-Text--bodyMd" for="brand-name">Brand Name *</label>
                <input type="text" id="brand-name" class="Polaris-TextField__Input" required placeholder="e.g. Acme Corp" /></div>
            <div class="form-field mb-300"><label class="Polaris-Text--bodyMd" for="brand-domain">Primary Domain *</label>
                <input type="text" id="brand-domain" class="Polaris-TextField__Input" required placeholder="e.g. acme.com" /></div>
            <button type="submit" class="Polaris-Button Polaris-Button--primary">Create Brand & Run Audit</button>
        </form></div></div>`;
}

function renderBrandSettings(brand) {
    if (!brand) return '';
    const theme = brand.theme_json || {};
    return `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">
        <h2 class="Polaris-Text--headingXl mb-400">Settings - ${escapeHtml(brand.name)}</h2>
        <form id="brand-update-form" class="brand-form">
            <div class="form-field mb-300"><label>Name</label><input type="text" id="edit-brand-name" class="Polaris-TextField__Input" value="${escapeHtml(brand.name || '')}" /></div>
            <div class="form-field mb-300"><label>Industry</label><input type="text" id="edit-brand-industry" class="Polaris-TextField__Input" value="${escapeHtml(brand.industry || '')}" /></div>
            <div class="form-field mb-300"><label>Description</label><textarea id="edit-brand-description" class="Polaris-TextField__Input" rows="3">${escapeHtml(brand.description || '')}</textarea></div>
            <div class="form-field mb-300"><label>Persona</label><input type="text" id="edit-brand-persona" class="Polaris-TextField__Input" value="${escapeHtml(brand.persona || '')}" /></div>
            <div class="form-field mb-300"><label>Revenue</label><select id="edit-brand-revenue" class="Polaris-TextField__Input"><option value="">Select...</option>${['<$1M','$1-5M','$5-20M','$20-100M','$100M+'].map(v=>`<option value="${v}" ${brand.revenue_range===v?'selected':''}>${v}</option>`).join('')}</select></div>
            <button type="submit" class="Polaris-Button Polaris-Button--primary">Save Profile</button>
        </form>
    </div></div>
    <div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Report Theme</h3></div><div class="Polaris-Card__Section">
        <div class="form-field mb-300"><label>Logo</label><input type="file" id="logo-upload" accept="image/png,image/jpeg,image/svg+xml,image/webp" />
            ${brand.logo_path ? `<p class="Polaris-Text--bodySm Polaris-Text--success mt-100">Current: ${escapeHtml(brand.logo_path)}</p>` : ''}</div>
        <div class="form-field mb-300"><label>Primary Color</label><input type="color" id="theme-primary-color" value="${escapeHtml(theme.primary_color || '#a58464')}" /></div>
        <div class="form-field mb-300"><label>Background Color</label><input type="color" id="theme-bg-color" value="${escapeHtml(theme.bg_color || '#faf9f7')}" /></div>
        <div class="form-field mb-300"><label>Background Image</label><input type="file" id="bg-upload" accept="image/png,image/jpeg,image/webp" />
            ${theme.bg_image_path ? `<p class="Polaris-Text--bodySm Polaris-Text--success mt-100">Current: ${escapeHtml(theme.bg_image_path)}</p>` : ''}</div>
        <button class="Polaris-Button Polaris-Button--primary" id="save-theme-btn">Save Theme</button>
    </div></div>`;
}

function renderReportsPage(brand, audits) {
    if (!brand) return '';
    let html = `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section"><h2 class="Polaris-Text--headingXl mb-200">Reports - ${escapeHtml(brand.name)}</h2><p class="Polaris-Text--bodySm Polaris-Text--subdued">Generate branded PDF reports.</p></div></div>`;
    if (!audits || !audits.length) return html + '<div class="Polaris-Card"><div class="Polaris-Card__Section text-center"><p class="Polaris-Text--bodySm Polaris-Text--subdued">Run an audit first.</p></div></div>';
    html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Date</th><th>URL</th><th>Score</th><th></th></tr></thead><tbody>';
    audits.forEach(a => {
        const date = a.created_at ? new Date(a.created_at).toLocaleDateString() : '-';
        html += `<tr><td>${date}</td><td class="break-all">${escapeHtml(a.audited_url)}</td><td><span class="Polaris-Badge Polaris-Badge--${scoreTone(a.overall_score)}">${a.overall_score}</span></td><td><button class="Polaris-Button Polaris-Button--primary" data-export-pdf="${escapeHtml(a.id)}">Generate PDF</button></td></tr>`;
    });
    html += '</tbody></table></div></div></div>';
    return html;
}

function renderQuickAuditForm() {
    return `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">
        <h2 class="Polaris-Text--headingXl mb-400">Quick Audit</h2>
        <p class="Polaris-Text--bodySm Polaris-Text--subdued mb-300">Run a one-off audit without saving to a brand.</p>
        <form id="quick-audit-form" class="brand-form">
            <div class="form-field mb-300"><label for="qa-url">URL *</label><input type="url" id="qa-url" class="Polaris-TextField__Input" required placeholder="https://example.com" /></div>
            <div style="display:flex;gap:var(--p-space-400);flex-wrap:wrap;margin-bottom:var(--p-space-300)">
                <label class="Polaris-Checkbox"><input type="checkbox" id="qa-crawl" /><span class="Polaris-Checkbox__Input"></span> Crawl</label>
                <label class="Polaris-Checkbox"><input type="checkbox" id="qa-psi" /><span class="Polaris-Checkbox__Input"></span> PageSpeed</label>
                <label class="Polaris-Checkbox"><input type="checkbox" id="qa-schema" /><span class="Polaris-Checkbox__Input"></span> Schema</label>
                <label class="Polaris-Checkbox"><input type="checkbox" id="qa-intel" /><span class="Polaris-Checkbox__Input"></span> Intel</label>
            </div>
            <button type="submit" class="Polaris-Button Polaris-Button--primary">Run Audit</button>
        </form></div></div>`;
}

function renderBrandAuditForm(brand) {
    if (!brand) return '';
    return `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section">
        <h2 class="Polaris-Text--headingXl mb-400">New Audit - ${escapeHtml(brand.name)}</h2>
        <form id="brand-audit-form" class="brand-form">
            <div class="form-field mb-300"><label for="ba-url">URL *</label><input type="url" id="ba-url" class="Polaris-TextField__Input" required value="https://${escapeHtml(brand.primary_domain)}" /></div>
            <div style="display:flex;gap:var(--p-space-400);flex-wrap:wrap;margin-bottom:var(--p-space-300)">
                <label class="Polaris-Checkbox"><input type="checkbox" id="ba-crawl" /><span class="Polaris-Checkbox__Input"></span> Crawl</label>
                <label class="Polaris-Checkbox"><input type="checkbox" id="ba-psi" /><span class="Polaris-Checkbox__Input"></span> PageSpeed</label>
                <label class="Polaris-Checkbox"><input type="checkbox" id="ba-schema" /><span class="Polaris-Checkbox__Input"></span> Schema</label>
                <label class="Polaris-Checkbox"><input type="checkbox" id="ba-intel" /><span class="Polaris-Checkbox__Input"></span> Intel</label>
            </div>
            <p class="Polaris-Text--bodySm Polaris-Text--subdued mb-300">Results saved to ${escapeHtml(brand.name)}'s history.</p>
            <button type="submit" class="Polaris-Button Polaris-Button--primary">Run & Save Audit</button>
        </form></div></div>`;
}

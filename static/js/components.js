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
};


// ============================================================
// Render: Sidebar
// ============================================================

function renderSidebar(categories, selected, auditData) {
    if (!categories || !categories.length) return '';

    const overallScore = auditData ? auditData.overall_score : 0;
    const overallTone = scoreTone(overallScore);
    const overallColor = scoreColorRaw(overallScore);

    let html = `
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

function renderOverviewPanel(auditData) {
    if (!auditData) return '';

    const score = auditData.overall_score;
    const color = scoreColorRaw(score);
    const tone = scoreTone(score);

    // Score gauge
    let html = `
        <div class="overview-score-section">
            <div class="score-gauge">
                <svg width="160" height="160" viewBox="0 0 160 160">
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
            <p class="Polaris-Text--bodySm Polaris-Text--subdued mt-200">${escapeHtml(auditData.url)}</p>
        </div>`;

    // Top errors across all categories
    const allErrors = [];
    auditData.categories.forEach(cat => {
        (cat.issues || []).forEach(issue => {
            if (issue.severity === 'error') {
                allErrors.push({ category: CATEGORY_LABELS[cat.name] || cat.name, ...issue });
            }
        });
    });

    if (allErrors.length) {
        html += `<div class="Polaris-Card mt-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm Polaris-Text--critical">Top Errors (${allErrors.length})</h3></div><div class="Polaris-Card__Section">`;
        allErrors.slice(0, 10).forEach(err => {
            html += `<div class="issue-item">
                ${severityIcon('error')}
                <div>
                    <span class="Polaris-Text--bodySm" style="font-weight:var(--p-font-weight-medium)">${escapeHtml(err.category)}</span>
                    <span class="Polaris-Text--bodySm" style="margin-left:var(--p-space-100)">${escapeHtml(err.message)}</span>
                </div>
            </div>`;
        });
        html += '</div></div>';
    }

    // Audit log with durations
    html += `<div class="Polaris-Card mt-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Audit Log</h3></div>
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

/* ============================================================
   SEO Auditor — Shopify Polaris-styled Dashboard
   ============================================================ */

// --- API base URL ---
// When hosted on Netlify, API calls go to the Render backend.
// When running locally, calls go to the same origin.
const API_BASE = window.location.hostname.includes('netlify.app')
    ? 'https://seo-auditor-api.onrender.com'
    : '';

// --- DOM refs ---
const form = document.getElementById('audit-form');
const urlInput = document.getElementById('url-input');
const auditBtn = document.getElementById('audit-btn');
const errorMsg = document.getElementById('error-msg');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const categoriesGrid = document.getElementById('categories-grid');
const downloadPdfBtn = document.getElementById('download-pdf-btn');
const includeExternalCb = document.getElementById('include-external');
const includeCrawlCb = document.getElementById('include-crawl');
const crawlMaxPages = document.getElementById('crawl-max-pages');
const crawlPagesWrapper = document.getElementById('crawl-pages-wrapper');
const intelTabBtn = document.getElementById('intel-tab-btn');
const crawlTabBtn = document.getElementById('crawl-tab-btn');
const crawlResultsContent = document.getElementById('crawl-results-content');

window._lastAuditData = null;

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
    ads_quality: 'Ads Landing Page Quality',
    serp_features: 'SERP Feature Eligibility',
    accessibility: 'Accessibility (WAVE)',
    crawl: 'Site Crawl Analysis',
};

const CATEGORY_ICONS = {
    meta_tags: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"/></svg>',
    headings: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h8m-8 6h16"/></svg>',
    images: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
    links: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>',
    performance: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
    mobile: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>',
    structured_data: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
    sitemap: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 20l-5.447-2.724A2 2 0 013 15.382V5.618a2 2 0 011.553-1.894L9 2m0 18l6-3m-6 3V2m6 15l5.447-2.724A2 2 0 0021 12.382V5.618a2 2 0 00-1.553-1.894L15 2m0 15V2m0 0L9 2"/></svg>',
    robots: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>',
    tracking: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>',
    semantic: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>',
    ads_quality: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/><path stroke-linecap="round" stroke-linejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/></svg>',
    serp_features: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>',
    accessibility: '<svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
};


// --- Polaris score colors ---
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


// --- Helpers ---
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function severityIcon(severity) {
    const symbols = { error: '!', warning: '!', info: 'i', pass: '\u2713' };
    return `<span class="severity-icon severity-${severity}">${symbols[severity]}</span>`;
}


// --- Tab switching ---
function switchTab(btn, tabId) {
    document.querySelectorAll('.Polaris-Tabs__Tab').forEach(t => t.classList.remove('Polaris-Tabs__Tab--selected'));
    btn.classList.add('Polaris-Tabs__Tab--selected');
    document.getElementById('seo-tab').classList.add('hidden');
    document.getElementById('crawl-tab').classList.add('hidden');
    document.getElementById('intel-tab').classList.add('hidden');
    document.getElementById(tabId).classList.remove('hidden');
}


// --- Score ring ---
function renderOverallScore(score) {
    const ring = document.getElementById('score-ring');
    const circumference = 2 * Math.PI * 68; // ~427
    const offset = circumference - (score / 100) * circumference;
    ring.style.strokeDasharray = circumference;
    ring.style.strokeDashoffset = circumference;
    ring.style.stroke = scoreColorRaw(score);

    requestAnimationFrame(() => {
        setTimeout(() => { ring.style.strokeDashoffset = offset; }, 80);
    });

    const el = document.getElementById('overall-score');
    let current = 0;
    const step = Math.max(1, Math.floor(score / 40));
    const interval = setInterval(() => {
        current += step;
        if (current >= score) { current = score; clearInterval(interval); }
        el.textContent = current;
        el.style.color = scoreColorRaw(current);
    }, 25);
}


// --- Category card ---
function renderCategory(cat) {
    const label = CATEGORY_LABELS[cat.name] || cat.name;
    const icon = CATEGORY_ICONS[cat.name] || '';
    const color = scoreColor(cat.score);
    const rawColor = scoreColorRaw(cat.score);
    const tone = scoreTone(cat.score);
    const id = `cat-${cat.name}`;

    const issuesHtml = cat.issues.map(issue =>
        `<div class="issue-item">${severityIcon(issue.severity)}<span>${escapeHtml(issue.message)}</span></div>`
    ).join('');

    const errorCount = cat.issues.filter(i => i.severity === 'error').length;
    const warnCount = cat.issues.filter(i => i.severity === 'warning').length;

    let badges = '';
    if (errorCount) badges += `<span class="Polaris-Badge Polaris-Badge--critical">${errorCount} error${errorCount > 1 ? 's' : ''}</span> `;
    if (warnCount) badges += `<span class="Polaris-Badge Polaris-Badge--warning">${warnCount} warning${warnCount > 1 ? 's' : ''}</span>`;
    if (!errorCount && !warnCount) badges = '<span class="Polaris-Badge Polaris-Badge--success">All clear</span>';

    return `
        <div class="category-card">
            <button onclick="toggleIssues('${id}')" class="category-card__button">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--p-space-300)">
                    <div style="display:flex;align-items:center;gap:var(--p-space-200)">
                        <span style="color:${rawColor}">${icon}</span>
                        <span class="Polaris-Text--headingSm">${label}</span>
                    </div>
                    <span class="Polaris-Text--headingMd" style="color:${rawColor}">${cat.score}</span>
                </div>
                <div class="Polaris-ProgressBar mb-200">
                    <div class="Polaris-ProgressBar__Fill Polaris-ProgressBar__Fill--${tone}" style="width:${cat.score}%"></div>
                </div>
                <div style="display:flex;align-items:center;gap:var(--p-space-100)">${badges}</div>
            </button>
            <div id="${id}" class="issues-list px-500">
                ${issuesHtml}
            </div>
        </div>`;
}

function toggleIssues(id) {
    document.getElementById(id).classList.toggle('open');
}


// --- Crawl results ---
function renderCrawlResults(data) {
    const rawColor = scoreColorRaw(data.score);
    const tone = scoreTone(data.score);
    let html = `
        <div class="Polaris-Card mb-400">
            <div class="Polaris-Card__Section text-center">
                <h2 class="Polaris-Text--headingLg mb-200">Site Crawl Results</h2>
                <p class="Polaris-Text--bodySm Polaris-Text--subdued mb-300">${escapeHtml(data.url)}</p>
                <div class="mb-200">
                    <span class="Polaris-Text--headingXl" style="color:${rawColor}">${data.score}</span>
                    <span class="Polaris-Text--bodySm Polaris-Text--subdued"> / 100</span>
                </div>
                <p class="Polaris-Text--bodySm Polaris-Text--subdued">${data.pages_crawled} pages crawled, max depth ${data.max_depth}</p>
            </div>
        </div>`;

    if (data.issues && data.issues.length) {
        html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Crawl Issues</h3></div><div class="Polaris-Card__Section">';
        data.issues.forEach(issue => {
            html += `<div class="issue-item">${severityIcon(issue.severity)}<span>${escapeHtml(issue.message)}</span></div>`;
        });
        html += '</div></div>';
    }

    if (data.broken_links && data.broken_links.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm Polaris-Text--critical">Broken Links (${data.broken_links.length})</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Target URL</th><th>Status</th><th>Source</th></tr></thead><tbody>`;
        data.broken_links.forEach(bl => {
            html += `<tr><td class="break-all">${escapeHtml(bl.target_url)}</td><td style="color:var(--p-color-text-critical)">${bl.status_code || 'Timeout'}</td><td class="break-all" style="color:var(--p-color-text-secondary)">${escapeHtml(bl.source_url)}</td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }

    if (data.duplicate_titles && data.duplicate_titles.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm Polaris-Text--warning">Duplicate Titles (${data.duplicate_titles.length})</h3></div><div class="Polaris-Card__Section">`;
        data.duplicate_titles.forEach(dt => {
            html += `<div class="mb-300"><p class="Polaris-Text--bodyMd" style="font-weight:var(--p-font-weight-medium)">"${escapeHtml(dt.value)}"</p>`;
            dt.pages.forEach(p => { html += `<p class="Polaris-Text--bodySm Polaris-Text--subdued" style="margin-left:var(--p-space-300)">- ${escapeHtml(p)}</p>`; });
            html += '</div>';
        });
        html += '</div></div>';
    }

    if (data.duplicate_descriptions && data.duplicate_descriptions.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm Polaris-Text--warning">Duplicate Descriptions (${data.duplicate_descriptions.length})</h3></div><div class="Polaris-Card__Section">`;
        data.duplicate_descriptions.forEach(dd => {
            html += `<div class="mb-300"><p class="Polaris-Text--bodyMd" style="font-weight:var(--p-font-weight-medium)">"${escapeHtml(dd.value.substring(0, 80))}..."</p>`;
            dd.pages.forEach(p => { html += `<p class="Polaris-Text--bodySm Polaris-Text--subdued" style="margin-left:var(--p-space-300)">- ${escapeHtml(p)}</p>`; });
            html += '</div>';
        });
        html += '</div></div>';
    }

    if (data.orphan_pages && data.orphan_pages.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm Polaris-Text--warning">Orphan Pages (${data.orphan_pages.length})</h3></div><div class="Polaris-Card__Section">`;
        data.orphan_pages.forEach(p => {
            html += `<p class="Polaris-Text--bodySm Polaris-Text--subdued">- ${escapeHtml(p)}</p>`;
        });
        html += '</div></div>';
    }

    if (data.pages && data.pages.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Pages Crawled (${data.pages.length})</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>URL</th><th>Title</th><th>Links</th><th>Depth</th></tr></thead><tbody>`;
        data.pages.forEach(p => {
            html += `<tr><td class="break-all">${escapeHtml(p.url)}</td><td style="color:var(--p-color-text-secondary)">${escapeHtml(p.title || '(none)')}</td><td>${p.internal_links}</td><td>${p.depth}</td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }

    return html;
}


// ============================================================
// External Intelligence Rendering
// ============================================================

function renderExternalInsights(insights) {
    const sw = insights.similarweb;
    const sr = insights.semrush;

    renderKPICards(sw, sr);
    renderChannelChart(sw);
    renderCountryChart(sw);
    renderKeywordChart(sr);
    renderKeywordsTable(sr);
    renderBacklinksTable(sr);
    renderCompetitorsTable(sw, sr);
}

function kpiCard(label, value, sublabel) {
    return `<div class="kpi-card">
        <p class="kpi-card__label">${escapeHtml(label)}</p>
        <p class="kpi-card__value">${escapeHtml(value)}</p>
        ${sublabel ? `<p class="kpi-card__source">${escapeHtml(sublabel)}</p>` : ''}
    </div>`;
}

function renderKPICards(sw, sr) {
    const el = document.getElementById('intel-kpi-cards');
    const cards = [];

    if (sw && sw.status === 'ok') {
        cards.push(kpiCard('Monthly Visits', sw.estimated_monthly_visits?.display || 'N/A', 'Similarweb'));
        cards.push(kpiCard('Bounce Rate', sw.bounce_rate?.display || 'N/A', 'Similarweb'));
        cards.push(kpiCard('Avg Duration', sw.visit_duration?.display || 'N/A', 'Similarweb'));
    } else if (sw) {
        cards.push(kpiCard('Traffic Data', sw.status === 'not_configured' ? 'No API Key' : 'Error', 'Similarweb'));
    }

    if (sr && sr.status === 'ok') {
        cards.push(kpiCard('Organic Keywords', (sr.organic_keywords?.length || 0).toString(), 'SEMrush'));
        cards.push(kpiCard('Ref. Domains', sr.backlink_summary?.referring_domains?.toLocaleString() || 'N/A', 'SEMrush'));
    } else if (sr) {
        cards.push(kpiCard('Search Data', sr.status === 'not_configured' ? 'No API Key' : 'Error', 'SEMrush'));
    }

    el.innerHTML = cards.join('');
}

function renderBarChart(container, items, labelKey, valueKey, maxVal, colorFn) {
    if (!items || !items.length) {
        container.innerHTML = `<div class="Polaris-Banner Polaris-Banner--info"><span class="Polaris-Text--bodySm">No data available</span></div>`;
        return;
    }
    const max = maxVal || Math.max(...items.map(i => i[valueKey] || 0));
    let html = '';
    items.forEach(item => {
        const val = item[valueKey] || 0;
        const pct = max > 0 ? (val / max) * 100 : 0;
        const label = item[labelKey] || '';
        const color = colorFn ? colorFn(label) : '#005bd3';
        const displayVal = typeof val === 'number' && val <= 1 ? (val * 100).toFixed(1) + '%' : val;
        html += `<div class="bar-chart__row">
            <div class="bar-chart__header">
                <span class="bar-chart__label">${escapeHtml(label)}</span>
                <span class="bar-chart__value">${displayVal}</span>
            </div>
            <div class="Polaris-ProgressBar">
                <div class="Polaris-ProgressBar__Fill" style="width:${pct}%;background:${color}"></div>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

const CHANNEL_COLORS = {
    direct: '#005bd3',
    search: '#008060',
    social: '#b98900',
    referrals: '#7c3aed',
    email: '#d72c0d',
    display: '#0073b0',
};

function renderChannelChart(sw) {
    const el = document.getElementById('chart-channels');
    if (!sw || sw.status !== 'ok' || !sw.traffic_channels?.length) {
        el.innerHTML = `<div class="Polaris-Banner Polaris-Banner--info"><span class="Polaris-Text--bodySm">${sw?.status === 'not_configured' ? 'Similarweb API key not configured' : 'No data'}</span></div>`;
        return;
    }
    renderBarChart(el, sw.traffic_channels, 'channel', 'share', 1, c => CHANNEL_COLORS[c] || '#005bd3');
}

function renderCountryChart(sw) {
    const el = document.getElementById('chart-countries');
    if (!sw || sw.status !== 'ok' || !sw.top_countries?.length) {
        el.innerHTML = `<div class="Polaris-Banner Polaris-Banner--info"><span class="Polaris-Text--bodySm">${sw?.status === 'not_configured' ? 'Similarweb API key not configured' : 'No data'}</span></div>`;
        return;
    }
    renderBarChart(el, sw.top_countries.slice(0, 8), 'country', 'share', 1, () => '#7c3aed');
}

function renderKeywordChart(sr) {
    const el = document.getElementById('chart-keywords');
    if (!sr || sr.status !== 'ok' || !sr.keyword_distribution?.length) {
        el.innerHTML = `<div class="Polaris-Banner Polaris-Banner--info"><span class="Polaris-Text--bodySm">${sr?.status === 'not_configured' ? 'SEMrush API key not configured' : 'No data'}</span></div>`;
        return;
    }
    const maxCount = Math.max(...sr.keyword_distribution.map(b => b.count));
    renderBarChart(el, sr.keyword_distribution, 'range', 'count', maxCount, () => '#008060');
}

function renderKeywordsTable(sr) {
    const wrapper = document.getElementById('intel-keywords-table');
    const body = document.getElementById('keywords-table-body');
    if (!sr || sr.status !== 'ok' || !sr.organic_keywords?.length) {
        wrapper.classList.add('hidden');
        return;
    }
    wrapper.classList.remove('hidden');
    let html = '<table class="Polaris-DataTable"><thead><tr><th>Keyword</th><th>Pos</th><th>Volume</th></tr></thead><tbody>';
    sr.organic_keywords.slice(0, 15).forEach(kw => {
        html += `<tr>
            <td>${escapeHtml(kw.keyword)}</td>
            <td style="text-align:center">${kw.position ?? '-'}</td>
            <td style="text-align:right;font-variant-numeric:tabular-nums">${kw.volume?.toLocaleString() ?? '-'}</td>
        </tr>`;
    });
    html += '</tbody></table>';
    body.innerHTML = html;
}

function renderBacklinksTable(sr) {
    const wrapper = document.getElementById('intel-backlinks-table');
    const body = document.getElementById('backlinks-table-body');
    if (!sr || sr.status !== 'ok' || !sr.top_backlinks?.length) {
        wrapper.classList.add('hidden');
        return;
    }
    wrapper.classList.remove('hidden');
    let html = '<table class="Polaris-DataTable"><thead><tr><th>Source</th><th>Anchor</th></tr></thead><tbody>';
    sr.top_backlinks.slice(0, 10).forEach(bl => {
        html += `<tr>
            <td class="break-all" style="font-size:var(--p-font-size-300)">${escapeHtml(bl.source_url)}</td>
            <td style="font-size:var(--p-font-size-300)">${escapeHtml(bl.anchor || '-')}</td>
        </tr>`;
    });
    html += '</tbody></table>';
    body.innerHTML = html;
}

function renderCompetitorsTable(sw, sr) {
    const wrapper = document.getElementById('intel-competitors-table');
    const body = document.getElementById('competitors-table-body');
    const competitors = [];

    if (sw?.status === 'ok' && sw.similar_sites?.length) {
        sw.similar_sites.forEach(s => competitors.push({ domain: s.domain, source: 'Similarweb' }));
    }
    if (sr?.status === 'ok' && sr.organic_competitors?.length) {
        sr.organic_competitors.forEach(s => competitors.push({ domain: s.domain, source: 'SEMrush' }));
    }

    if (!competitors.length) {
        wrapper.classList.add('hidden');
        return;
    }
    wrapper.classList.remove('hidden');
    let html = '';
    competitors.slice(0, 10).forEach(c => {
        html += `<div style="display:flex;justify-content:space-between;padding:var(--p-space-200) 0;border-bottom:1px solid var(--p-color-border-secondary)">
            <span class="Polaris-Text--bodyMd">${escapeHtml(c.domain)}</span>
            <span class="Polaris-Badge Polaris-Badge--default">${c.source}</span>
        </div>`;
    });
    body.innerHTML = html;
}


// ============================================================
// Event Listeners
// ============================================================

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    errorMsg.classList.add('hidden');
    results.classList.add('hidden');
    loading.classList.remove('hidden');
    auditBtn.disabled = true;
    auditBtn.classList.add('disabled');

    try {
        const body = { url };

        if (includeCrawlCb.checked) {
            body.include_crawl = true;
            body.crawl_max_pages = parseInt(crawlMaxPages.value, 10) || 10;
        }

        if (includeExternalCb.checked) {
            body.include_external = true;
            body.external_modules = ['similarweb', 'semrush'];
        }

        const resp = await fetch(API_BASE + '/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.detail || `Server error (${resp.status})`);
        }

        const data = await resp.json();
        window._lastAuditData = data;

        // Render SEO results
        document.getElementById('audited-url').textContent = data.url;
        categoriesGrid.innerHTML = data.categories.map(renderCategory).join('');
        renderOverallScore(data.overall_score);

        // Show/hide crawl tab
        if (data.crawl_results) {
            crawlTabBtn.style.display = '';
            crawlResultsContent.innerHTML = renderCrawlResults(data.crawl_results);
        } else {
            crawlTabBtn.style.display = 'none';
            crawlResultsContent.innerHTML = '';
        }

        // Show/hide intel tab
        if (data.external_insights) {
            intelTabBtn.style.display = '';
            renderExternalInsights(data.external_insights);
        } else {
            intelTabBtn.style.display = 'none';
        }

        // Reset to SEO tab
        const seoTabBtn = document.querySelector('[data-tab="seo-tab"]');
        switchTab(seoTabBtn, 'seo-tab');

        loading.classList.add('hidden');
        results.classList.remove('hidden');
    } catch (err) {
        loading.classList.add('hidden');
        errorMsg.textContent = err.message;
        errorMsg.classList.remove('hidden');
    } finally {
        auditBtn.disabled = false;
        auditBtn.classList.remove('disabled');
    }
});

// Toggle crawl max-pages visibility
includeCrawlCb.addEventListener('change', () => {
    crawlPagesWrapper.style.display = includeCrawlCb.checked ? 'flex' : 'none';
});

downloadPdfBtn.addEventListener('click', async () => {
    if (!window._lastAuditData) return;

    downloadPdfBtn.disabled = true;
    const origText = downloadPdfBtn.innerHTML;
    downloadPdfBtn.innerHTML = '<div class="Polaris-Spinner" style="width:20px;height:20px;border-width:2px"></div> Generating...';

    try {
        const resp = await fetch(API_BASE + '/api/report/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(window._lastAuditData),
        });

        if (!resp.ok) throw new Error('PDF generation failed');

        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'seo-audit-report.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert('Failed to generate PDF: ' + err.message);
    } finally {
        downloadPdfBtn.innerHTML = origText;
        downloadPdfBtn.disabled = false;
    }
});

// Hide optional tabs by default until results arrive
crawlTabBtn.style.display = 'none';
intelTabBtn.style.display = 'none';

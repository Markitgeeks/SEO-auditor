/* ============================================================
   SEO Auditor — Controller (Shopify Admin Panel Style)
   ============================================================ */

// --- API base URL ---
const API_BASE = window.location.hostname.includes('netlify.app')
    ? 'https://seo-auditor-api.onrender.com'
    : '';

// --- DOM refs ---
const $form = document.getElementById('audit-form');
const $urlInput = document.getElementById('url-input');
const $auditBtn = document.getElementById('audit-btn');
const $errorMsg = document.getElementById('error-msg');
const $appLayout = document.querySelector('.app-layout');
const $sidebar = document.getElementById('app-sidebar');
const $sidebarContent = document.getElementById('sidebar-content');
const $sidebarOverlay = document.getElementById('sidebar-overlay');
const $mainContent = document.getElementById('main-content');
const $welcomeState = document.getElementById('welcome-state');
const $loadingState = document.getElementById('loading-state');
const $mainSkeleton = document.getElementById('main-skeleton');
const $downloadPdfBtn = document.getElementById('download-pdf-btn');
const $hamburgerBtn = document.getElementById('hamburger-btn');
const $includeCrawlCb = document.getElementById('include-crawl');
const $includeExternalCb = document.getElementById('include-external');
const $crawlMaxPages = document.getElementById('crawl-max-pages');
const $crawlPagesWrapper = document.getElementById('crawl-pages-wrapper');

window._lastAuditData = null;


// ============================================================
// Store Subscriptions — Targeted Re-renders
// ============================================================

Store.subscribe((changed, state) => {
    // Sidebar re-render
    if (changed.some(k => ['auditData', 'selectedCategory'].includes(k))) {
        renderSidebarView(state);
    }

    // Main content re-render
    if (changed.some(k => ['auditData', 'selectedCategory', 'activeTab', 'issueFilter', 'issueSort', 'issuePage', 'issueSearch'].includes(k))) {
        renderMainView(state);
    }

    // Loading state
    if (changed.includes('isLoading')) {
        if (state.isLoading) {
            $welcomeState.classList.add('hidden');
            $mainContent.classList.add('hidden');
            $loadingState.classList.remove('hidden');
            $appLayout.classList.add('has-results');
            $sidebarContent.innerHTML = renderSidebarSkeleton();
            $mainSkeleton.innerHTML = renderMainSkeleton();
        } else {
            $loadingState.classList.add('hidden');
            if (!state.auditData) {
                $appLayout.classList.remove('has-results');
            }
        }
    }

    // Error
    if (changed.includes('error')) {
        if (state.error) {
            $errorMsg.textContent = state.error;
            $errorMsg.classList.remove('hidden');
        } else {
            $errorMsg.classList.add('hidden');
        }
    }

    // Sidebar mobile toggle
    if (changed.includes('sidebarOpen')) {
        $sidebar.classList.toggle('open', state.sidebarOpen);
        $sidebarOverlay.classList.toggle('open', state.sidebarOpen);
    }

    // PDF button + layout toggle
    if (changed.includes('auditData')) {
        $downloadPdfBtn.classList.toggle('hidden', !state.auditData);
        $appLayout.classList.toggle('has-results', !!state.auditData);
    }
});


// ============================================================
// Render: Sidebar
// ============================================================

function renderSidebarView(state) {
    if (!state.auditData) return;
    $sidebarContent.innerHTML = renderSidebar(
        state.auditData.categories,
        state.selectedCategory,
        state.auditData
    );
}


// ============================================================
// Render: Main Panel
// ============================================================

function renderMainView(state) {
    if (!state.auditData) return;

    $welcomeState.classList.add('hidden');
    $mainContent.classList.remove('hidden');

    const selected = state.selectedCategory;

    if (selected === 'overview') {
        $mainContent.innerHTML = renderOverviewPanel(state.auditData);
        bindOverviewLinks();
        return;
    }

    if (selected === 'crawl' && state.auditData.crawl_results) {
        $mainContent.innerHTML = renderCrawlResultsPanel(state.auditData.crawl_results);
        return;
    }

    if (selected === 'intel' && state.auditData.external_insights) {
        $mainContent.innerHTML = renderIntelPanel(state.auditData.external_insights);
        return;
    }

    // Find category
    const category = state.auditData.categories.find(c => c.name === selected);
    if (!category) return;

    let html = renderCategoryHeader(category);
    html += renderCategoryTabs(state.activeTab);

    switch (state.activeTab) {
        case 'summary':
            html += renderSummaryTab(category);
            break;
        case 'issues':
            html += renderIssueList(category.issues, state.issueFilter, state.issueSort, state.issuePage, state.issueSearch);
            break;
        case 'evidence':
            html += renderEvidenceTab(category);
            break;
        case 'recommendations':
            html += renderRecommendationsTab(category);
            break;
    }

    $mainContent.innerHTML = html;
    bindMainEvents();
}


// ============================================================
// Crawl Results Panel (reused from old code, adapted)
// ============================================================

function renderCrawlResultsPanel(data) {
    const rawColor = scoreColorRaw(data.score);
    let html = `
        <div class="category-header">
            <div class="category-header__title">
                <h2 class="Polaris-Text--headingLg">Site Crawl Results</h2>
                <span class="Polaris-Badge Polaris-Badge--${scoreTone(data.score)}">${data.score}/100</span>
            </div>
        </div>
        <div class="Polaris-Card mb-400"><div class="Polaris-Card__Section text-center">
            <p class="Polaris-Text--bodySm Polaris-Text--subdued mb-200">${escapeHtml(data.url)}</p>
            <p class="Polaris-Text--bodySm Polaris-Text--subdued">${data.pages_crawled} pages crawled, max depth ${data.max_depth}</p>
        </div></div>`;

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
// Intel Panel (reused, adapted)
// ============================================================

function renderIntelPanel(insights) {
    const sw = insights.similarweb;
    const sr = insights.semrush;

    let html = `<div class="category-header"><div class="category-header__title"><h2 class="Polaris-Text--headingLg">Market & Competitive Intelligence</h2></div></div>`;

    // KPI cards
    html += '<div class="kpi-grid mb-400">';
    if (sw && sw.status === 'ok') {
        html += renderIntelKPI('Monthly Visits', sw.estimated_monthly_visits?.display || 'N/A', 'Similarweb');
        html += renderIntelKPI('Bounce Rate', sw.bounce_rate?.display || 'N/A', 'Similarweb');
        html += renderIntelKPI('Avg Duration', sw.visit_duration?.display || 'N/A', 'Similarweb');
    }
    if (sr && sr.status === 'ok') {
        html += renderIntelKPI('Organic Keywords', (sr.organic_keywords?.length || 0).toString(), 'SEMrush');
        html += renderIntelKPI('Ref. Domains', sr.backlink_summary?.referring_domains?.toLocaleString() || 'N/A', 'SEMrush');
    }
    html += '</div>';

    // Keywords table
    if (sr && sr.status === 'ok' && sr.organic_keywords?.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Top Organic Keywords</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Keyword</th><th>Pos</th><th>Volume</th></tr></thead><tbody>`;
        sr.organic_keywords.slice(0, 15).forEach(kw => {
            html += `<tr><td>${escapeHtml(kw.keyword)}</td><td style="text-align:center">${kw.position ?? '-'}</td><td style="text-align:right">${kw.volume?.toLocaleString() ?? '-'}</td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }

    // Backlinks table
    if (sr && sr.status === 'ok' && sr.top_backlinks?.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Top Backlinks</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Source</th><th>Anchor</th></tr></thead><tbody>`;
        sr.top_backlinks.slice(0, 10).forEach(bl => {
            html += `<tr><td class="break-all">${escapeHtml(bl.source_url)}</td><td>${escapeHtml(bl.anchor || '-')}</td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }

    // Competitors
    const competitors = [];
    if (sw?.status === 'ok' && sw.similar_sites?.length) {
        sw.similar_sites.forEach(s => competitors.push({ domain: s.domain, source: 'Similarweb' }));
    }
    if (sr?.status === 'ok' && sr.organic_competitors?.length) {
        sr.organic_competitors.forEach(s => competitors.push({ domain: s.domain, source: 'SEMrush' }));
    }
    if (competitors.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Similar / Competitor Sites</h3></div><div class="Polaris-Card__Section">`;
        competitors.slice(0, 10).forEach(c => {
            html += `<div style="display:flex;justify-content:space-between;padding:var(--p-space-200) 0;border-bottom:1px solid var(--p-color-border-secondary)"><span>${escapeHtml(c.domain)}</span><span class="Polaris-Badge Polaris-Badge--default">${c.source}</span></div>`;
        });
        html += '</div></div>';
    }

    return html;
}

function renderIntelKPI(label, value, source) {
    return `<div class="kpi-card">
        <p class="kpi-card__label">${escapeHtml(label)}</p>
        <p class="kpi-card__value">${escapeHtml(value)}</p>
        <p class="kpi-card__source">${escapeHtml(source)}</p>
    </div>`;
}


// ============================================================
// Event Binding
// ============================================================

// Sidebar clicks (delegated)
$sidebarContent.addEventListener('click', (e) => {
    const item = e.target.closest('.sidebar-item');
    if (!item) return;
    const category = item.dataset.category;
    Store.set({ selectedCategory: category, activeTab: 'summary', issueFilter: 'all', issuePage: 0, issueSearch: '', sidebarOpen: false });
});

// Main content events (delegated)
function bindMainEvents() {
    // Tab clicks
    $mainContent.querySelectorAll('.Polaris-Tabs__Tab[data-tab]').forEach(tab => {
        tab.addEventListener('click', () => {
            Store.set({ activeTab: tab.dataset.tab, issuePage: 0 });
        });
    });

    // Filter pills
    $mainContent.querySelectorAll('.filter-pill[data-filter]').forEach(pill => {
        pill.addEventListener('click', () => {
            Store.set({ issueFilter: pill.dataset.filter, issuePage: 0 });
        });
    });

    // Search input
    const searchInput = $mainContent.querySelector('[data-action="search-issues"]');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                Store.set({ issueSearch: searchInput.value, issuePage: 0 });
            }, 250);
        });
        searchInput.focus();
    }

    // Issue row expand/collapse
    $mainContent.querySelectorAll('[data-toggle]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const details = document.getElementById(btn.dataset.toggle);
            if (details) {
                details.classList.toggle('open');
                btn.classList.toggle('issue-row__expand--open');
            }
        });
    });

    // Expandable row click (on the main row)
    $mainContent.querySelectorAll('.issue-row__main--expandable').forEach(row => {
        row.addEventListener('click', (e) => {
            if (e.target.closest('.issue-row__expand')) return;
            const toggleBtn = row.querySelector('[data-toggle]');
            if (toggleBtn) toggleBtn.click();
        });
    });

    // Pagination
    $mainContent.querySelectorAll('[data-page]').forEach(btn => {
        btn.addEventListener('click', () => {
            Store.set({ issuePage: parseInt(btn.dataset.page, 10) });
        });
    });
}

// Overview audit log links
function bindOverviewLinks() {
    $mainContent.querySelectorAll('[data-category]').forEach(link => {
        link.addEventListener('click', () => {
            Store.set({ selectedCategory: link.dataset.category, activeTab: 'summary' });
        });
    });
}


// ============================================================
// Form Submit — Audit
// ============================================================

$form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = $urlInput.value.trim();
    if (!url) return;

    Store.set({ isLoading: true, error: null });
    $auditBtn.disabled = true;
    $auditBtn.classList.add('disabled');

    try {
        const body = { url };

        if ($includeCrawlCb.checked) {
            body.include_crawl = true;
            body.crawl_max_pages = parseInt($crawlMaxPages.value, 10) || 10;
        }

        if ($includeExternalCb.checked) {
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

        Store.set({
            auditData: data,
            selectedCategory: 'overview',
            activeTab: 'summary',
            issueFilter: 'all',
            issuePage: 0,
            issueSearch: '',
            isLoading: false,
            error: null,
        });

    } catch (err) {
        Store.set({ isLoading: false, error: err.message });
    } finally {
        $auditBtn.disabled = false;
        $auditBtn.classList.remove('disabled');
    }
});


// ============================================================
// Crawl checkbox toggle
// ============================================================

$includeCrawlCb.addEventListener('change', () => {
    $crawlPagesWrapper.style.display = $includeCrawlCb.checked ? 'flex' : 'none';
});


// ============================================================
// PDF Download
// ============================================================

$downloadPdfBtn.addEventListener('click', async () => {
    if (!window._lastAuditData) return;

    $downloadPdfBtn.disabled = true;
    const origText = $downloadPdfBtn.innerHTML;
    $downloadPdfBtn.innerHTML = '<div class="Polaris-Spinner" style="width:20px;height:20px;border-width:2px"></div>';

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
        $downloadPdfBtn.innerHTML = origText;
        $downloadPdfBtn.disabled = false;
    }
});


// ============================================================
// Mobile Hamburger
// ============================================================

$hamburgerBtn.addEventListener('click', () => {
    Store.set({ sidebarOpen: !Store.get('sidebarOpen') });
});

$sidebarOverlay.addEventListener('click', () => {
    Store.set({ sidebarOpen: false });
});


// ============================================================
// Keyboard Navigation
// ============================================================

document.addEventListener('keydown', (e) => {
    const state = Store.get();
    if (!state.auditData) return;

    const categories = state.auditData.categories;
    const allItems = ['overview', ...categories.map(c => c.name)];
    if (state.auditData.crawl_results) allItems.push('crawl');
    if (state.auditData.external_insights) allItems.push('intel');

    const currentIdx = allItems.indexOf(state.selectedCategory);

    if (e.key === 'ArrowDown' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        const next = Math.min(currentIdx + 1, allItems.length - 1);
        Store.set({ selectedCategory: allItems[next], activeTab: 'summary' });
    } else if (e.key === 'ArrowUp' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        const prev = Math.max(currentIdx - 1, 0);
        Store.set({ selectedCategory: allItems[prev], activeTab: 'summary' });
    }
});

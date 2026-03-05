/* ============================================================
   SEO Auditor — Controller (Multi-Brand Platform)
   ============================================================ */

const API_BASE = window.location.hostname.includes('netlify.app')
    ? 'https://seo-auditor-api.onrender.com'
    : '';

// --- DOM refs ---
const $appLayout = document.getElementById('app-layout');
const $sidebar = document.getElementById('app-sidebar');
const $sidebarContent = document.getElementById('sidebar-content');
const $sidebarOverlay = document.getElementById('sidebar-overlay');
const $mainContent = document.getElementById('main-content');
const $welcomeState = document.getElementById('welcome-state');
const $loadingState = document.getElementById('loading-state');
const $mainSkeleton = document.getElementById('main-skeleton');
const $hamburgerBtn = document.getElementById('hamburger-btn');
const $errorMsg = document.getElementById('error-msg');

window._lastAuditData = null;

// ============================================================
// Store Subscriptions
// ============================================================

Store.subscribe((changed, state) => {
    // Always show sidebar in platform mode
    $appLayout.classList.add('has-results');
    $sidebar.style.display = '';

    // Re-render sidebar on nav changes
    if (changed.some(k => ['currentView', 'selectedBrand', 'brands', 'auditData'].includes(k))) {
        renderAppSidebarView(state);
    }

    // Re-render main on most changes
    if (changed.some(k => ['currentView', 'brands', 'selectedBrand', 'selectedBrandId', 'brandAudits',
        'auditData', 'selectedCategory', 'activeTab', 'issueFilter', 'issueSort', 'issuePage', 'issueSearch',
        'keywordData', 'keywordSort', 'selectedAudit'].includes(k))) {
        renderMainPanel(state);
    }

    // Loading
    if (changed.includes('isLoading')) {
        if (state.isLoading) {
            $mainContent.classList.add('hidden');
            $loadingState.classList.remove('hidden');
            $mainSkeleton.innerHTML = renderMainSkeleton();
        } else {
            $loadingState.classList.add('hidden');
            $mainContent.classList.remove('hidden');
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

    // Sidebar mobile
    if (changed.includes('sidebarOpen')) {
        $sidebar.classList.toggle('open', state.sidebarOpen);
        $sidebarOverlay.classList.toggle('open', state.sidebarOpen);
    }
});


// ============================================================
// Render: App Sidebar (platform nav)
// ============================================================

function renderAppSidebarView(state) {
    // If we have audit data in category view, show category sidebar
    if (state.auditData && state.currentView === 'category') {
        $sidebarContent.innerHTML = renderSidebar(
            state.auditData.categories,
            state.selectedCategory,
            state.auditData
        );
        return;
    }
    // Otherwise show platform nav
    $sidebarContent.innerHTML = renderAppSidebar(state);
}


// ============================================================
// Render: Main Panel (view router)
// ============================================================

function renderMainPanel(state) {
    $welcomeState.classList.add('hidden');
    $mainContent.classList.remove('hidden');

    const view = state.currentView;

    switch (view) {
        case 'home':
            $mainContent.innerHTML = renderHomePage(state);
            bindHomeEvents();
            break;

        case 'brands':
            $mainContent.innerHTML = renderBrandsList(state.brands || []);
            bindBrandListEvents();
            break;

        case 'new-brand':
            $mainContent.innerHTML = renderNewBrandForm();
            bindNewBrandForm();
            break;

        case 'brand-detail':
            $mainContent.innerHTML = renderBrandDetail(state.selectedBrand, state.brandAudits);
            bindBrandDetailEvents();
            break;

        case 'brand-audits':
            $mainContent.innerHTML = renderAuditHistoryTable(state.brandAudits, state.selectedBrand?.name);
            bindAuditListEvents();
            break;

        case 'audit-run':
            $mainContent.innerHTML = renderBrandAuditForm(state.selectedBrand);
            bindBrandAuditForm();
            break;

        case 'reports':
            $mainContent.innerHTML = renderReportsPage(state.selectedBrand, state.brandAudits);
            bindReportEvents();
            break;

        case 'settings':
            $mainContent.innerHTML = renderBrandSettings(state.selectedBrand);
            bindSettingsEvents();
            break;

        case 'quick-audit':
            $mainContent.innerHTML = renderQuickAuditForm();
            bindQuickAuditForm();
            break;

        case 'category':
            renderCategoryView(state);
            break;

        default:
            $mainContent.innerHTML = renderHomePage(state);
            bindHomeEvents();
    }
}


// ============================================================
// Category View (audit detail with sidebar categories)
// ============================================================

function renderCategoryView(state) {
    if (!state.auditData) {
        $mainContent.innerHTML = '<p>No audit data loaded.</p>';
        return;
    }

    const selected = state.selectedCategory;

    if (selected === 'overview') {
        $mainContent.innerHTML = renderOverviewPanel(state.auditData);

        // Add exec summary below overview if available
        if (state.auditData.executive_summary) {
            $mainContent.innerHTML += renderExecutiveSummarySection(
                state.auditData.executive_summary, state.auditData.overall_score
            );
        }

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
    if (selected === 'pagespeed' && state.auditData.pagespeed_insights) {
        $mainContent.innerHTML = renderPageSpeedPanel(state.auditData.pagespeed_insights);
        return;
    }
    if (selected === 'schema_validation' && state.auditData.schema_validation) {
        $mainContent.innerHTML = renderSchemaValidationPanel(state.auditData.schema_validation);
        return;
    }
    if (selected === 'keyword_research' && state.keywordData) {
        $mainContent.innerHTML = renderKeywordPanel(state.keywordData);
        bindKeywordSort();
        return;
    }

    const category = state.auditData.categories.find(c => c.name === selected);
    if (!category) return;

    let html = renderCategoryHeader(category);
    html += renderCategoryTabs(state.activeTab);

    switch (state.activeTab) {
        case 'summary': html += renderSummaryTab(category); break;
        case 'issues': html += renderIssueList(category.issues, state.issueFilter, state.issueSort, state.issuePage, state.issueSearch); break;
        case 'evidence': html += renderEvidenceTab(category); break;
        case 'recommendations': html += renderRecommendationsTab(category); break;
    }

    $mainContent.innerHTML = html;
    bindMainEvents();
}


// ============================================================
// Crawl / Intel panels (reused from old code)
// ============================================================

function renderCrawlResultsPanel(data) {
    const rawColor = scoreColorRaw(data.score);
    let html = `<div class="category-header"><div class="category-header__title"><h2 class="Polaris-Text--headingLg">Site Crawl Results</h2><span class="Polaris-Badge Polaris-Badge--${scoreTone(data.score)}">${data.score}/100</span></div></div>`;
    html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Section text-center"><p class="Polaris-Text--bodySm Polaris-Text--subdued">${escapeHtml(data.url)} | ${data.pages_crawled} pages, depth ${data.max_depth}</p></div></div>`;
    if (data.issues && data.issues.length) {
        html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Issues</h3></div><div class="Polaris-Card__Section">';
        data.issues.forEach(i => { html += `<div class="issue-item">${severityIcon(i.severity)}<span>${escapeHtml(i.message)}</span></div>`; });
        html += '</div></div>';
    }
    if (data.broken_links && data.broken_links.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm Polaris-Text--critical">Broken Links (${data.broken_links.length})</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Target</th><th>Status</th><th>Source</th></tr></thead><tbody>`;
        data.broken_links.forEach(bl => { html += `<tr><td class="break-all">${escapeHtml(bl.target_url)}</td><td style="color:var(--p-color-text-critical)">${bl.status_code||'Timeout'}</td><td class="break-all Polaris-Text--subdued">${escapeHtml(bl.source_url)}</td></tr>`; });
        html += '</tbody></table></div></div></div>';
    }
    if (data.pages && data.pages.length) {
        html += `<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Pages (${data.pages.length})</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>URL</th><th>Title</th><th>Links</th><th>Depth</th></tr></thead><tbody>`;
        data.pages.forEach(p => { html += `<tr><td class="break-all">${escapeHtml(p.url)}</td><td>${escapeHtml(p.title||'(none)')}</td><td>${p.internal_links}</td><td>${p.depth}</td></tr>`; });
        html += '</tbody></table></div></div></div>';
    }
    return html;
}

function renderIntelPanel(insights) {
    const sw = insights.similarweb, sr = insights.semrush;
    let html = '<div class="category-header"><div class="category-header__title"><h2 class="Polaris-Text--headingLg">Market Intelligence</h2></div></div>';
    html += '<div class="kpi-grid mb-400">';
    if (sw && sw.status === 'ok') {
        html += renderIntelKPI('Monthly Visits', sw.estimated_monthly_visits?.display || 'N/A', 'Similarweb');
        html += renderIntelKPI('Bounce Rate', sw.bounce_rate?.display || 'N/A', 'Similarweb');
    }
    if (sr && sr.status === 'ok') {
        html += renderIntelKPI('Organic Keywords', (sr.organic_keywords?.length || 0).toString(), 'SEMrush');
        html += renderIntelKPI('Ref. Domains', sr.backlink_summary?.referring_domains?.toLocaleString() || 'N/A', 'SEMrush');
    }
    html += '</div>';
    if (sr && sr.status === 'ok' && sr.organic_keywords?.length) {
        html += '<div class="Polaris-Card mb-400"><div class="Polaris-Card__Header"><h3 class="Polaris-Text--headingSm">Top Organic Keywords</h3></div><div class="Polaris-Card__Section" style="padding:0"><div class="overflow-x"><table class="Polaris-DataTable"><thead><tr><th>Keyword</th><th>Pos</th><th>Volume</th></tr></thead><tbody>';
        sr.organic_keywords.slice(0,15).forEach(kw => { html += `<tr><td>${escapeHtml(kw.keyword)}</td><td style="text-align:center">${kw.position??'-'}</td><td style="text-align:right">${kw.volume?.toLocaleString()??'-'}</td></tr>`; });
        html += '</tbody></table></div></div></div>';
    }
    return html;
}


// ============================================================
// Event Bindings
// ============================================================

// Platform sidebar navigation (delegated)
$sidebarContent.addEventListener('click', (e) => {
    const navItem = e.target.closest('[data-nav]');
    if (navItem) {
        const nav = navItem.dataset.nav;
        if (nav === 'home') { Store.set({ currentView: 'home', sidebarOpen: false }); loadBrands(); }
        else if (nav === 'brands') { Store.set({ currentView: 'brands', sidebarOpen: false }); loadBrands(); }
        else if (nav === 'quick-audit') { Store.set({ currentView: 'quick-audit', sidebarOpen: false }); }
        else if (['brand-detail', 'brand-audits', 'audit-run', 'reports', 'settings'].includes(nav)) {
            Store.set({ currentView: nav, sidebarOpen: false });
        }
        return;
    }

    // Category sidebar clicks (when viewing audit)
    const catItem = e.target.closest('.sidebar-item[data-category]');
    if (catItem) {
        Store.set({ selectedCategory: catItem.dataset.category, activeTab: 'summary', issueFilter: 'all', issuePage: 0, issueSearch: '', sidebarOpen: false });
    }
});

function bindMainEvents() {
    // Tabs, filters, sort, search, expand, pagination
    $mainContent.querySelectorAll('.Polaris-Tabs__Tab[data-tab]').forEach(tab => {
        tab.addEventListener('click', () => Store.set({ activeTab: tab.dataset.tab, issuePage: 0 }));
    });
    $mainContent.querySelectorAll('.filter-pill[data-filter]').forEach(pill => {
        pill.addEventListener('click', () => Store.set({ issueFilter: pill.dataset.filter, issuePage: 0 }));
    });
    $mainContent.querySelectorAll('.filter-pill[data-sort]').forEach(pill => {
        pill.addEventListener('click', () => Store.set({ issueSort: pill.dataset.sort, issuePage: 0 }));
    });
    const searchInput = $mainContent.querySelector('[data-action="search-issues"]');
    if (searchInput) {
        let t; searchInput.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => Store.set({ issueSearch: searchInput.value, issuePage: 0 }), 250); });
    }
    $mainContent.querySelectorAll('[data-toggle]').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); const d = document.getElementById(btn.dataset.toggle); if (d) { d.classList.toggle('open'); btn.classList.toggle('issue-row__expand--open'); } });
    });
    $mainContent.querySelectorAll('.issue-row__main--expandable').forEach(row => {
        row.addEventListener('click', (e) => { if (e.target.closest('.issue-row__expand')) return; const b = row.querySelector('[data-toggle]'); if (b) b.click(); });
    });
    $mainContent.querySelectorAll('[data-page]').forEach(btn => {
        btn.addEventListener('click', () => Store.set({ issuePage: parseInt(btn.dataset.page, 10) }));
    });
}

function bindOverviewLinks() {
    $mainContent.querySelectorAll('[data-category]').forEach(link => {
        link.addEventListener('click', () => Store.set({ selectedCategory: link.dataset.category, activeTab: 'summary' }));
    });
}

function bindKeywordSort() {
    $mainContent.querySelectorAll('[data-kw-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.dataset.kwSort;
            const cur = Store.get('keywordSort') || 'volume_desc';
            const [c, d] = cur.split('_');
            Store.set({ keywordSort: `${col}_${c === col && d === 'desc' ? 'asc' : 'desc'}` });
        });
    });
}

// Copy buttons
$mainContent.addEventListener('click', (e) => {
    const copyBtn = e.target.closest('.copy-btn');
    if (copyBtn) { const b = copyBtn.closest('.evidence-block'); if (b) navigator.clipboard.writeText(b.childNodes[0]?.textContent || '').catch(()=>{}); }
});

// Home events
function bindHomeEvents() {
    $mainContent.querySelectorAll('[data-action="new-brand"]').forEach(btn => {
        btn.addEventListener('click', () => Store.set({ currentView: 'new-brand' }));
    });
    $mainContent.querySelectorAll('[data-nav]').forEach(btn => {
        btn.addEventListener('click', () => Store.set({ currentView: btn.dataset.nav }));
    });
    $mainContent.querySelectorAll('[data-brand-id]').forEach(card => {
        card.addEventListener('click', () => selectBrand(card.dataset.brandId));
    });
}

// Brand list events
function bindBrandListEvents() {
    $mainContent.querySelectorAll('[data-action="new-brand"]').forEach(btn => {
        btn.addEventListener('click', () => Store.set({ currentView: 'new-brand' }));
    });
    $mainContent.querySelectorAll('[data-brand-id]').forEach(row => {
        row.addEventListener('click', () => selectBrand(row.dataset.brandId));
    });
}

// Brand detail events
function bindBrandDetailEvents() {
    $mainContent.querySelectorAll('[data-view-audit]').forEach(btn => {
        btn.addEventListener('click', () => viewAudit(btn.dataset.viewAudit));
    });
    $mainContent.querySelectorAll('[data-export-pdf]').forEach(btn => {
        btn.addEventListener('click', () => exportPDF(btn.dataset.exportPdf));
    });
}

// Audit list events
function bindAuditListEvents() {
    $mainContent.querySelectorAll('[data-view-audit]').forEach(btn => {
        btn.addEventListener('click', () => viewAudit(btn.dataset.viewAudit));
    });
    $mainContent.querySelectorAll('[data-export-pdf]').forEach(btn => {
        btn.addEventListener('click', () => exportPDF(btn.dataset.exportPdf));
    });
}

// Report events
function bindReportEvents() {
    $mainContent.querySelectorAll('[data-export-pdf]').forEach(btn => {
        btn.addEventListener('click', () => exportPDF(btn.dataset.exportPdf));
    });
}


// ============================================================
// Brand Form
// ============================================================

function bindNewBrandForm() {
    const form = document.getElementById('brand-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const body = {
            name: document.getElementById('brand-name').value.trim(),
            primary_domain: document.getElementById('brand-domain').value.trim(),
            industry: document.getElementById('brand-industry').value.trim() || undefined,
            description: document.getElementById('brand-description').value.trim() || undefined,
            persona: document.getElementById('brand-persona').value.trim() || undefined,
            revenue_range: document.getElementById('brand-revenue').value || undefined,
        };
        if (!body.name || !body.primary_domain) return;

        // Disable submit button while creating
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating & fetching site info...';
        }

        try {
            const resp = await fetch(API_BASE + '/api/brands', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!resp.ok) throw new Error('Failed to create brand');
            const brand = await resp.json();

            // Navigate to brand detail immediately
            await selectBrand(brand.id);

            // Kick off initial audit in the background
            const domain = brand.primary_domain;
            const auditUrl = `https://${domain}`;
            Store.set({ loading: true });

            try {
                const auditResp = await fetch(API_BASE + `/api/brands/${brand.id}/audits`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: auditUrl,
                        save_result: true,
                        include_exec_summary: true,
                    }),
                });
                if (auditResp.ok) {
                    const auditData = await auditResp.json();
                    Store.set({ auditData, activeTab: 'overview', loading: false });
                } else {
                    Store.set({ loading: false });
                }
            } catch (_auditErr) {
                Store.set({ loading: false });
            }
        } catch (err) {
            Store.set({ error: err.message });
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Brand';
            }
        }
    });
}


// ============================================================
// Settings Form
// ============================================================

function bindSettingsEvents() {
    const form = document.getElementById('brand-update-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const brand = Store.get('selectedBrand');
            if (!brand) return;
            const body = {
                name: document.getElementById('edit-brand-name').value.trim() || undefined,
                industry: document.getElementById('edit-brand-industry').value.trim() || undefined,
                description: document.getElementById('edit-brand-description').value.trim() || undefined,
                persona: document.getElementById('edit-brand-persona').value.trim() || undefined,
                revenue_range: document.getElementById('edit-brand-revenue').value || undefined,
            };
            try {
                const resp = await fetch(API_BASE + `/api/brands/${brand.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                });
                if (!resp.ok) throw new Error('Update failed');
                const updated = await resp.json();
                Store.set({ selectedBrand: updated });
            } catch (err) {
                Store.set({ error: err.message });
            }
        });
    }

    // Logo upload
    const logoInput = document.getElementById('logo-upload');
    if (logoInput) {
        logoInput.addEventListener('change', () => uploadFile(logoInput, 'logo'));
    }

    // BG upload
    const bgInput = document.getElementById('bg-upload');
    if (bgInput) {
        bgInput.addEventListener('change', () => uploadFile(bgInput, 'background'));
    }

    // Save theme
    const saveThemeBtn = document.getElementById('save-theme-btn');
    if (saveThemeBtn) {
        saveThemeBtn.addEventListener('click', async () => {
            const brand = Store.get('selectedBrand');
            if (!brand) return;
            const theme = {
                primary_color: document.getElementById('theme-primary-color')?.value || '#a58464',
                bg_color: document.getElementById('theme-bg-color')?.value || '#faf9f7',
            };
            try {
                const resp = await fetch(API_BASE + `/api/brands/${brand.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ theme_json: theme }),
                });
                if (!resp.ok) throw new Error('Theme save failed');
                const updated = await resp.json();
                Store.set({ selectedBrand: updated });
            } catch (err) {
                Store.set({ error: err.message });
            }
        });
    }
}

async function uploadFile(input, fileType) {
    const brand = Store.get('selectedBrand');
    if (!brand || !input.files[0]) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);
    try {
        const resp = await fetch(API_BASE + `/api/uploads?brand_id=${brand.id}&file_type=${fileType}`, {
            method: 'POST', body: formData,
        });
        if (!resp.ok) { const d = await resp.json().catch(()=>({})); throw new Error(d.detail || 'Upload failed'); }
        // Refresh brand
        await selectBrand(brand.id);
    } catch (err) {
        Store.set({ error: err.message });
    }
}


// ============================================================
// Quick Audit Form
// ============================================================

function bindQuickAuditForm() {
    const form = document.getElementById('quick-audit-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('qa-url').value.trim();
        if (!url) return;

        Store.set({ isLoading: true, error: null });
        try {
            const body = {
                url,
                include_exec_summary: true,
                include_crawl: document.getElementById('qa-crawl')?.checked || false,
                include_pagespeed: document.getElementById('qa-psi')?.checked || false,
                include_schema_validation: document.getElementById('qa-schema')?.checked || false,
                include_external: document.getElementById('qa-intel')?.checked || false,
            };
            if (body.include_external) body.external_modules = ['similarweb', 'semrush'];

            const resp = await fetch(API_BASE + '/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!resp.ok) { const d = await resp.json().catch(()=>({})); throw new Error(d.detail || 'Audit failed'); }

            const data = await resp.json();
            window._lastAuditData = data;
            Store.set({
                auditData: data,
                currentView: 'category',
                selectedCategory: 'overview',
                activeTab: 'summary',
                isLoading: false,
            });
        } catch (err) {
            Store.set({ isLoading: false, error: err.message });
        }
    });
}


// ============================================================
// Brand Audit Form
// ============================================================

function bindBrandAuditForm() {
    const form = document.getElementById('brand-audit-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const brand = Store.get('selectedBrand');
        if (!brand) return;
        const url = document.getElementById('ba-url').value.trim();
        if (!url) return;

        Store.set({ isLoading: true, error: null });
        try {
            const body = {
                url,
                brand_id: brand.id,
                save_result: true,
                include_exec_summary: true,
                include_crawl: document.getElementById('ba-crawl')?.checked || false,
                include_pagespeed: document.getElementById('ba-psi')?.checked || false,
                include_schema_validation: document.getElementById('ba-schema')?.checked || false,
                include_external: document.getElementById('ba-intel')?.checked || false,
            };
            if (body.include_external) body.external_modules = ['similarweb', 'semrush'];

            const resp = await fetch(API_BASE + '/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!resp.ok) { const d = await resp.json().catch(()=>({})); throw new Error(d.detail || 'Audit failed'); }

            const data = await resp.json();
            window._lastAuditData = data;
            Store.set({
                auditData: data,
                currentView: 'category',
                selectedCategory: 'overview',
                activeTab: 'summary',
                isLoading: false,
            });

            // Refresh brand audits
            loadBrandAudits(brand.id);
        } catch (err) {
            Store.set({ isLoading: false, error: err.message });
        }
    });
}


// ============================================================
// API helpers
// ============================================================

async function loadBrands() {
    try {
        const resp = await fetch(API_BASE + '/api/brands');
        if (resp.ok) {
            const brands = await resp.json();
            Store.set({ brands });
        }
    } catch (e) { /* ignore */ }
}

async function selectBrand(brandId) {
    try {
        const [brandResp, auditsResp] = await Promise.all([
            fetch(API_BASE + `/api/brands/${brandId}`),
            fetch(API_BASE + `/api/brands/${brandId}/audits`),
        ]);
        if (!brandResp.ok) throw new Error('Brand not found');
        const brand = await brandResp.json();
        const audits = auditsResp.ok ? await auditsResp.json() : [];
        Store.set({
            selectedBrandId: brandId,
            selectedBrand: brand,
            brandAudits: audits,
            currentView: 'brand-detail',
        });
    } catch (err) {
        Store.set({ error: err.message });
    }
}

async function loadBrandAudits(brandId) {
    try {
        const resp = await fetch(API_BASE + `/api/brands/${brandId}/audits`);
        if (resp.ok) {
            const audits = await resp.json();
            Store.set({ brandAudits: audits });
        }
    } catch (e) { /* ignore */ }
}

async function viewAudit(auditId) {
    try {
        Store.set({ isLoading: true });
        const resp = await fetch(API_BASE + `/api/audits/${auditId}`);
        if (!resp.ok) throw new Error('Audit not found');
        const audit = await resp.json();

        // Reconstruct audit data for category view
        const snapshot = audit.category_results_json || {};
        const auditData = {
            url: snapshot.url || audit.audited_url,
            overall_score: snapshot.overall_score || audit.overall_score,
            categories: snapshot.categories || [],
            executive_summary: audit.summary_json,
        };
        window._lastAuditData = auditData;
        Store.set({
            auditData,
            currentView: 'category',
            selectedCategory: 'overview',
            activeTab: 'summary',
            isLoading: false,
        });
    } catch (err) {
        Store.set({ isLoading: false, error: err.message });
    }
}

async function exportPDF(auditId) {
    try {
        const resp = await fetch(API_BASE + '/api/reports/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audit_id: auditId }),
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
        alert('PDF export failed: ' + err.message);
    }
}


// ============================================================
// Mobile Hamburger
// ============================================================

$hamburgerBtn.addEventListener('click', () => Store.set({ sidebarOpen: !Store.get('sidebarOpen') }));
$sidebarOverlay.addEventListener('click', () => Store.set({ sidebarOpen: false }));


// ============================================================
// Legacy form support (topbar audit form if it exists)
// ============================================================

const $form = document.getElementById('audit-form');
if ($form) {
    $form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const urlInput = document.getElementById('url-input');
        const url = urlInput ? urlInput.value.trim() : '';
        if (!url) return;
        Store.set({ isLoading: true, error: null });
        try {
            const body = { url, include_exec_summary: true };
            const psi = document.getElementById('include-psi');
            if (psi && psi.checked) body.include_pagespeed = true;
            const schema = document.getElementById('include-schema');
            if (schema && schema.checked) body.include_schema_validation = true;
            const crawl = document.getElementById('include-crawl');
            if (crawl && crawl.checked) {
                body.include_crawl = true;
                const mp = document.getElementById('crawl-max-pages');
                body.crawl_max_pages = mp ? parseInt(mp.value, 10) || 10 : 10;
            }
            const intel = document.getElementById('include-external');
            if (intel && intel.checked) { body.include_external = true; body.external_modules = ['similarweb', 'semrush']; }

            const resp = await fetch(API_BASE + '/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!resp.ok) { const d = await resp.json().catch(()=>({})); throw new Error(d.detail || `Error (${resp.status})`); }

            const data = await resp.json();
            window._lastAuditData = data;
            Store.set({
                auditData: data,
                currentView: 'category',
                selectedCategory: 'overview',
                activeTab: 'summary',
                isLoading: false,
            });
        } catch (err) {
            Store.set({ isLoading: false, error: err.message });
        }
    });
}

// Legacy PDF download button
const $downloadPdfBtn = document.getElementById('download-pdf-btn');
if ($downloadPdfBtn) {
    $downloadPdfBtn.addEventListener('click', async () => {
        if (!window._lastAuditData) return;
        $downloadPdfBtn.disabled = true;
        try {
            const resp = await fetch(API_BASE + '/api/report/pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(window._lastAuditData),
            });
            if (!resp.ok) throw new Error('PDF failed');
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'seo-audit-report.pdf';
            document.body.appendChild(a); a.click(); a.remove();
            URL.revokeObjectURL(url);
        } catch (err) { alert('PDF error: ' + err.message); }
        finally { $downloadPdfBtn.disabled = false; }
    });
}


// ============================================================
// Init: Load brands and show home
// ============================================================

(async function init() {
    $appLayout.classList.add('has-results');
    await loadBrands();
    Store.set({ currentView: 'home' });
})();

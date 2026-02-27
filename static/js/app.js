const form = document.getElementById('audit-form');
const urlInput = document.getElementById('url-input');
const auditBtn = document.getElementById('audit-btn');
const errorMsg = document.getElementById('error-msg');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const categoriesGrid = document.getElementById('categories-grid');
const downloadPdfBtn = document.getElementById('download-pdf-btn');

const crawlForm = document.getElementById('crawl-form');
const crawlUrlInput = document.getElementById('crawl-url-input');
const crawlMaxPages = document.getElementById('crawl-max-pages');
const crawlBtn = document.getElementById('crawl-btn');
const crawlErrorMsg = document.getElementById('crawl-error-msg');
const crawlLoading = document.getElementById('crawl-loading');
const crawlResults = document.getElementById('crawl-results');
const crawlResultsContent = document.getElementById('crawl-results-content');

window._lastAuditData = null;

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
    meta_tags: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"/></svg>',
    headings: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16"/></svg>',
    images: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
    links: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/></svg>',
    performance: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
    mobile: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>',
    structured_data: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>',
    sitemap: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A2 2 0 013 15.382V5.618a2 2 0 011.553-1.894L9 2m0 18l6-3m-6 3V2m6 15l5.447-2.724A2 2 0 0021 12.382V5.618a2 2 0 00-1.553-1.894L15 2m0 15V2m0 0L9 2"/></svg>',
    robots: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>',
    tracking: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>',
    semantic: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>',
    ads_quality: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"/></svg>',
    serp_features: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>',
    accessibility: '<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>',
};

function scoreColor(score) {
    if (score >= 80) return '#22c55e';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
}

function scoreLabel(score) {
    if (score >= 80) return 'Good';
    if (score >= 50) return 'Needs Work';
    return 'Poor';
}

function severityIcon(severity) {
    const symbols = { error: '!', warning: '!', info: 'i', pass: '\u2713' };
    return `<span class="severity-icon severity-${severity}">${symbols[severity]}</span>`;
}

function renderOverallScore(score) {
    const ring = document.getElementById('score-ring');
    const circumference = 2 * Math.PI * 78; // ~490
    const offset = circumference - (score / 100) * circumference;
    ring.style.strokeDasharray = circumference;
    ring.style.strokeDashoffset = circumference;
    ring.style.stroke = scoreColor(score);

    // Animate after a brief delay
    requestAnimationFrame(() => {
        setTimeout(() => {
            ring.style.strokeDashoffset = offset;
        }, 100);
    });

    // Animate number
    const el = document.getElementById('overall-score');
    let current = 0;
    const step = Math.max(1, Math.floor(score / 40));
    const interval = setInterval(() => {
        current += step;
        if (current >= score) {
            current = score;
            clearInterval(interval);
        }
        el.textContent = current;
        el.style.color = scoreColor(current);
    }, 25);
}

function renderCategory(cat) {
    const label = CATEGORY_LABELS[cat.name] || cat.name;
    const icon = CATEGORY_ICONS[cat.name] || '';
    const color = scoreColor(cat.score);
    const id = `cat-${cat.name}`;

    const issuesHtml = cat.issues.map(issue =>
        `<div class="issue-item">
            ${severityIcon(issue.severity)}
            <span class="text-slate-300">${escapeHtml(issue.message)}</span>
        </div>`
    ).join('');

    const errorCount = cat.issues.filter(i => i.severity === 'error').length;
    const warnCount = cat.issues.filter(i => i.severity === 'warning').length;

    let badge = '';
    if (errorCount) badge += `<span class="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">${errorCount} error${errorCount > 1 ? 's' : ''}</span>`;
    if (warnCount) badge += `<span class="text-xs px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 ml-1">${warnCount} warning${warnCount > 1 ? 's' : ''}</span>`;
    if (!errorCount && !warnCount) badge = `<span class="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">All clear</span>`;

    return `
        <div class="category-card">
            <button onclick="toggleIssues('${id}')" class="w-full text-left p-4 focus:outline-none">
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center gap-2">
                        <span style="color:${color}">${icon}</span>
                        <span class="font-semibold">${label}</span>
                    </div>
                    <span class="text-lg font-bold" style="color:${color}">${cat.score}</span>
                </div>
                <div class="score-bar-bg mb-2">
                    <div class="score-bar-fill" style="width:${cat.score}%;background:${color}"></div>
                </div>
                <div class="flex items-center gap-1">${badge}</div>
            </button>
            <div id="${id}" class="issues-list px-4 pb-2">
                ${issuesHtml}
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function toggleIssues(id) {
    document.getElementById(id).classList.toggle('open');
}

// --- Crawl results rendering ---

function renderCrawlResults(data) {
    const color = scoreColor(data.score);
    let html = `
        <div class="text-center mb-6">
            <h2 class="text-xl font-bold mb-1">Site Crawl Results</h2>
            <p class="text-slate-400 text-sm">${escapeHtml(data.url)}</p>
            <div class="mt-3">
                <span class="text-3xl font-bold" style="color:${color}">${data.score}</span>
                <span class="text-slate-400 text-sm ml-1">/ 100</span>
            </div>
            <p class="text-slate-500 text-xs mt-1">${data.pages_crawled} pages crawled, max depth ${data.max_depth}</p>
        </div>
    `;

    // Issues
    if (data.issues && data.issues.length) {
        html += '<div class="category-card mb-4"><div class="p-4">';
        html += '<h3 class="font-semibold mb-3">Crawl Issues</h3>';
        data.issues.forEach(issue => {
            html += `<div class="issue-item">${severityIcon(issue.severity)}<span class="text-slate-300">${escapeHtml(issue.message)}</span></div>`;
        });
        html += '</div></div>';
    }

    // Broken links table
    if (data.broken_links && data.broken_links.length) {
        html += '<div class="category-card mb-4"><div class="p-4">';
        html += `<h3 class="font-semibold mb-3 text-red-400">Broken Links (${data.broken_links.length})</h3>`;
        html += '<div class="overflow-x-auto"><table class="w-full text-sm text-left">';
        html += '<thead><tr class="text-slate-400 border-b border-slate-700"><th class="pb-2">Target URL</th><th class="pb-2">Status</th><th class="pb-2">Source</th></tr></thead><tbody>';
        data.broken_links.forEach(bl => {
            html += `<tr class="border-b border-slate-800"><td class="py-1.5 text-slate-300 break-all">${escapeHtml(bl.target_url)}</td><td class="py-1.5 text-red-400">${bl.status_code || 'Timeout'}</td><td class="py-1.5 text-slate-500 break-all">${escapeHtml(bl.source_url)}</td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }

    // Duplicate titles
    if (data.duplicate_titles && data.duplicate_titles.length) {
        html += '<div class="category-card mb-4"><div class="p-4">';
        html += `<h3 class="font-semibold mb-3 text-yellow-400">Duplicate Titles (${data.duplicate_titles.length})</h3>`;
        data.duplicate_titles.forEach(dt => {
            html += `<div class="mb-2"><p class="text-slate-300 text-sm font-medium">"${escapeHtml(dt.value)}"</p>`;
            dt.pages.forEach(p => { html += `<p class="text-slate-500 text-xs ml-3">- ${escapeHtml(p)}</p>`; });
            html += '</div>';
        });
        html += '</div></div>';
    }

    // Duplicate descriptions
    if (data.duplicate_descriptions && data.duplicate_descriptions.length) {
        html += '<div class="category-card mb-4"><div class="p-4">';
        html += `<h3 class="font-semibold mb-3 text-yellow-400">Duplicate Descriptions (${data.duplicate_descriptions.length})</h3>`;
        data.duplicate_descriptions.forEach(dd => {
            html += `<div class="mb-2"><p class="text-slate-300 text-sm font-medium">"${escapeHtml(dd.value.substring(0, 80))}..."</p>`;
            dd.pages.forEach(p => { html += `<p class="text-slate-500 text-xs ml-3">- ${escapeHtml(p)}</p>`; });
            html += '</div>';
        });
        html += '</div></div>';
    }

    // Orphan pages
    if (data.orphan_pages && data.orphan_pages.length) {
        html += '<div class="category-card mb-4"><div class="p-4">';
        html += `<h3 class="font-semibold mb-3 text-yellow-400">Orphan Pages (${data.orphan_pages.length})</h3>`;
        data.orphan_pages.forEach(p => {
            html += `<p class="text-slate-400 text-sm">- ${escapeHtml(p)}</p>`;
        });
        html += '</div></div>';
    }

    // Pages table
    if (data.pages && data.pages.length) {
        html += '<div class="category-card mb-4"><div class="p-4">';
        html += `<h3 class="font-semibold mb-3">Pages Crawled (${data.pages.length})</h3>`;
        html += '<div class="overflow-x-auto"><table class="w-full text-sm text-left">';
        html += '<thead><tr class="text-slate-400 border-b border-slate-700"><th class="pb-2">URL</th><th class="pb-2">Title</th><th class="pb-2">Links</th><th class="pb-2">Depth</th></tr></thead><tbody>';
        data.pages.forEach(p => {
            html += `<tr class="border-b border-slate-800"><td class="py-1.5 text-slate-300 break-all">${escapeHtml(p.url)}</td><td class="py-1.5 text-slate-400">${escapeHtml(p.title || '(none)')}</td><td class="py-1.5 text-slate-500">${p.internal_links}</td><td class="py-1.5 text-slate-500">${p.depth}</td></tr>`;
        });
        html += '</tbody></table></div></div></div>';
    }

    return html;
}

// --- Event listeners ---

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    errorMsg.classList.add('hidden');
    results.classList.add('hidden');
    loading.classList.remove('hidden');
    auditBtn.disabled = true;

    try {
        const resp = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });

        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.detail || `Server error (${resp.status})`);
        }

        const data = await resp.json();
        window._lastAuditData = data;

        // Render results
        document.getElementById('audited-url').textContent = data.url;
        categoriesGrid.innerHTML = data.categories.map(renderCategory).join('');
        renderOverallScore(data.overall_score);

        loading.classList.add('hidden');
        results.classList.remove('hidden');
    } catch (err) {
        loading.classList.add('hidden');
        errorMsg.textContent = err.message;
        errorMsg.classList.remove('hidden');
    } finally {
        auditBtn.disabled = false;
    }
});

crawlForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = crawlUrlInput.value.trim();
    const maxPages = parseInt(crawlMaxPages.value, 10) || 10;
    if (!url) return;

    crawlErrorMsg.classList.add('hidden');
    crawlResults.classList.add('hidden');
    crawlLoading.classList.remove('hidden');
    crawlBtn.disabled = true;

    try {
        const resp = await fetch('/api/crawl', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, max_pages: maxPages }),
        });

        if (!resp.ok) {
            const data = await resp.json().catch(() => ({}));
            throw new Error(data.detail || `Crawl error (${resp.status})`);
        }

        const data = await resp.json();
        crawlResultsContent.innerHTML = renderCrawlResults(data);

        crawlLoading.classList.add('hidden');
        crawlResults.classList.remove('hidden');
    } catch (err) {
        crawlLoading.classList.add('hidden');
        crawlErrorMsg.textContent = err.message;
        crawlErrorMsg.classList.remove('hidden');
    } finally {
        crawlBtn.disabled = false;
    }
});

downloadPdfBtn.addEventListener('click', async () => {
    if (!window._lastAuditData) return;

    downloadPdfBtn.disabled = true;
    const origText = downloadPdfBtn.innerHTML;
    downloadPdfBtn.innerHTML = `<svg class="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg> Generating PDF...`;

    try {
        const resp = await fetch('/api/report/pdf', {
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

const form = document.getElementById('audit-form');
const urlInput = document.getElementById('url-input');
const auditBtn = document.getElementById('audit-btn');
const errorMsg = document.getElementById('error-msg');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const categoriesGrid = document.getElementById('categories-grid');

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

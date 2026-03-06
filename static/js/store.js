/* ============================================================
   Simple Observable State Store
   ============================================================ */

const Store = (() => {
    const _state = {
        // Navigation
        currentView: 'home',        // 'home' | 'brands' | 'brand-detail' | 'audit-detail' | 'audit-run' | 'reports' | 'settings' | 'category'
        selectedCategory: 'overview',
        activeTab: 'summary',

        // Audit data (single audit view)
        auditData: null,
        issueFilter: 'all',
        issueSort: 'severity',
        issuePage: 0,
        issueSearch: '',

        // Multi-brand state
        brands: [],
        selectedBrandId: null,
        selectedBrand: null,
        brandAudits: [],

        // Audit detail (from DB)
        selectedAuditId: null,
        selectedAudit: null,

        // Loading / error
        isLoading: false,
        error: null,
        sidebarOpen: false,

        // Keyword planner
        adminToken: null,
        keywordEnabled: false,
        keywordData: null,
        keywordSort: 'volume_desc',

        // Sitemap export + Tag discovery
        sitemapExportJob: null,   // { job_id, status, progress, ... }
        tagScanJob: null,         // { job_id, status, progress, ... }
    };

    const _listeners = [];

    function get(key) {
        if (key) return _state[key];
        return { ..._state };
    }

    function set(updates) {
        const changed = [];
        for (const [key, value] of Object.entries(updates)) {
            if (_state[key] !== value) {
                _state[key] = value;
                changed.push(key);
            }
        }
        if (changed.length) {
            _listeners.forEach(fn => fn(changed, _state));
        }
    }

    function subscribe(fn) {
        _listeners.push(fn);
        return () => {
            const idx = _listeners.indexOf(fn);
            if (idx > -1) _listeners.splice(idx, 1);
        };
    }

    return { get, set, subscribe };
})();

/* ============================================================
   Simple Observable State Store
   ============================================================ */

const Store = (() => {
    const _state = {
        auditData: null,
        selectedCategory: 'overview',
        activeTab: 'summary',
        issueFilter: 'all',       // 'all' | 'error' | 'warning' | 'info' | 'pass'
        issueSort: 'severity',    // 'severity' | 'impact'
        issuePage: 0,
        issueSearch: '',
        isLoading: false,
        error: null,
        sidebarOpen: false,       // mobile sidebar toggle
        adminToken: null,          // keyword planner auth (memory only)
        keywordEnabled: false,     // whether keyword planner is available
        keywordData: null,         // standalone keyword results
        keywordSort: 'volume_desc', // keyword table sort
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

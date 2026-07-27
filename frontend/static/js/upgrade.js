const API_BASE = '';

// ✅ FIX: Apply saved theme immediately when the page loads
const savedTheme = localStorage.getItem('vision_ai_theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

// ============================================================
// THEME TOGGLE FUNCTIONS
// ============================================================
function toggleTheme() {
    const current = localStorage.getItem('vision_ai_theme') || 'dark';
    if (current === 'dark') {
        applyTheme('light');
    } else if (current === 'light') {
        applyTheme('system');
    } else {
        applyTheme('dark');
    }
}

function applyTheme(theme) {
    const toggleBtn = document.getElementById('themeToggle');
    if (theme === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', systemTheme);
        localStorage.setItem('vision_ai_theme', 'system');
        if (toggleBtn) toggleBtn.textContent = '💻';
    } else if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('vision_ai_theme', 'light');
        if (toggleBtn) toggleBtn.textContent = '☀️';
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('vision_ai_theme', 'dark');
        if (toggleBtn) toggleBtn.textContent = '🌙';
    }
}

// ============================================================
// AUTHENTICATION
// ============================================================
function getAccessToken() { return localStorage.getItem('vision_ai_access_token'); }

async function authedFetch(url, options = {}) {
    const token = getAccessToken();
    const headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    return fetch(url, { ...options, headers });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text ?? '';
    return div.innerHTML;
}

function showStatus(message, type) {
    const el = document.getElementById('statusMsg');
    el.textContent = message;
    el.className = `status-msg show ${type}`;
    setTimeout(() => el.classList.remove('show'), 4000);
}

function formatPrice(plan) {
    if (plan.price === 0) return `<div class="plan-price">Free</div>`;
    return `<div class="plan-price"><sup>$</sup>${plan.price.toFixed(2)}<span class="per"> / ${escapeHtml(plan.billing)}</span></div>`;
}

let currentPlanId = 'free';

// ============================================================
// LOAD PLANS
// ============================================================
async function loadPlans() {
    try {
        const [plansRes, meRes] = await Promise.all([
            fetch(`${API_BASE}/upgrade/plans`),
            getAccessToken() ? authedFetch(`${API_BASE}/upgrade/me`) : Promise.resolve(null),
        ]);

        if (!plansRes.ok) throw new Error('Could not load plans');
        const plans = await plansRes.json();

        if (meRes && meRes.ok) {
            const me = await meRes.json();
            currentPlanId = me.current_plan || 'free';
            const banner = document.getElementById('currentPlanBanner');
            banner.style.display = 'block';
            banner.innerHTML = `Signed in as <strong>${escapeHtml(me.username)}</strong> — current plan: <strong>${escapeHtml(me.plan_details?.name || me.current_plan)}</strong>`;
        } else if (meRes === null) {
            // Not logged in — plans are still viewable, but actions will redirect to login
        }

        renderPlans(plans);
    } catch (err) {
        document.getElementById('plansContainer').innerHTML =
            `<div class="loading-state">⚠️ ${escapeHtml(err.message || 'Failed to load plans')}</div>`;
    }
}

function renderPlans(plans) {
    const container = document.getElementById('plansContainer');
    const grid = document.createElement('div');
    grid.className = 'plans-grid';

    plans.forEach(plan => {
        const isCurrent = plan.id === currentPlanId;
        const card = document.createElement('div');
        card.className = `plan-card${isCurrent ? ' current' : ''}${plan.id === 'pro' ? ' popular' : ''}`;

        const featuresHtml = (plan.features || []).map(f => `<li>${escapeHtml(f)}</li>`).join('');

        let btnHtml;
        if (isCurrent) {
            btnHtml = `<button class="plan-btn current-btn" disabled>Current Plan</button>`;
        } else if (plan.id === 'free') {
            btnHtml = `<button class="plan-btn downgrade" data-plan="${plan.id}" data-action="downgrade">Downgrade to Free</button>`;
        } else {
            btnHtml = `<button class="plan-btn upgrade" data-plan="${plan.id}" data-action="upgrade">Upgrade to ${escapeHtml(plan.name)}</button>`;
        }

        card.innerHTML = `
            <div class="plan-name">${escapeHtml(plan.name)}</div>
            ${formatPrice(plan)}
            <ul class="plan-features">${featuresHtml}</ul>
            ${btnHtml}
        `;
        grid.appendChild(card);
    });

    container.innerHTML = '';
    container.appendChild(grid);

    grid.querySelectorAll('button[data-action]').forEach(btn => {
        btn.addEventListener('click', () => handlePlanAction(btn.dataset.action, btn.dataset.plan, btn));
    });
}

async function handlePlanAction(action, planId, btnEl) {
    if (!getAccessToken()) {
        window.location.href = '/login.html';
        return;
    }

    btnEl.disabled = true;
    const originalText = btnEl.textContent;
    btnEl.textContent = 'Please wait…';

    try {
        const url = action === 'upgrade' ? `${API_BASE}/upgrade/upgrade` : `${API_BASE}/upgrade/downgrade`;
        const options = { method: 'POST', headers: { 'Content-Type': 'application/json' } };
        if (action === 'upgrade') options.body = JSON.stringify({ plan: planId });

        const res = await authedFetch(url, options);
        const data = await res.json();

        if (res.ok) {
            showStatus(data.message || 'Plan updated!', 'success');
            currentPlanId = planId === 'free' || action === 'downgrade' ? 'free' : planId;
            await loadPlans();
        } else {
            showStatus(data.detail || 'Something went wrong', 'error');
            btnEl.disabled = false;
            btnEl.textContent = originalText;
        }
    } catch (err) {
        showStatus('Connection error. Is the server running?', 'error');
        btnEl.disabled = false;
        btnEl.textContent = originalText;
    }
}

// ============================================================
// INITIALIZATION
// ============================================================
// Apply theme on load (this already updates the icon)
applyTheme(savedTheme);

// Add event listener for theme toggle when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const themeBtn = document.getElementById('themeToggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }
});

// Load plans
loadPlans();
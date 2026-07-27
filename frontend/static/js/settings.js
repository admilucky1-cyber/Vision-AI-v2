// ============================================================
// SETTINGS LOGIC
// ============================================================
const savedTheme = localStorage.getItem('vision_ai_theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

function getAccessToken() { return localStorage.getItem('vision_ai_access_token'); }
function clearTokens() {
    localStorage.removeItem('vision_ai_access_token');
    localStorage.removeItem('vision_ai_refresh_token');
    localStorage.removeItem('vision_ai_user');
    localStorage.removeItem('vision_ai_plan');
}

async function authedFetch(url, options = {}) {
    let token = getAccessToken();
    let headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    let res = await fetch(url, { ...options, headers });
    if (res.status === 401) {
        const refreshToken = localStorage.getItem('vision_ai_refresh_token');
        if (refreshToken) {
            const r = await fetch('/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });
            if (r.ok) {
                const data = await r.json();
                localStorage.setItem('vision_ai_access_token', data.access_token);
                localStorage.setItem('vision_ai_refresh_token', data.refresh_token);
                headers['Authorization'] = `Bearer ${data.access_token}`;
                res = await fetch(url, { ...options, headers });
            }
        }
    }
    return res;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text ?? '';
    return div.innerHTML;
}

function fmtDate(iso) {
    if (!iso) return '—';
    try { return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }); }
    catch { return iso; }
}

function getThemePreference() {
    const stored = localStorage.getItem('vision_ai_theme');
    if (stored) return stored;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

// ============================================================
// THEME FUNCTIONS
// ============================================================
function updateThemeIcon(theme) {
    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
        if (theme === 'light') toggleBtn.textContent = '☀️';
        else if (theme === 'system') toggleBtn.textContent = '💻';
        else toggleBtn.textContent = '🌙';
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

function toggleTheme() {
    const current = localStorage.getItem('vision_ai_theme') || 'dark';
    if (current === 'dark') applyTheme('light');
    else if (current === 'light') applyTheme('system');
    else applyTheme('dark');
}

async function init() {
    if (!getAccessToken()) {
        window.location.href = '/login.html';
        return;
    }
    
    // 🔥 FIX: Apply theme (this already updates the icon)
    const theme = getThemePreference();
    applyTheme(theme);
    
    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) toggleBtn.addEventListener('click', toggleTheme);

    try {
        const [meRes, planRes] = await Promise.all([
            authedFetch('/auth/me'),
            authedFetch('/upgrade/me'),
        ]);
        if (meRes.status === 401) {
            clearTokens();
            window.location.href = '/login.html';
            return;
        }
        if (!meRes.ok) throw new Error('Could not load your profile');
        const me = await meRes.json();
        const plan = planRes.ok ? await planRes.json() : null;
        renderContent(me, plan);
    } catch (err) {
        document.getElementById('content').innerHTML = `<div class="loading-state">⚠️ ${escapeHtml(err.message || 'Failed to load settings')}</div>`;
    }
}

function renderContent(me, plan) {
    const planName = plan?.plan_details?.name || me.plan || 'Free';
    document.getElementById('content').innerHTML = `
        <div class="card">
            <h2>👤 Profile</h2>
            <div class="profile-row"><span class="label">Username</span><span class="value">${escapeHtml(me.username)}</span></div>
            <div class="profile-row" id="nameRow">
                <span class="label">Full name</span>
                <div class="value" id="nameDisplay">
                    <span id="nameText">${escapeHtml(me.full_name || '—')}</span>
                    <button class="edit-icon-btn" onclick="toggleNameEdit()">✏️</button>
                </div>
                <div class="value" id="nameEdit" style="display:none;">
                    <div class="edit-input-group">
                        <input type="text" id="nameInput" value="${escapeHtml(me.full_name || '')}" placeholder="Enter full name">
                        <button class="btn btn-primary" onclick="saveName()" style="padding: 6px 12px; font-size: 12px;">Save</button>
                        <button class="btn btn-outline" onclick="toggleNameEdit()" style="padding: 6px 12px; font-size: 12px;">Cancel</button>
                    </div>
                </div>
            </div>
            <div class="profile-row"><span class="label">Email</span><span class="value">${escapeHtml(me.email || '—')}</span></div>
            <div class="profile-row"><span class="label">Member since</span><span class="value">${fmtDate(me.created_at)}</span></div>
        </div>
        <div class="card">
            <h2>💎 Plan</h2>
            <div class="profile-row">
                <span class="label">Current plan</span>
                <span class="plan-badge">${escapeHtml(planName)}</span>
            </div>
            <div class="card-actions" style="margin-top: 16px;">
                <button class="btn btn-primary" onclick="window.location.href='/upgrade.html'">Manage Plan</button>
            </div>
        </div>
        <div class="card">
            <h2>🔒 Change Password</h2>
            <form id="pwForm">
                <div class="form-group">
                    <label>Current password</label>
                    <input type="password" id="oldPassword" required autocomplete="current-password">
                    <button type="button" class="toggle-password" onclick="togglePw('oldPassword', this)">👁️</button>
                </div>
                <div class="form-group">
                    <label>New password</label>
                    <input type="password" id="newPassword" required minlength="6" autocomplete="new-password">
                    <button type="button" class="toggle-password" onclick="togglePw('newPassword', this)">👁️</button>
                </div>
                <div class="card-actions">
                    <button type="submit" class="btn btn-primary" id="pwSubmitBtn">Update Password</button>
                </div>
                <div class="msg" id="pwMsg"></div>
            </form>
        </div>
        <div class="card">
            <h2>🚪 Session</h2>
            <div class="card-actions">
                <button class="btn btn-danger-outline" onclick="handleLogout()">Log out</button>
            </div>
        </div>
    `;
    document.getElementById('pwForm').addEventListener('submit', handleChangePassword);
}

let isEditingName = false;
function toggleNameEdit() {
    const display = document.getElementById('nameDisplay');
    const edit = document.getElementById('nameEdit');
    isEditingName = !isEditingName;
    display.style.display = isEditingName ? 'none' : 'flex';
    edit.style.display = isEditingName ? 'flex' : 'none';
    if (isEditingName) document.getElementById('nameInput').focus();
}

async function saveName() {
    const input = document.getElementById('nameInput');
    const newName = input.value.trim();
    if (!newName) return;
    const btn = document.querySelector('#nameEdit .btn-primary');
    btn.disabled = true;
    btn.textContent = 'Saving...';
    try {
        const res = await authedFetch('/auth/update-profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: newName })
        });
        if (res.ok) {
            document.getElementById('nameText').textContent = newName;
            toggleNameEdit();
            const storedUser = JSON.parse(localStorage.getItem('vision_ai_user') || '{}');
            storedUser.full_name = newName;
            localStorage.setItem('vision_ai_user', JSON.stringify(storedUser));
            showToast('Profile updated successfully!', 'success');
        } else {
            const data = await res.json();
            showToast(data.detail || 'Failed to update name', 'error');
        }
    } catch (err) {
        showToast('Connection error', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save';
    }
}

function showToast(msg, type = 'info') {
    const el = document.getElementById('pwMsg');
    if (el) {
        el.textContent = msg;
        el.className = `msg show ${type}`;
        setTimeout(() => { el.className = 'msg'; }, 4000);
    }
}

function togglePw(id, btn) {
    const input = document.getElementById(id);
    const isPw = input.type === 'password';
    input.type = isPw ? 'text' : 'password';
    btn.textContent = isPw ? '🙈' : '👁️';
}

async function handleChangePassword(event) {
    event.preventDefault();
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const msgEl = document.getElementById('pwMsg');
    const btn = document.getElementById('pwSubmitBtn');
    msgEl.className = 'msg';
    btn.disabled = true;
    btn.textContent = 'Updating…';
    try {
        const res = await authedFetch('/auth/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
        });
        const data = await res.json();
        if (res.ok) {
            msgEl.textContent = 'Password updated successfully.';
            msgEl.className = 'msg show success';
            document.getElementById('pwForm').reset();
        } else {
            msgEl.textContent = data.detail || 'Could not update password.';
            msgEl.className = 'msg show error';
        }
    } catch (err) {
        msgEl.textContent = 'Connection error. Is the server running?';
        msgEl.className = 'msg show error';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Update Password';
    }
}

async function handleLogout() {
    try {
        await fetch('/auth/logout', { method: 'POST', headers: { 'Authorization': `Bearer ${getAccessToken()}` } });
    } catch {}
    clearTokens();
    window.location.href = '/login.html';
}

// Initialize
init();
// ============================================================
// VISION AI v2.0 - INDEX LOGIC (Production Ready)
// ============================================================

// ============================================================
// 🌙 THEME SYNC
// ============================================================
function applyTheme(theme) {
    if (theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    } else if (theme === 'system') {
        const systemTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', systemTheme);
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

// ============================================================
// AUTHENTICATION & TOKEN MANAGEMENT
// ============================================================
function getAccessToken() { return localStorage.getItem('vision_ai_access_token'); }
function getRefreshToken() { return localStorage.getItem('vision_ai_refresh_token'); }

function setTokens(access, refresh) {
    localStorage.setItem('vision_ai_access_token', access);
    if (refresh) localStorage.setItem('vision_ai_refresh_token', refresh);
}

function clearTokens() {
    localStorage.removeItem('vision_ai_access_token');
    localStorage.removeItem('vision_ai_refresh_token');
    localStorage.removeItem('vision_ai_user');
    localStorage.removeItem('vision_ai_plan');
}

async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;
    try {
        const res = await fetch('/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (res.ok) {
            const data = await res.json();
            setTokens(data.access_token, data.refresh_token);
            return true;
        }
    } catch (e) {
        console.error('Token refresh failed:', e);
    }
    return false;
}

async function authenticatedFetch(url, options = {}) {
    let token = getAccessToken();
    const headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    let res = await fetch(url, { ...options, headers });
    
    if (res.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            headers['Authorization'] = `Bearer ${getAccessToken()}`;
            res = await fetch(url, { ...options, headers });
        } else {
            showToast('Session expired. Please login again.', 'error');
            setTimeout(() => window.location.href = '/login.html', 2000);
        }
    }
    return res;
}

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { error: '⚠️', success: '✅', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${escapeHtml(String(message))}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ============================================================
// SIDEBAR LOGIC (Fully Fixed)
// ============================================================
window.toggleSidebar = function() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        sidebar.classList.toggle('open-mobile');
        document.getElementById('sidebar-overlay').classList.toggle('active');
    } else {
        sidebar.classList.toggle('rail-mode');
        const toolbar = document.getElementById('collapsedToolbar');
        if (sidebar.classList.contains('rail-mode')) {
            toolbar.classList.add('active');
        } else {
            toolbar.classList.remove('active');
        }
    }
}

window.closeMobileSidebar = function() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    if (window.innerWidth <= 768 && sidebar.classList.contains('open-mobile')) {
        sidebar.classList.remove('open-mobile');
        document.getElementById('sidebar-overlay').classList.remove('active');
    }
}

window.forceOpenSearch = function() {
    const sidebar = document.getElementById('sidebar');
    const searchBar = document.getElementById('search-bar');
    const isMobile = window.innerWidth <= 768;

    // If the search bar is already open, treat this as a close toggle.
    if (searchBar && !searchBar.classList.contains('hidden')) {
        searchBar.classList.add('hidden');
        return;
    }

    if (isMobile) {
        if (!sidebar.classList.contains('open-mobile')) {
            sidebar.classList.add('open-mobile');
            document.getElementById('sidebar-overlay').classList.add('active');
        }
    } else {
        if (sidebar.classList.contains('rail-mode')) {
            sidebar.classList.remove('rail-mode');
            document.getElementById('collapsedToolbar').classList.remove('active');
        }
    }
    setTimeout(() => {
        searchBar.classList.remove('hidden');
        document.getElementById('history-search').focus();
    }, 300);
}

// ============================================================
// CHAT HISTORY
// ============================================================
let chatHistory = JSON.parse(localStorage.getItem('vision_ai_history_v2') || '[]');
let currentChatId = null;
let isEditMode = false;

function renderHistory() {
    const list = document.getElementById('historyList');
    if (!list) return;
    list.innerHTML = '';
    
    const groups = {};
    const now = new Date();
    chatHistory.forEach(item => {
        const date = new Date(item.timestamp);
        let key = 'Older';
        if (date.toDateString() === now.toDateString()) key = 'Today';
        else if (date.toDateString() === new Date(now - 86400000).toDateString()) key = 'Yesterday';
        else if (now - date < 604800000) key = '7 Days';
        if (!groups[key]) groups[key] = [];
        groups[key].push(item);
    });

    const order = ['Today', 'Yesterday', '7 Days', 'Older'];
    order.forEach(group => {
        if (!groups[group]) return;
        const section = document.createElement('div');
        section.innerHTML = `<div class="history-section-title">${group}</div>`;
        groups[group].forEach(item => {
            const wrapper = document.createElement('div');
            wrapper.className = `chat-item-wrapper ${item.id === currentChatId ? 'active' : ''}`;
            const titleSpan = document.createElement('span');
            titleSpan.className = 'chat-title';
            titleSpan.textContent = item.title || 'New Chat';
            titleSpan.onclick = () => loadChat(item.id);
            const menuBtn = document.createElement('button');
            menuBtn.className = 'chat-item-options';
            menuBtn.innerHTML = '⋮';
            menuBtn.onclick = (e) => {
                e.stopPropagation();
                toggleChatMenu(menuBtn);
            };
            const menu = document.createElement('div');
            menu.className = 'chat-action-menu';
            menu.innerHTML = `
                <button onclick="renameChat('${item.id}')">✏️ Rename</button>
                <button onclick="deleteChat('${item.id}')" class="delete-btn">🗑️ Delete</button>
            `;
            wrapper.appendChild(titleSpan);
            wrapper.appendChild(menuBtn);
            wrapper.appendChild(menu);
            section.appendChild(wrapper);
        });
        list.appendChild(section);
    });
}

function toggleChatMenu(btn) {
    const menu = btn.nextElementSibling;
    document.querySelectorAll('.chat-action-menu.show').forEach(el => {
        if (el !== menu) el.classList.remove('show');
    });
    if (menu) menu.classList.toggle('show');
}

function renameChat(id) {
    const chat = chatHistory.find(c => c.id === id);
    if (!chat) return;
    const newName = prompt("Rename chat:", chat.title);
    if (newName && newName.trim()) {
        chat.title = newName.trim();
        saveHistory();
        renderHistory();
        if (id === currentChatId) document.getElementById('chatTitle').textContent = chat.title;
    }
}

function deleteChat(id) {
    if (!confirm("Delete this chat?")) return;
    const index = chatHistory.findIndex(c => c.id === id);
    if (index !== -1) {
        chatHistory.splice(index, 1);
        saveHistory();
        if (id === currentChatId) startNewChat();
        else renderHistory();
    }
}

function startNewChat() {
    currentChatId = Date.now().toString();
    chatHistory.unshift({ id: currentChatId, title: 'New Chat', timestamp: Date.now(), messages: [] });
    saveHistory();
    renderHistory();
    document.getElementById('chatOutput').innerHTML = '';
    document.getElementById('chatTitle').textContent = 'New Chat';
    if (window.innerWidth <= 768) closeMobileSidebar();
}

function saveHistory() { localStorage.setItem('vision_ai_history_v2', JSON.stringify(chatHistory)); }

function loadChat(id) {
    const chat = chatHistory.find(c => c.id === id);
    if (!chat) return;
    currentChatId = id;
    const output = document.getElementById('chatOutput');
    output.innerHTML = '';
    document.getElementById('chatTitle').textContent = chat.title;
    chat.messages.forEach(msg => {
        addMessage(msg.role, msg.text, msg.images || null, msg.modelUsed || null);
    });
    renderHistory();
    if (window.innerWidth <= 768) closeMobileSidebar();
    output.querySelectorAll('pre code').forEach((block) => {
        if (window.hljs) hljs.highlightElement(block);
    });
}

// ============================================================
// CACHE MANAGEMENT
// ============================================================
async function clearAllCaches() {
    try {
        const res = await authenticatedFetch('/chat/clear-cache', { method: 'POST' });
        if (res.ok) { showToast('RAG cache cleared', 'success'); }
    } catch (e) { showToast('Failed to clear cache', 'error'); }
}

// ============================================================
// CHAT FUNCTIONS
// ============================================================
function addMessage(role, text, images = null, modelUsed = null) {
    const output = document.getElementById('chatOutput');
    if (!output) return;
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    let html = `<div class="message-bubble" onclick="${role === 'user' ? 'editMessage(this)' : ''}">`;
    if (role === 'ai' && modelUsed) {
        html += `<span class="model-used">🤖 <span>${modelUsed}</span></span>`;
    }
    if (role === 'ai' && typeof text === 'string') {
        let cleanHtml;
        if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
            try {
                const parsedHtml = marked.parse(text);
                cleanHtml = window.DOMPurify ? DOMPurify.sanitize(parsedHtml) : parsedHtml;
            } catch (e) {
                console.error('Markdown parsing failed:', e);
                cleanHtml = escapeHtml(text);
            }
        } else {
            cleanHtml = escapeHtml(text);
        }
        html += `<div class="markdown-content">${cleanHtml}</div>`;
    } else {
        html += `<div style="white-space: pre-wrap;">${escapeHtml(text)}</div>`;
    }
    const hasImages = images && Array.isArray(images) && images.length > 0;
    if (hasImages) {
        html += '<div class="ai-image-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-top:12px;"></div>';
    }
    html += '</div>';
    row.innerHTML = html;
    if (hasImages) {
        const grid = row.querySelector('.ai-image-grid');
        images.forEach(img => {
            const raw = (img && typeof img.data === 'string') ? img.data : '';
            const isDataUri = /^data:image\/(png|jpe?g|gif|webp);base64,[A-Za-z0-9+/=]+$/.test(raw);
            const isBareBase64 = /^[A-Za-z0-9+/=]+$/.test(raw) && raw.length > 0;
            const src = isDataUri ? raw : (isBareBase64 ? `data:image/png;base64,${raw}` : '');
            if (!src) return;
            const imgEl = document.createElement('img');
            imgEl.src = src;
            imgEl.style.cssText = 'width:100%;height:150px;object-fit:cover;border-radius:8px;cursor:pointer;border:1px solid #2a2a4a;';
            imgEl.addEventListener('click', () => window.open(src, '_blank'));
            grid.appendChild(imgEl);
        });
    }
    output.appendChild(row);
    output.scrollTop = output.scrollHeight;
    row.querySelectorAll('pre code').forEach((block) => {
        if (window.hljs) hljs.highlightElement(block);
    });
}

function editMessage(element) {
    const textDiv = element.querySelector('.markdown-content') || element.querySelector('div[style*="white-space"]');
    const currentText = textDiv ? textDiv.textContent : '';
    const inputField = document.getElementById('message');
    inputField.value = currentText;
    inputField.focus();
    inputField.setSelectionRange(currentText.length, currentText.length);
    document.querySelectorAll('.message-bubble.editing').forEach(el => el.classList.remove('editing'));
    element.classList.add('editing');
    window.editingElement = element;
    window.editingRow = element.closest('.message-row');
    isEditMode = true;
    document.getElementById('editActions').classList.add('active');
}

function cancelEdit() {
    window.editingElement = null;
    window.editingRow = null;
    document.querySelectorAll('.message-bubble.editing').forEach(el => el.classList.remove('editing'));
    document.getElementById('message').value = '';
    document.getElementById('editActions').classList.remove('active');
    isEditMode = false;
}

function sendEdit() {
    if (!window.editingElement) { cancelEdit(); return; }
    sendMessage();
}

// ============================================================
// DYNAMIC LOADING STATUS (UPDATED)
// ============================================================
const LOADING_STATUSES = [
    "Analyzing your request...",
    "Thinking...",
    "Contacting AI model...",
    "Model selection...",
    "Checking internet connection...",
    "Almost there...",
];

let loadingStatusIndex = 0;
let loadingStatusInterval = null;

function showLoading() {
    const output = document.getElementById('chatOutput');
    removeLoading();
    
    // Reset the rotator
    loadingStatusIndex = 0;
    if (loadingStatusInterval) {
        clearInterval(loadingStatusInterval);
        loadingStatusInterval = null;
    }

    const row = document.createElement('div');
    row.className = 'message-row ai';
    row.id = 'loadingMsg';
    row.innerHTML = `
        <div class="message-bubble">
            <div class="typing-indicator">
                <div class="dots"><span></span><span></span><span></span></div>
                <span class="blink-text" id="loadingStatus">${LOADING_STATUSES[0]}</span>
            </div>
        </div>
    `;
    output.appendChild(row);
    output.scrollTop = output.scrollHeight;

    // 🔥 NEW: Rotate the text every 1.5 seconds
    loadingStatusInterval = setInterval(() => {
        loadingStatusIndex = (loadingStatusIndex + 1) % LOADING_STATUSES.length;
        const el = document.getElementById('loadingStatus');
        if (el) el.textContent = LOADING_STATUSES[loadingStatusIndex];
    }, 1500);
}

function updateLoadingStatus(msg) {
    // Instead of overriding the text, we just immediately jump to that specific status
    const el = document.getElementById('loadingStatus');
    if (el) {
        el.textContent = msg;
        // We stop the rotator when a specific event happens
        if (msg === "Generating response...") {
            if (loadingStatusInterval) {
                clearInterval(loadingStatusInterval);
                loadingStatusInterval = null;
            }
        }
    }
}

function removeLoading() {
    const el = document.getElementById('loadingMsg');
    if (el) el.remove();
    
    // Clean up the interval when the loading is removed
    if (loadingStatusInterval) {
        clearInterval(loadingStatusInterval);
        loadingStatusInterval = null;
    }
}

async function sendMessage() {
    const msgInput = document.getElementById('message');
    const msg = msgInput.value.trim();
    const fileInput = document.getElementById('fileInput');
    const sendBtn = document.getElementById('sendBtn');
    
    // Snapshot the files BEFORE anything else
    const filesToUpload = Array.from(fileInput.files); 

    if (!msg && filesToUpload.length === 0) return;

    const wasEditing = isEditMode;
    if (wasEditing) cancelEdit();
    if (!currentChatId) startNewChat();
    const chat = chatHistory.find(c => c.id === currentChatId);
    if (!chat) return;

    // Edit logic
    if (wasEditing && window.editingElement) {
        const rowToRemove = window.editingRow;
        const oldText = window.editingElement.querySelector('.markdown-content')?.textContent || '';
        const msgIndex = chat.messages.findIndex(m => m.role === 'user' && m.text === oldText);
        if (msgIndex !== -1) chat.messages.splice(msgIndex, 1);
        if (rowToRemove) rowToRemove.remove();
        window.editingElement = null;
        window.editingRow = null;
    }

    let userMessage = msg;
    // Use 'filesToUpload' instead of 'fileInput.files'
    if (filesToUpload.length > 0) {
        const fileList = filesToUpload
            .map(f => `📄 ${f.name} (${(f.size/1024).toFixed(1)}KB)`)
            .join('\n');
        userMessage = `Uploading Files:\n${fileList}\n\nMessage: ${msg}`;
    }
    addMessage('user', userMessage);
    
    // Use 'filesToUpload' for history
    chat.messages.push({ role: 'user', text: userMessage, filesCount: filesToUpload.length, fileNames: filesToUpload.map(f => f.name) });
    
    if (chat.title === 'New Chat') {
        chat.title = msg.substring(0, 40) + (msg.length > 40 ? '...' : '');
    }
    saveHistory();
    renderHistory();
    document.getElementById('chatTitle').textContent = chat.title;
    msgInput.value = '';
    fileInput.value = ''; // Safe to clear NOW because we already snapped 'filesToUpload'
    renderFilePreview(); // Clear the preview chips too
    sendBtn.disabled = true;
    showLoading("Analyzing your request...");

    const formData = new FormData();
    formData.append('message', msg);
    formData.append('model', document.getElementById('modelSelector').value);
    formData.append('generate_images', 'true');
    
    // Use the snapshot variable here!
    for (const file of filesToUpload) {
        formData.append('files', file); 
    }


    try {
        updateLoadingStatus("Contacting AI model...");
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s safety timeout
        let res;
        try {
            res = await authenticatedFetch('/chat/send', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
        } finally {
            clearTimeout(timeoutId);
        }
        updateLoadingStatus("Generating response...");
        const data = await res.json();
        removeLoading();
        sendBtn.disabled = false;
        if (res.ok) {
            addMessage('ai', data.answer, data.images || null, data.model_used || null);
            chat.messages.push({ role: 'ai', text: data.answer, images: data.images, modelUsed: data.model_used, });
            saveHistory();
            showToast(`Response from ${data.model_used} in ${data.response_time}s`, 'success', 2000);
        } else {
            addMessage('ai', '❌ Error: ' + (data.detail || data.error || 'Unknown error'));
            showToast(data.detail || 'Request failed', 'error');
        }
    } catch (err) {
        removeLoading();
        sendBtn.disabled = false;
        if (err.name === 'AbortError') {
            addMessage('ai', '❌ The request timed out. The AI model may be taking too long or the server may be unresponsive.');
            showToast('Request timed out after 60s.', 'error');
        } else {
            addMessage('ai', '❌ Connection error: ' + err.message);
            showToast('Connection error. Please check your network.', 'error');
        }
    }
}

// ============================================================
// 👤 USER PROFILE MANAGEMENT
// ============================================================
function renderUserProfile() {
    const footer = document.getElementById('sidebarFooter');
    if (!footer) return;
    const userData = JSON.parse(localStorage.getItem('vision_ai_user') || '{}');
    const plan = localStorage.getItem('vision_ai_plan') || 'free';

    if (!userData.username) {
        footer.innerHTML = `
            <a href="/login.html" style="display:flex;align-items:center;justify-content:center;width:100%;padding:12px;background:linear-gradient(135deg, #00C6FF, #7B68EE);color:#fff;border-radius:10px;text-decoration:none;font-weight:600;font-size:14px;gap:8px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
                Sign In
            </a>
        `;
        return;
    }

    const nameToUse = userData.full_name || userData.username || 'User';
    const initials = nameToUse.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

    footer.innerHTML = `
        <div class="user-profile-container" onclick="window.toggleProfileDropdown()" style="display:flex;align-items:center;gap:12px;cursor:pointer;padding:6px 8px;border-radius:10px;width:100%;">
            <div class="user-avatar" style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg, #7B68EE, #00C6FF);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:16px;text-transform:uppercase;">
                ${initials}
            </div>
            <div style="flex:1;min-width:0;">
                <div style="font-weight:600;font-size:14px;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(nameToUse)}</div>
                <div style="font-size:10px;font-weight:700;color:#00C6FF;background:rgba(0,198,255,0.1);padding:1px 8px;border-radius:12px;width:fit-content;margin-top:2px;border:1px solid rgba(0,198,255,0.2);">${escapeHtml(plan).charAt(0).toUpperCase() + escapeHtml(plan).slice(1)}</div>
            </div>
        </div>
        <div id="profileDropdown" style="display:none;position:absolute;bottom:calc(100% + 12px);left:16px;width:calc(100% - 32px);background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:12px;box-shadow:var(--shadow-lg);padding:6px;flex-direction:column;gap:2px;z-index:50;">
            <a href="/settings.html" style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;color:var(--text-main);font-size:14px;text-decoration:none;cursor:pointer;transition:background 0.2s;">⚙️ Settings</a>
            <a href="/upgrade.html" style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;color:var(--text-main);font-size:14px;text-decoration:none;cursor:pointer;transition:background 0.2s;">💎 Upgrade Plan</a>
            <div onclick="window.performLogout()" style="display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;color:#ef4444;font-size:14px;cursor:pointer;transition:background 0.2s;">🚪 Log out</div>
        </div>
    `;
}

window.toggleProfileDropdown = function() {
    const dropdown = document.getElementById('profileDropdown');
    if (dropdown) {
        dropdown.style.display = (dropdown.style.display === 'flex') ? 'none' : 'flex';
    }
}

document.addEventListener('click', function(event) {
    const footer = document.getElementById('sidebarFooter');
    const dropdown = document.getElementById('profileDropdown');
    if (dropdown && footer && !footer.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

// ============================================================
// AUTHENTICATION
// ============================================================
async function checkAuth() {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');
    const urlRefresh = urlParams.get('refresh');
    if (urlToken) {
        setTokens(urlToken, urlRefresh);
        window.history.replaceState({}, document.title, "/");
    }
    const token = getAccessToken();
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    try {
        const res = await authenticatedFetch('/auth/me');
        if (!res.ok) {
            clearTokens();
            window.location.href = '/login.html';
        } else {
            const data = await res.json();
            localStorage.setItem('vision_ai_user', JSON.stringify(data));
            localStorage.setItem('vision_ai_plan', data.plan || 'free');
            renderUserProfile(); 
            updateStatus(true);
        }
    } catch {
        window.location.href = '/login.html';
    }
}

window.performLogout = function() {
    if (!confirm("Log out?")) return;
    try {
        fetch('/auth/logout', { method: 'POST', headers: { 'Authorization': `Bearer ${getAccessToken()}` } });
    } finally {
        clearTokens();
        window.location.href = '/login.html';
    }
}

function updateStatus(online) {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    if (dot && text) {
        dot.className = online ? 'status-dot' : 'status-dot offline';
        text.textContent = online ? 'Online' : 'Offline';
        text.style.color = online ? '#00C6FF' : '#ff6b6b';
    }
}

// ============================================================
// 🌙 FLOATING THEME TOGGLE
// ============================================================
function updateThemeIcon(theme) {
    const btn = document.getElementById('floatingThemeToggle');
    if (btn) {
        if (theme === 'light') btn.textContent = '☀️';
        else if (theme === 'system') btn.textContent = '💻';
        else btn.textContent = '🌙';
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    let nextTheme;
    if (current === 'dark') {
        nextTheme = 'light';
    } else if (current === 'light') {
        nextTheme = 'system';
    } else {
        nextTheme = 'dark';
    }
    applyTheme(nextTheme);
    localStorage.setItem('vision_ai_theme', nextTheme);
    updateThemeIcon(nextTheme);
}

// ============================================================
// EVENT LISTENERS
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    const savedTheme = localStorage.getItem('vision_ai_theme') || 'dark';
    applyTheme(savedTheme);
    updateThemeIcon(savedTheme);

    // Listen for system theme changes if using system theme
    if (savedTheme === 'system') {
        window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
            applyTheme('system');
            updateThemeIcon('system');
        });
    }

    try {
        if (chatHistory.length === 0) startNewChat();
        else loadChat(chatHistory[0].id);
    } catch (e) {
        console.error('Failed to load initial chat:', e);
    }

    const messageInput = document.getElementById('message');
    if (messageInput) {
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 150) + 'px';
        });
    }

    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', renderFilePreview);
    }

    console.log('👁️ Vision AI v2.0 - Ready');
});

// ============================================================
// FILE PREVIEW (attach feedback)
// ============================================================
function renderFilePreview() {
    const fileInput = document.getElementById('fileInput');
    const previewArea = document.getElementById('filePreviewArea');
    if (!fileInput || !previewArea) return;

    previewArea.innerHTML = '';
    const files = Array.from(fileInput.files);
    if (files.length === 0) return;

    files.forEach((file, index) => {
        const chip = document.createElement('div');
        chip.className = 'file-chip';
        chip.innerHTML = `
            <span>📄</span>
            <span class="file-chip-name" title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
            <button type="button" class="file-chip-remove" title="Remove file">✕</button>
        `;
        chip.querySelector('.file-chip-remove').addEventListener('click', () => removeSelectedFile(index));
        previewArea.appendChild(chip);
    });
}

function removeSelectedFile(index) {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;
    const dt = new DataTransfer();
    Array.from(fileInput.files).forEach((file, i) => {
        if (i !== index) dt.items.add(file);
    });
    fileInput.files = dt.files;
    renderFilePreview();
}
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
function getAccessToken() { 
    return localStorage.getItem('vision_ai_access_token'); 
}

function getRefreshToken() { 
    return localStorage.getItem('vision_ai_refresh_token'); 
}

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
    const headers = { 
        ...options.headers, 
        'Authorization': `Bearer ${token}` 
    };
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
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'toastContainer';
        newContainer.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 99999;
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-width: 400px;
            width: 100%;
        `;
        document.body.appendChild(newContainer);
        showToast(message, type, duration);
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { error: '⚠️', success: '✅', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${escapeHtml(String(message))}</span>`;
    toast.style.cssText = `
        position: relative;
        padding: 12px 16px;
        border-radius: 10px;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-lg);
        display: flex;
        align-items: center;
        gap: 10px;
        animation: toastIn 0.3s ease-out;
        backdrop-filter: blur(8px);
        font-size: 14px;
        color: var(--text-main);
        ${type === 'error' ? 'border-left: 4px solid #ef4444;' : ''}
        ${type === 'success' ? 'border-left: 4px solid #22c55e;' : ''}
        ${type === 'info' ? 'border-left: 4px solid #00C6FF;' : ''}
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Add toast animations if not already in CSS
if (!document.getElementById('toastStyles')) {
    const style = document.createElement('style');
    style.id = 'toastStyles';
    style.textContent = `
        @keyframes toastIn {
            from { opacity: 0; transform: translateY(20px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes toastOut {
            from { opacity: 1; transform: translateY(0) scale(1); }
            to { opacity: 0; transform: translateY(20px) scale(0.95); }
        }
    `;
    document.head.appendChild(style);
}

// ============================================================
// SIDEBAR LOGIC
// ============================================================
window.toggleSidebar = function() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    // Always force reflow to avoid stuck state after resize
    void sidebar.offsetWidth;
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        sidebar.classList.toggle('open-mobile');
        let overlay = document.getElementById('sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'sidebar-overlay';
            overlay.className = 'sidebar-overlay';
            overlay.onclick = () => closeMobileSidebar();
            document.body.appendChild(overlay);
        }
        if (overlay) overlay.classList.toggle('active');
    } else {
        sidebar.classList.toggle('rail-mode');
        const toolbar = document.getElementById('collapsedToolbar');
        if (sidebar.classList.contains('rail-mode')) {
            if (toolbar) toolbar.classList.add('active');
        } else {
            if (toolbar) toolbar.classList.remove('active');
        }
    }
}

window.closeMobileSidebar = function() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    if (window.innerWidth <= 768 && sidebar.classList.contains('open-mobile')) {
        sidebar.classList.remove('open-mobile');
        const overlay = document.getElementById('sidebar-overlay');
        if (overlay) overlay.classList.remove('active');
    }
}

window.forceOpenSearch = function() {
    const sidebar = document.getElementById('sidebar');
    const searchBar = document.getElementById('search-bar');
    const isMobile = window.innerWidth <= 768;

    if (searchBar && !searchBar.classList.contains('hidden')) {
        searchBar.classList.add('hidden');
        return;
    }

    if (isMobile) {
        if (!sidebar.classList.contains('open-mobile')) {
            sidebar.classList.add('open-mobile');
            const overlay = document.getElementById('sidebar-overlay');
            if (overlay) overlay.classList.add('active');
        }
    } else {
        if (sidebar.classList.contains('rail-mode')) {
            sidebar.classList.remove('rail-mode');
            const toolbar = document.getElementById('collapsedToolbar');
            if (toolbar) toolbar.classList.remove('active');
        }
    }
    setTimeout(() => {
        if (searchBar) {
            searchBar.classList.remove('hidden');
            const searchInput = document.getElementById('history-search');
            if (searchInput) searchInput.focus();
        }
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
        if (id === currentChatId) {
            const titleEl = document.getElementById('chatTitle');
            if (titleEl) titleEl.textContent = chat.title;
        }
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
    const output = document.getElementById('chatOutput');
    if (output) output.innerHTML = '';
    const titleEl = document.getElementById('chatTitle');
    if (titleEl) titleEl.textContent = 'New Chat';
    if (window.innerWidth <= 768) closeMobileSidebar();
}

function saveHistory() { 
    localStorage.setItem('vision_ai_history_v2', JSON.stringify(chatHistory)); 
}

function loadChat(id) {
    const chat = chatHistory.find(c => c.id === id);
    if (!chat) return;
    currentChatId = id;
    const output = document.getElementById('chatOutput');
    if (!output) return;
    output.innerHTML = '';
    const titleEl = document.getElementById('chatTitle');
    if (titleEl) titleEl.textContent = chat.title;
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
        if (!res) {
            showToast('Please log in again', 'error');
            return;
        }
        let data = {};
        try { data = await res.json(); } catch (_) {}
        if (res.ok) {
            showToast(data.message || 'Caches cleared', 'success');
        } else {
            const detail = data.detail || data.message || ('HTTP ' + res.status);
            showToast('Failed to clear cache: ' + detail, 'error', 5000);
        }
    } catch (e) {
        showToast('Failed to clear cache: ' + e.message, 'error');
    }
}

// ============================================================
// CHAT FUNCTIONS (✅ UPDATED WITH BADGES)
// ============================================================
function addMessage(role, text, images = null, modelUsed = null, ragCount = 0, searchUsed = false, imageCount = 0) {
    const output = document.getElementById('chatOutput');
    if (!output) return;
    
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    
    let html = `<div class="message-bubble" onclick="${role === 'user' ? 'editMessage(this)' : ''}">`;
    
    // 🟢 NEW: Render Badges for AI messages
    if (role === 'ai') {
        let badges = [];
        if (ragCount > 0) badges.push(`📄 ${ragCount} document${ragCount > 1 ? 's' : ''}`);
        if (searchUsed) badges.push('🌐 Web search');
        if (imageCount > 0) badges.push(`🖼️ ${imageCount} image${imageCount > 1 ? 's' : ''}`);
        if (badges.length > 0) {
            html += `<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">`;
            badges.forEach(b => {
                html += `<span style="background:rgba(0,198,255,0.1);color:#00C6FF;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">${b}</span>`;
            });
            html += `</div>`;
        }
    }
    
    if (role === 'ai' && modelUsed) {
        const modelClass = 'model-' + String(modelUsed || 'auto').toLowerCase().replace(/[^a-z0-9]+/g, '-');
        html += `<span class="model-used ${modelClass}"><span class="model-dot"></span><span>${escapeHtml(modelUsed)}</span></span>`;
    }
    
    if (role === 'ai' && typeof text === 'string') {
        let cleanHtml;
        // Soft-format plain transcripts into readable paragraphs when no markdown structure
        let src = text;
        const looksPlain = !/(^|\n)#{1,3}\s|(^|\n)[-*]\s|(^|\n)\d+\.\s|```/.test(src);
        if (looksPlain && src.length > 600) {
            // Break very long lines into paragraph chunks every ~3-4 sentences
            src = src
                .replace(/\[Music\]/gi, '\n\n*[Music]*\n\n')
                .replace(/([.!?])\s+(?=[A-Z])/g, '$1\n\n')
                .replace(/\n{3,}/g, '\n\n');
        }
        if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
            try {
                if (typeof marked.setOptions === 'function') {
                    marked.setOptions({ breaks: true, gfm: true });
                }
                const parsedHtml = marked.parse(src);
                cleanHtml = window.DOMPurify ? DOMPurify.sanitize(parsedHtml) : parsedHtml;
            } catch (e) {
                console.error('Markdown parsing failed:', e);
                cleanHtml = escapeHtml(text).replace(/\n/g, '<br>');
            }
        } else {
            cleanHtml = escapeHtml(text).replace(/\n/g, '<br>');
        }
        const isLong = text.length > 1800;
        const bodyClass = isLong ? 'markdown-content msg-long-body' : 'markdown-content';
        html += `<div class="${bodyClass}">${cleanHtml}</div>`;
        // mark download links for forced download
        cleanHtml = cleanHtml.replace(
            /href="([^"]*\/upload\/downloads\/[^"]+)"/g,
            'href="$1" download target="_blank" rel="noopener" class="dl-file-link"'
        );
        html += `<div class="msg-actions">
            <button type="button" class="msg-action-btn" onclick="copyMessageText(this)" title="Copy">📋 Copy</button>
            <button type="button" class="msg-action-btn speak-btn" onclick="event.stopPropagation();speakMessage(this)" title="Read aloud">🔊 Speak</button>
            <button type="button" class="msg-action-btn" onclick="event.stopPropagation();stopSpeaking()" title="Stop voice">⏹</button>
            <button type="button" class="msg-action-btn" onclick="toggleExpandMessage(this)" title="Expand height">↕ Height</button>
            <button type="button" class="msg-action-btn" onclick="toggleWideMessage(this)" title="Wider message">↔ Width</button>
            <button type="button" class="msg-action-btn" onclick="zoomMessage(this, 1.1)" title="Zoom in">🔍+</button>
            <button type="button" class="msg-action-btn" onclick="zoomMessage(this, 0.9)" title="Zoom out">🔍−</button>
            <button type="button" class="msg-action-btn" onclick="focusMessageFullscreen(this)" title="Fullscreen">⛶ Full</button>
        </div>`;
    } else {
        html += `<div style="white-space: pre-wrap;">${escapeHtml(text)}</div>`;
    }
    
    const hasImages = images && Array.isArray(images) && images.length > 0;
    if (hasImages) {
        html += '<div class="ai-image-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-top:12px;"></div>';
    }
    html += '</div>';
    row.innerHTML = html;
    row.querySelectorAll('a[href*="/upload/downloads/"]').forEach(function (a) {
        a.setAttribute('download', '');
        a.classList.add('dl-file-link');
        a.addEventListener('click', function (ev) {
            const href = a.getAttribute('href');
            if (!href) return;
            const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || '');
            if (!isMobile) return; // desktop: normal navigation + Content-Disposition is enough
            ev.preventDefault();
            forceMobileDownload(href, a.getAttribute('download') || '').catch(function () {
                window.location.href = href;
            });
        });
    });

    
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
    if (!inputField) return;
    
    inputField.value = currentText;
    inputField.focus();
    inputField.setSelectionRange(currentText.length, currentText.length);
    document.querySelectorAll('.message-bubble.editing').forEach(el => el.classList.remove('editing'));
    element.classList.add('editing');
    window.editingElement = element;
    window.editingRow = element.closest('.message-row');
    isEditMode = true;
    const editActions = document.getElementById('editActions');
    if (editActions) editActions.classList.add('active');
}

function cancelEdit() {
    window.editingElement = null;
    window.editingRow = null;
    document.querySelectorAll('.message-bubble.editing').forEach(el => el.classList.remove('editing'));
    const inputField = document.getElementById('message');
    if (inputField) inputField.value = '';
    const editActions = document.getElementById('editActions');
    if (editActions) editActions.classList.remove('active');
    isEditMode = false;
}

function sendEdit() {
    if (!window.editingElement) { 
        cancelEdit(); 
        return; 
    }
    sendMessage();
}

// ============================================================
// DYNAMIC LOADING / TYPING INDICATOR
// ============================================================
const LOADING_STATUSES = [
    { title: 'Receiving your request…', sub: 'Files, links, and text are being prepared' },
    { title: 'Processing documents…', sub: 'PDF / image OCR can take up to 1–2 minutes' },
    { title: 'Fetching media / search…', sub: 'YouTube and web data if needed' },
    { title: 'Running AI model…', sub: 'Generating a detailed answer' },
    { title: 'Finishing response…', sub: 'Formatting and diagrams' },
];

let loadingStatusIndex = 0;
let loadingStatusInterval = null;

function showLoading() {
    const output = document.getElementById('chatOutput');
    if (!output) return;

    loadingStatusIndex = 0;
    if (loadingStatusInterval) {
        clearInterval(loadingStatusInterval);
        loadingStatusInterval = null;
    }

    removeLoading();

    const row = document.createElement('div');
    row.className = 'message-row ai';
    row.id = 'loadingRow';
    row.innerHTML = `
        <div class="message-bubble">
            <div class="typing-indicator" role="status" aria-live="polite">
                <div class="loader-ring" aria-hidden="true"></div>
                <div class="loader-dots" aria-hidden="true"><span></span><span></span><span></span></div>
                <div class="loader-text-wrap">
                    <span id="loadingStatus">${LOADING_STATUSES[0].title}</span>
                    <span id="loadingSub">${LOADING_STATUSES[0].sub}</span>
                    <div class="progress-track" aria-hidden="true"><div class="progress-fill" id="loadingProgress"></div></div>
                    <span id="loadingEta" class="loading-eta">Working… large files can take 30–120s</span>
                </div>
            </div>
        </div>
    `;
    output.appendChild(row);
    output.scrollTop = output.scrollHeight;

    window._progressPct = 8;
    const pEl = document.getElementById('loadingProgress');
    if (pEl) pEl.style.width = '8%';
    if (window._progressTimer) clearInterval(window._progressTimer);
    window._progressTimer = setInterval(() => {
        // asymptotic progress (never hits 100 until done)
        window._progressPct = Math.min(92, window._progressPct + Math.max(0.4, (92 - window._progressPct) * 0.035));
        const bar = document.getElementById('loadingProgress');
        if (bar) bar.style.width = window._progressPct.toFixed(1) + '%';
        const eta = document.getElementById('loadingEta');
        if (eta) {
            if (window._progressPct < 25) eta.textContent = 'Starting…';
            else if (window._progressPct < 50) eta.textContent = 'Reading files / links…';
            else if (window._progressPct < 75) eta.textContent = 'Model is thinking…';
            else eta.textContent = 'Almost done…';
        }
    }, 400);
    loadingStatusInterval = setInterval(() => {
        loadingStatusIndex = (loadingStatusIndex + 1) % LOADING_STATUSES.length;
        const el = document.getElementById('loadingStatus');
        const sub = document.getElementById('loadingSub');
        const item = LOADING_STATUSES[loadingStatusIndex];
        if (el) el.textContent = item.title;
        if (sub) sub.textContent = item.sub;
    }, 2200);
}


function updateLoadingStatus(msg) {
    const el = document.getElementById('loadingStatus');
    const sub = document.getElementById('loadingSub');
    if (el) {
        if (loadingStatusInterval) {
            clearInterval(loadingStatusInterval);
            loadingStatusInterval = null;
        }
        el.textContent = msg;
    }
    if (sub) sub.textContent = 'Working…';
}

function removeLoading() {
    if (window._progressTimer) { clearInterval(window._progressTimer); window._progressTimer = null; }
    const bar = document.getElementById('loadingProgress');
    if (bar) bar.style.width = '100%';

    const el = document.getElementById('loadingRow') || document.getElementById('loadingMsg');
    if (el) el.remove();
    if (loadingStatusInterval) {
        clearInterval(loadingStatusInterval);
        loadingStatusInterval = null;
    }
}


function stopGeneration() {
    window._userStopped = true;
    try {
        if (window._activeChatAbort) {
            window._activeChatAbort.abort();
            window._activeChatAbort = null;
        }
    } catch (_) {}
    removeLoading();
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) sendBtn.disabled = false;
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) stopBtn.hidden = true;
    // Restore last draft so user can edit
    const input = document.getElementById('message');
    if (input && window._lastDraftMessage) {
        input.value = window._lastDraftMessage;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.focus();
    }
    showToast('Stopped — edit your message and send again', 'info', 3500);
}
window.stopGeneration = stopGeneration;

async function sendMessage() {
    const msgInput = document.getElementById('message');
    if (!msgInput) return;
    const msg = msgInput.value.trim();
    const fileInput = document.getElementById('fileInput');
    const sendBtn = document.getElementById('sendBtn');
    
    const filesToUpload = Array.from(fileInput ? fileInput.files : []); 

    if (!msg && filesToUpload.length === 0) return;
    window._lastDraftMessage = msg;

    const wasEditing = isEditMode;
    if (wasEditing) cancelEdit();
    if (!currentChatId) startNewChat();
    const chat = chatHistory.find(c => c.id === currentChatId);
    if (!chat) return;

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
    if (filesToUpload.length > 0) {
        const fileList = filesToUpload
            .map(f => `📄 ${escapeHtml(f.name)} (${(f.size/1024).toFixed(1)}KB)`)
            .join('\n');
        userMessage = `Uploading Files:\n${fileList}\n\nMessage: ${msg}`;
    }
    addMessage('user', userMessage);
    
    chat.messages.push({ 
        role: 'user', 
        text: userMessage, 
        filesCount: filesToUpload.length, 
        fileNames: filesToUpload.map(f => f.name) 
    });
    
    if (chat.title === 'New Chat') {
        chat.title = msg.substring(0, 40) + (msg.length > 40 ? '...' : '');
    }
    saveHistory();
    renderHistory();
    const titleEl = document.getElementById('chatTitle');
    if (titleEl) titleEl.textContent = chat.title;
    msgInput.value = '';
    if (fileInput) fileInput.value = ''; 
    renderFilePreview(); 
    if (sendBtn) sendBtn.disabled = true;
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) stopBtn.hidden = false;
    showLoading();

    const formData = new FormData();
    formData.append('message', msg);
    // Short context so "what is this chat about" uses this thread
    try {
        const recent = (chat.messages || []).slice(-6).map(m => (m.role + ': ' + (m.text || '').slice(0, 200))).join('\n');
        if (recent) formData.append('history_hint', recent.slice(0, 1500));
    } catch (_) {}
    const modelSelector = document.getElementById('modelSelector');
    formData.append('model', modelSelector ? modelSelector.value : 'default');
    formData.append('generate_images', 'true');
    const chatLang = localStorage.getItem('vision_ai_chat_lang') || 'auto';
    if (chatLang && chatLang !== 'auto') {
        formData.append('preferred_language', chatLang);
    }
    
    for (const file of filesToUpload) {
        formData.append('files', file); 
    }

    try {
        updateLoadingStatus("Contacting AI model...");
        const controller = new AbortController();
        window._activeChatAbort = controller;
        // Downloads / long transcripts need more than the default chat budget
        const isHeavy = /download|transcript|youtube\.com|youtu\.be|mp3|1080p|720p/i.test(userMessage || '');
        const timeoutMs = isHeavy ? 600000 : 90000; // 10 min for media, 90s for chat
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        let res;
        try {
            res = await authenticatedFetch('/chat/send', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
        } finally {
            clearTimeout(timeoutId);
            window._activeChatAbort = null;
        }
        updateLoadingStatus("Generating response...");
        const data = await res.json();
        removeLoading();
        if (sendBtn) sendBtn.disabled = false;
        if (stopBtn) stopBtn.hidden = true;
        if (res.ok) {
            // ✅ UPDATED: Pass badge data to addMessage
            addMessage(
                'ai', 
                data.answer, 
                data.images || null, 
                data.model_used || null,
                data.rag_files_loaded || 0,
                data.search_performed || false,
                data.images_generated || 0
            );
            chat.messages.push({ 
                role: 'ai', 
                text: data.answer, 
                images: data.images, 
                modelUsed: data.model_used 
            });
            saveHistory();
            showToast(`Response from ${data.model_used} in ${data.response_time}s`, 'success', 2000);
        } else {
            addMessage('ai', '❌ Error: ' + (data.detail || data.error || 'Unknown error'));
            showToast(data.detail || 'Request failed', 'error');
        }
    } catch (err) {
        removeLoading();
        if (sendBtn) sendBtn.disabled = false;
        const stopBtn2 = document.getElementById('stopBtn');
        if (stopBtn2) stopBtn2.hidden = true;
        if (err.name === 'AbortError') {
            // User stop vs timeout
            if (window._userStopped) {
                window._userStopped = false;
                addMessage('ai', '⏹ Stopped. Edit your message above and press Send to continue.');
                showToast('Generation stopped', 'info');
                return;
            }

            addMessage('ai', '❌ The request timed out. The AI model may be taking too long or the server may be unresponsive.');
            showToast('Request timed out. Try again or use a shorter clip.', 'error');
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
    } catch (err) {
        console.error('Auth check failed:', err);
        window.location.href = '/login.html';
    }
}

window.performLogout = function() {
    if (!confirm("Log out?")) return;
    try {
        fetch('/auth/logout', { 
            method: 'POST', 
            headers: { 'Authorization': `Bearer ${getAccessToken()}` } 
        });
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
    try {
        const current = document.documentElement.getAttribute('data-theme') || localStorage.getItem('vision_ai_theme') || 'dark';
        const nextTheme = (current === 'light') ? 'dark' : 'light';
        applyTheme(nextTheme);
        localStorage.setItem('vision_ai_theme', nextTheme);
        if (typeof updateThemeIcon === 'function') updateThemeIcon(nextTheme);
        ['floatingThemeToggle','headerThemeBtn'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.textContent = nextTheme === 'light' ? '☀️' : '🌙';
        });
    } catch (e) {
        console.error(e);
        const cur = document.documentElement.getAttribute('data-theme');
        document.documentElement.setAttribute('data-theme', cur === 'light' ? 'dark' : 'light');
    }
}

// ============================================================
// PROMPT STUDIO — Modern redesign
// Categories, tags, search, favorites, recent, templates, one-click copy
// ============================================================
let favorites = JSON.parse(localStorage.getItem('vision_ai_favorites') || '[]');
let recent = JSON.parse(localStorage.getItem('vision_ai_recent') || '[]');
let currentCategory = 'All';
let isFavoritesMode = false;
let isRecentMode = false;
let activeTag = null;

const PROMPT_LIBRARY = {
    "Study & Exams": {
        icon: "🎓", color: "#06b6d4", tags: ["exam","physics","igcse"],
        prompts: [
            { title: "IGCSE Physics paper solver", t: "You are a Cambridge IGCSE/A-Level physics examiner-tutor. Solve the uploaded paper question-by-question.\nFor each Q: (1) what is asked (2) formula/concept (3) numbers + units (4) final answer / option letter.\nIf a diagram is required but not in the text, say so. Never invent options.", tags: ["exam","physics"] },
            { title: "Master-level concept deep dive", t: "Explain [concept] at Master's physics level: rigorous math, assumptions, limits of the model, and one real experiment or application.", tags: ["explain"] },
            { title: "Quiz from document/video", t: "From the uploaded document or video transcript only, create a 10-question quiz with answers and short explanations. Match the source language (Urdu/English).", tags: ["exam"] },
            { title: "Revision sheet", t: "One-page revision sheet for [topic]: core formulas, 5 common exam mistakes, 3 practice questions with answers.", tags: ["exam"] },
            { title: "Guided problem solve", t: "Solve step-by-step and PAUSE after each step so I can attempt the next: [problem]", tags: ["explain"] },
            { title: "Theory comparison", t: "Compare [Theory A] vs [Theory B]: assumptions, equations, evidence, and when to use each.", tags: ["explain"] }
        ]
    },
    "YouTube & Media": {
        icon: "🎥", color: "#ef4444", tags: ["youtube","quiz","download"],
        prompts: [
            { title: "Urdu video summary", t: "اس یوٹیوب ویڈیو کا خلاصہ واضح پاکستانی اردو میں لکھیں: اہم نکات، ترتیبِ وقت، اور سبق۔\nلنک: [paste link]", tags: ["youtube","summary"] },
            { title: "Urdu quiz from video", t: "اس یوٹیوب ویڈیو پر 10 سوالوں کا کوئز بنائیں — ہر سوال کے ساتھ درست جواب اور 1–2 سطری وضاحت۔\nلنک: [paste link]", tags: ["youtube","quiz"] },
            { title: "English summary + timeline", t: "Summarize this YouTube video with timestamps and key takeaways.\nURL: [paste link]", tags: ["youtube"] },
            { title: "List download formats", t: "List all available download formats (video + audio) with quality for: [paste YouTube URL]", tags: ["download"] },
            { title: "Download MP3", t: "Download audio MP3 from: [paste YouTube URL]", tags: ["download"] },
            { title: "Download video (works in browser)", t: "Download video 720p from: [paste YouTube URL]", tags: ["download"] },
            { title: "Teach from transcript", t: "Extract transcript then teach me as a short lesson with examples and a 5-question mini-test.\nURL: [paste link]", tags: ["youtube"] }
        ]
    },
    "Coding": {
        icon: "💻", color: "#8b5cf6", tags: ["code","debug","api"],
        prompts: [
            { title: "Production code review", t: "Act as a senior engineer. Review for bugs, security, and performance. Give a minimal production-ready fix.\n\n```\n[paste code]\n```", tags: ["code","debug"] },
            { title: "Implement feature", t: "Write production-ready [language] for: [feature]. Include errors, tests/docstrings, and a short usage example.", tags: ["code"] },
            { title: "Refactor SOLID", t: "Refactor for SOLID and clarity without changing behavior. List changes.\n\n```\n[paste code]\n```", tags: ["code"] },
            { title: "REST API design", t: "Design REST API for [domain]: endpoints, JSON shapes, auth, validation, error codes.", tags: ["api"] },
            { title: "Debug error", t: "Root-cause this error and give the exact fix.\nError:\n[paste]\nCode:\n[paste]", tags: ["debug"] }
        ]
    },
    "Data & BI": {
        icon: "📊", color: "#10b981", tags: ["sql","bi","analytics"],
        prompts: [
            { title: "Teach document + exam", t: "Teach the uploaded document as a lesson (objectives → concepts → examples). Then give a 10-question exam with answers.", tags: ["analytics"] },
            { title: "SQL expert", t: "Write optimized SQL for: [question]. Note indexes and edge cases.\nSchema:\n[paste]", tags: ["sql"] },
            { title: "Dashboard KPIs", t: "Design Power BI / dashboard KPIs for [business]: metrics, visuals, filters.", tags: ["bi"] },
            { title: "Dataset insights", t: "Propose cleaning steps, charts, and 5 insights for:\n[describe or paste data]", tags: ["analytics"] }
        ]
    },
    "Writing": {
        icon: "✍️", color: "#f59e0b", tags: ["email","urdu","rewrite"],
        prompts: [
            { title: "Polish English", t: "Rewrite in clear professional English; keep meaning:\n\n[paste text]", tags: ["rewrite"] },
            { title: "Pakistani Urdu polish", t: "اس متن کو درست، روان پاکستانی اردو میں لکھیں:\n\n[متن]", tags: ["urdu"] },
            { title: "Professional email", t: "Draft email about [topic] for [audience]: subject + body + CTA.", tags: ["email"] },
            { title: "Executive summary", t: "5 bullets + 2-sentence executive summary:\n\n[paste]", tags: ["rewrite"] }
        ]
    },
    "Career": {
        icon: "🚀", color: "#3b82f6", tags: ["cv","interview","plan"],
        prompts: [
            { title: "Physics → career plan", t: "I have a Master's in Physics. 6-month plan toward [data science / quant / software]: weekly milestones and free resources.", tags: ["plan"] },
            { title: "CV bullet upgrade", t: "Rewrite this CV bullet with metric + action + result:\n[paste]", tags: ["cv"] },
            { title: "Interview pack", t: "8 interview Q&As for [role], tailored to a physics graduate.", tags: ["interview"] }
        ]
    },
    "Image & PDF": {
        icon: "🖼️", color: "#ec4899", tags: ["image","pdf"],
        prompts: [
            { title: "Deep image analysis", t: "Describe every visible detail in the uploaded image (text, UI, diagrams, labels). Then answer: [question]", tags: ["image"] },
            { title: "Exam PDF solver", t: "Solve the uploaded exam PDF question-by-question with formulas and final answers. State when a diagram is missing.", tags: ["pdf"] },
            { title: "Notes from PDF", t: "Extract text from this document and turn it into structured revision notes.", tags: ["pdf"] },
            { title: "Electrician / trade book", t: "Summarize this trade/training book chapter by chapter. List practical skills and safety rules. Language: [English or Urdu].", tags: ["pdf"] }
        ]
    }
};



function normalizePrompt(p) {
    if (typeof p === 'string') return { t: p, tags: [] };
    return p;
}

function getAllPrompts() {
    const all = [];
    Object.entries(PROMPT_LIBRARY).forEach(([cat, data]) => {
        (data.prompts || []).forEach(p => {
            const n = normalizePrompt(p);
            all.push({ ...n, category: cat, icon: data.icon });
        });
    });
    return all;
}

function getAllTags() {
    const tags = new Set();
    getAllPrompts().forEach(p => (p.tags || []).forEach(t => tags.add(t)));
    return Array.from(tags).sort();
}

function toggleHelpModal() {
    const modal = document.getElementById('helpModal');
    if (!modal) {
        createHelpModal();
        document.getElementById('helpModal').style.display = 'flex';
        renderCategories();
        renderTagChips();
        renderPrompts();
        updateStats();
        setTimeout(() => {
            const s = document.getElementById('promptSearch');
            if (s) s.focus();
        }, 50);
    } else if (modal.style.display === 'flex') {
        modal.style.display = 'none';
    } else {
        modal.style.display = 'flex';
        renderCategories();
        renderTagChips();
        renderPrompts();
        updateStats();
    }
}

function createHelpModal() {
    const modal = document.createElement('div');
    modal.id = 'helpModal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-label', 'Prompt Studio');
    modal.style.cssText = 'display:none; position:fixed; inset:0; z-index:99999; background:rgba(0,0,0,0.72); backdrop-filter:blur(10px); align-items:center; justify-content:center; padding:16px;';
    modal.innerHTML = `
        <div class="ps-panel" style="background:var(--bg-secondary); width:100%; max-width:1080px; max-height:92vh; border-radius:20px; overflow:hidden; display:flex; flex-direction:column; box-shadow:var(--shadow-lg); border:1px solid var(--border-color);">
            <div style="padding:20px 24px 12px; border-bottom:1px solid var(--border-color); flex-shrink:0;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:14px;">
                    <div>
                        <h2 style="font-size:20px; font-weight:800; color:var(--text-main); display:flex; align-items:center; gap:10px; letter-spacing:-0.3px;">
                            <span style="background:linear-gradient(135deg,#00C6FF,#7B68EE); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Prompt Studio</span>
                        </h2>
                        <p style="color:var(--text-muted); font-size:13px; margin-top:4px;">Click a card to load it into chat • edit placeholders • Send</p>
                    </div>
                    <div style="display:flex; gap:8px; align-items:center;">
                        <span id="promptCount" style="color:var(--text-muted); font-size:12px; background:var(--bg-tertiary); padding:4px 10px; border-radius:20px;">0</span>
                        <button onclick="toggleHelpModal()" aria-label="Close" style="background:var(--bg-tertiary); border:1px solid var(--border-color); color:var(--text-muted); width:36px; height:36px; border-radius:10px; cursor:pointer; font-size:18px; line-height:1;">✕</button>
                    </div>
                </div>
                <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                    <div style="flex:1; min-width:200px; position:relative;">
                        <input type="text" id="promptSearch" placeholder="Search prompts…" autocomplete="off"
                               style="width:100%; padding:11px 14px 11px 38px; border-radius:12px; border:1px solid var(--border-color); background:var(--input-bg); color:var(--text-main); font-size:14px; outline:none;"
                               oninput="handleSearchInput(this.value)">
                        <span style="position:absolute; left:12px; top:50%; transform:translateY(-50%); opacity:0.5; pointer-events:none;">🔍</span>
                    </div>
                    <button onclick="showRecentPrompts()" id="recentBtn" style="padding:10px 14px; border-radius:10px; border:1px solid var(--border-color); background:var(--bg-tertiary); color:var(--text-main); cursor:pointer; font-size:13px; white-space:nowrap;">🕐 Recent</button>
                    <button onclick="toggleFavorites()" id="favBtn" style="padding:10px 14px; border-radius:10px; border:1px solid var(--border-color); background:var(--bg-tertiary); color:var(--text-main); cursor:pointer; font-size:13px; white-space:nowrap;">⭐ Favorites</button>
                    <button onclick="clearSearch()" style="padding:10px 14px; border-radius:10px; border:1px solid var(--border-color); background:transparent; color:var(--text-muted); cursor:pointer; font-size:13px;">Clear</button>
                </div>
                <div id="tagChips" style="display:flex; gap:6px; flex-wrap:wrap; margin-top:12px;"></div>
            </div>
            <div id="categoryTabs" style="display:flex; gap:6px; flex-wrap:nowrap; overflow-x:auto; padding:12px 24px 0; flex-shrink:0; scrollbar-width:thin;"></div>
            <div id="promptGrid" style="overflow-y:auto; flex:1; padding:14px 24px 20px; display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:12px; min-height:200px;"></div>
            <div style="padding:12px 24px; border-top:1px solid var(--border-color); display:flex; justify-content:space-between; color:var(--text-muted); font-size:12px; flex-wrap:wrap; gap:8px; flex-shrink:0;">
                <span>⭐ <span id="favoriteCount">0</span> favorites · 🕐 <span id="recentCount">0</span> recent</span>
                <span><kbd style="background:var(--bg-tertiary); padding:2px 6px; border-radius:4px; border:1px solid var(--border-color);">Ctrl</kbd>+<kbd style="background:var(--bg-tertiary); padding:2px 6px; border-radius:4px; border:1px solid var(--border-color);">K</kbd> open · <kbd style="background:var(--bg-tertiary); padding:2px 6px; border-radius:4px; border:1px solid var(--border-color);">Esc</kbd> close</span>
            </div>
        </div>
    `;
    modal.addEventListener('click', (e) => { if (e.target === modal) toggleHelpModal(); });
    document.body.appendChild(modal);

    // Inject minimal styles once
    if (!document.getElementById('ps-styles')) {
        const style = document.createElement('style');
        style.id = 'ps-styles';
        style.textContent = `
            .category-tab { padding:8px 14px; border-radius:20px; border:1px solid var(--border-color); background:var(--bg-tertiary); color:var(--text-main); cursor:pointer; font-size:13px; white-space:nowrap; transition:all 0.15s ease; font-family:inherit; }
            .category-tab:hover { border-color:var(--primary-cyan); }
            .category-tab.active { background:linear-gradient(135deg,rgba(0,198,255,0.2),rgba(123,104,238,0.2)); border-color:var(--primary-cyan); color:var(--text-main); font-weight:600; }
            .ps-card { padding:14px; background:var(--bg-tertiary); border-radius:14px; border:1px solid var(--border-color); cursor:pointer; transition:all 0.18s ease; display:flex; flex-direction:column; gap:10px; min-height:110px; }
            .ps-card:hover { border-color:var(--primary-cyan); transform:translateY(-2px); box-shadow:var(--shadow-md); }
            .ps-card-text { font-size:13.5px; line-height:1.45; color:var(--text-main); flex:1; }
            .ps-card-meta { display:flex; justify-content:space-between; align-items:center; gap:8px; }
            .ps-tag { font-size:10px; padding:2px 8px; border-radius:10px; background:rgba(0,198,255,0.1); color:var(--primary-cyan); border:1px solid rgba(0,198,255,0.2); }
            .ps-actions button { background:none; border:none; cursor:pointer; font-size:16px; padding:2px 4px; border-radius:6px; line-height:1; }
            .ps-actions button:hover { background:var(--bg-secondary); }
            .ps-tag-chip { padding:4px 10px; border-radius:14px; border:1px solid var(--border-color); background:transparent; color:var(--text-muted); font-size:11px; cursor:pointer; font-family:inherit; }
            .ps-tag-chip.active { background:rgba(123,104,238,0.15); border-color:var(--primary-purple); color:var(--text-main); }
            #promptSearch:focus { border-color:var(--primary-cyan); box-shadow:0 0 0 3px rgba(0,198,255,0.12); }
            @media (max-width:600px) {
                #promptGrid { grid-template-columns:1fr !important; padding:12px !important; }
                .ps-panel { max-height:96vh !important; border-radius:16px !important; }
            }
        `;
        document.head.appendChild(style);
    }
}

function renderCategories() {
    const container = document.getElementById('categoryTabs');
    if (!container) return;
    let html = `<button class="category-tab ${currentCategory === 'All' && !isFavoritesMode && !isRecentMode ? 'active' : ''}" data-category="All" onclick="filterByCategory('All')">📌 All</button>`;
    Object.keys(PROMPT_LIBRARY).forEach(cat => {
        const icon = PROMPT_LIBRARY[cat].icon;
        const active = currentCategory === cat && !isFavoritesMode && !isRecentMode ? 'active' : '';
        html += `<button class="category-tab ${active}" data-category="${cat}" onclick="filterByCategory('${cat}')">${icon} ${cat}</button>`;
    });
    container.innerHTML = html;
}

function renderTagChips() {
    const el = document.getElementById('tagChips');
    if (!el) return;
    const tags = getAllTags().slice(0, 14);
    el.innerHTML = tags.map(t =>
        `<button class="ps-tag-chip ${activeTag === t ? 'active' : ''}" onclick="filterByTag('${t}')">#${t}</button>`
    ).join('');
}

function filterByTag(tag) {
    activeTag = activeTag === tag ? null : tag;
    isFavoritesMode = false;
    isRecentMode = false;
    renderTagChips();
    renderPrompts(currentCategory, document.getElementById('promptSearch')?.value || '');
}

function renderPrompts(category = currentCategory, searchTerm = '') {
    const grid = document.getElementById('promptGrid');
    const count = document.getElementById('promptCount');
    if (!grid) return;

    let prompts = [];
    if (isFavoritesMode) {
        prompts = favorites.map(t => ({ t, tags: [], category: 'Favorite', icon: '⭐' }));
    } else if (isRecentMode) {
        prompts = recent.map(t => ({ t, tags: [], category: 'Recent', icon: '🕐' }));
    } else if (category === 'All') {
        prompts = getAllPrompts();
    } else {
        const data = PROMPT_LIBRARY[category];
        prompts = (data?.prompts || []).map(p => {
            const n = normalizePrompt(p);
            return { ...n, category, icon: data.icon };
        });
    }

    if (searchTerm) {
        const q = searchTerm.toLowerCase();
        prompts = prompts.filter(p =>
            p.t.toLowerCase().includes(q) ||
            (p.tags || []).some(tg => tg.includes(q)) ||
            (p.category || '').toLowerCase().includes(q)
        );
    }
    if (activeTag) {
        prompts = prompts.filter(p => (p.tags || []).includes(activeTag));
    }

    if (prompts.length === 0) {
        grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:48px 20px; color:var(--text-muted);">
            <div style="font-size:32px; margin-bottom:8px;">🔍</div>
            <div>No prompts found. Try another search or category.</div>
        </div>`;
        if (count) count.textContent = '0 prompts';
        return;
    }

    grid.innerHTML = prompts.map(p => {
        const text = p.t;
        const escaped = text.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
        const isFav = favorites.includes(text);
        const tagsHtml = (p.tags || []).slice(0, 3).map(tg => `<span class="ps-tag">#${tg}</span>`).join('');
        const title = p.title ? `<div class="ps-card-title">${escapeHtml(p.title)}</div>` : '';
        return `
            <div class="ps-card" onclick="usePromptInChat('${escaped}')" title="Click to load into chat">
                ${title}
                <div class="ps-card-text">${escapeHtml((text.length > 140 ? text.slice(0, 140) + "…" : text))}</div>
                <div class="ps-card-meta">
                    <div style="display:flex; gap:4px; flex-wrap:wrap; align-items:center;">
                        <span style="font-size:11px; color:var(--text-muted);">${p.icon || ''} ${escapeHtml(p.category || '')}</span>
                        ${tagsHtml}
                    </div>
                    <div class="ps-actions" onclick="event.stopPropagation()">
                        <button type="button" title="${isFav ? 'Unfavorite' : 'Favorite'}" onclick="toggleFavorite('${escaped}')">${isFav ? '⭐' : '☆'}</button>
                        <button type="button" title="Use in chat" onclick="copyAndChat('${escaped}')">➤</button>
                    </div>
                </div>
            </div>`;
    }).join('');

    if (count) count.textContent = `${prompts.length} prompt${prompts.length === 1 ? '' : 's'}`;
}

function filterByCategory(category) {
    currentCategory = category;
    isFavoritesMode = false;
    isRecentMode = false;
    activeTag = null;
    const favBtn = document.getElementById('favBtn');
    const recentBtn = document.getElementById('recentBtn');
    if (favBtn) favBtn.textContent = '⭐ Favorites';
    if (recentBtn) recentBtn.style.opacity = '1';
    renderCategories();
    renderTagChips();
    renderPrompts(category, document.getElementById('promptSearch')?.value || '');
}

function handleSearchInput(value) {
    isFavoritesMode = false;
    isRecentMode = false;
    renderPrompts(currentCategory, value);
}

function clearSearch() {
    const s = document.getElementById('promptSearch');
    if (s) s.value = '';
    activeTag = null;
    isFavoritesMode = false;
    isRecentMode = false;
    renderTagChips();
    renderPrompts(currentCategory, '');
}

function showRecentPrompts() {
    isRecentMode = true;
    isFavoritesMode = false;
    activeTag = null;
    const favBtn = document.getElementById('favBtn');
    if (favBtn) favBtn.textContent = '⭐ Favorites';
    document.querySelectorAll('.category-tab').forEach(btn => btn.classList.remove('active'));
    renderPrompts();
}

function toggleFavorite(prompt) {
    const index = favorites.indexOf(prompt);
    if (index > -1) favorites.splice(index, 1);
    else favorites.push(prompt);
    localStorage.setItem('vision_ai_favorites', JSON.stringify(favorites));
    renderPrompts(currentCategory, document.getElementById('promptSearch')?.value || '');
    updateStats();
}

function toggleFavorites() {
    isFavoritesMode = !isFavoritesMode;
    isRecentMode = false;
    activeTag = null;
    const favBtn = document.getElementById('favBtn');
    if (favBtn) favBtn.textContent = isFavoritesMode ? '🔙 All' : '⭐ Favorites';
    if (isFavoritesMode) {
        document.querySelectorAll('.category-tab').forEach(btn => btn.classList.remove('active'));
        renderPrompts();
    } else {
        filterByCategory(currentCategory);
    }
}

function copyPrompt(text) {
    const doCopy = () => {
        recent = recent.filter(r => r !== text);
        recent.unshift(text);
        if (recent.length > 15) recent.pop();
        localStorage.setItem('vision_ai_recent', JSON.stringify(recent));
        updateStats();
        showToast('✅ Prompt copied', 'success');
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(doCopy).catch(() => {
            // fallback
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            doCopy();
        });
    } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        doCopy();
    }
}

function copyAndChat(text) {
    usePromptInChat(text);
}

function usePromptInChat(text) {
    recent = recent.filter(r => r !== text);
    recent.unshift(text);
    if (recent.length > 15) recent.pop();
    localStorage.setItem('vision_ai_recent', JSON.stringify(recent));
    updateStats();
    const input = document.getElementById('message');
    if (input) {
        input.value = text;
        input.focus();
        input.dispatchEvent(new Event('input', { bubbles: true }));
        // Place cursor at first [placeholder]
        const m = text.match(/\[[^\]]+\]/);
        if (m) {
            const i = text.indexOf(m[0]);
            try { input.setSelectionRange(i, i + m[0].length); } catch (_) {}
        }
    }
    const modal = document.getElementById('helpModal');
    if (modal) modal.style.display = 'none';
    showToast('Prompt loaded in chat — edit placeholders then Send', 'success', 3000);
}
window.usePromptInChat = usePromptInChat;

function updateStats() {
    const fc = document.getElementById('favoriteCount');
    const rc = document.getElementById('recentCount');
    if (fc) fc.textContent = favorites.length;
    if (rc) rc.textContent = recent.length;
}

// ============================================================
// EVENT LISTENERS
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    if (window._visionDOMReady) return;
    window._visionDOMReady = true;

    // Initialize theme first
    const savedTheme = localStorage.getItem('vision_ai_theme') || 'dark';
    applyTheme(savedTheme);
    updateThemeIcon(savedTheme);

    if (savedTheme === 'system') {
        window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
            applyTheme('system');
            updateThemeIcon('system');
        });
    }

    checkAuth();

    try {
        if (chatHistory.length === 0) startNewChat();
        else loadChat(chatHistory[0].id);
    } catch (e) {
        console.error('Failed to load initial chat:', e);
        startNewChat();
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

    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (window.innerWidth > 768) {
                const sidebar = document.getElementById('sidebar');
                if (sidebar && sidebar.classList.contains('open-mobile')) {
                    sidebar.classList.remove('open-mobile');
                    const overlay = document.getElementById('sidebar-overlay');
                    if (overlay) overlay.classList.remove('active');
                }
            }
        }, 250);
    });

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            toggleHelpModal();
        }
        if (e.key === 'Escape') {
            document.querySelectorAll('.chat-action-menu.show').forEach(el => el.classList.remove('show'));
            const dropdown = document.getElementById('profileDropdown');
            if (dropdown) dropdown.style.display = 'none';
            const modal = document.getElementById('helpModal');
            if (modal && modal.style.display === 'flex') {
                modal.style.display = 'none';
            }
        }
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            window.open('/admin/search', '_blank', 'noopener,noreferrer');
        }
    });

    // Admin floating buttons: only show for admin users (role or username)
(async function setupAdminButtons() {
    const adminBtn = document.getElementById('adminBtn');
    const adminPayBtn = document.getElementById('adminPayBtn');
    const token = getAccessToken();
    if (!token) return;
    let isAdmin = false;
    try {
        const user = JSON.parse(localStorage.getItem('vision_ai_user') || '{}');
        // ✅ FIX: Check for 'aftab' as well
        if (user.role === 'admin' || user.username === 'admin' || user.username === 'aftab') isAdmin = true;
    } catch (_) {}
    if (!isAdmin) {
        try {
            const res = await authedFetch('/auth/me');
            if (res && res.ok) {
                const data = await res.json();
                // ✅ FIX: Check for 'aftab' as well
                if (data.role === 'admin' || data.username === 'admin' || data.username === 'aftab') isAdmin = true;
                localStorage.setItem('vision_ai_user', JSON.stringify(data));
            }
        } catch (_) {}
    }
    if (isAdmin) {
        if (adminBtn) /* adminBtn moved to top bar */;
        if (adminPayBtn) adminPayBtn.style.display = 'flex';
    }
})();

    console.log('👁️ Vision AI v2.0 - Ready');
});

// ============================================================
// FILE PREVIEW
// ============================================================
function renderFilePreview() {
    try {
        const fi = document.getElementById('fileInput');
        if (fi && Array.from(fi.files || []).some(f => (f.type || '').startsWith('image/'))) {
            showToast('Image attached — ask what you see or “solve this diagram”', 'info', 2500);
        }
    } catch (_) {}

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

// ============================================================
// 🟢 ADDITIONAL SAFEGUARDS
// ============================================================
if (window._visionAIInitialized) {
    console.warn('Vision AI already initialized!');
} else {
    window._visionAIInitialized = true;
}

window.onerror = function(msg, url, line, col, error) {
    console.error('Global error:', msg, error);
    showToast('An unexpected error occurred. Please refresh the page.', 'error');
    return true;
};

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred.', 'error');
});

// Export functions for global access
window.applyTheme = applyTheme;
window.getAccessToken = getAccessToken;
window.getRefreshToken = getRefreshToken;
window.setTokens = setTokens;
window.clearTokens = clearTokens;
window.refreshAccessToken = refreshAccessToken;
window.authenticatedFetch = authenticatedFetch;
window.showToast = showToast;
window.toggleSidebar = toggleSidebar;
window.closeMobileSidebar = closeMobileSidebar;
window.forceOpenSearch = forceOpenSearch;
window.renameChat = renameChat;
window.deleteChat = deleteChat;
window.startNewChat = startNewChat;
window.loadChat = loadChat;
window.clearAllCaches = clearAllCaches;


function copyMessageText(btn) {
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;
    const body = bubble.querySelector('.markdown-content');
    const text = body ? body.innerText : bubble.innerText;
    const done = () => {
        const prev = btn.textContent;
        btn.textContent = '✅ Copied';
        setTimeout(() => { btn.textContent = prev; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(() => {
            const ta = document.createElement('textarea');
            ta.value = text; document.body.appendChild(ta); ta.select();
            document.execCommand('copy'); document.body.removeChild(ta); done();
        });
    }
}

function toggleExpandMessage(btn) {
    const bubble = btn.closest('.message-bubble');
    const body = bubble && bubble.querySelector('.markdown-content');
    if (!body) return;
    bubble.classList.toggle('msg-tall');
    body.classList.toggle('msg-expanded-height');
    btn.classList.toggle('active');
    btn.textContent = body.classList.contains('msg-expanded-height') ? '▴ Collapse' : '↕ Height';
}

function toggleWideMessage(btn) {
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;
    bubble.classList.toggle('msg-wide');
    bubble.classList.toggle('msg-tall');
    btn.classList.toggle('active');
    btn.textContent = bubble.classList.contains('msg-wide') ? '↔ Narrow' : '↔ Width';
}

function zoomMessage(btn, factor) {
    const bubble = btn.closest('.message-bubble');
    const body = bubble && bubble.querySelector('.markdown-content');
    if (!body) return;
    const cur = parseFloat(body.dataset.zoom || '1');
    const next = Math.min(1.8, Math.max(0.75, +(cur * factor).toFixed(2)));
    body.dataset.zoom = String(next);
    body.style.fontSize = (15 * next) + 'px';
    body.style.lineHeight = String(1.65 + (next - 1) * 0.2);
}

function focusMessageFullscreen(btn) {
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;
    let overlay = document.getElementById('msgFullscreenOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'msgFullscreenOverlay';
        overlay.innerHTML = `
            <div class="msg-fs-panel glass-panel">
                <div class="msg-fs-toolbar">
                    <span>Response view</span>
                    <div style="display:flex;gap:8px;">
                        <button type="button" class="msg-action-btn" id="msgFsCopy">📋 Copy</button>
                        <button type="button" class="msg-action-btn" id="msgFsClose">✕ Close</button>
                    </div>
                </div>
                <div class="msg-fs-body markdown-content" id="msgFsBody"></div>
            </div>`;
        document.body.appendChild(overlay);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) closeMsgFullscreen(); });
        document.getElementById('msgFsClose').onclick = closeMsgFullscreen;
        document.getElementById('msgFsCopy').onclick = () => {
            const t = document.getElementById('msgFsBody').innerText;
            navigator.clipboard.writeText(t).then(() => showToast('Copied', 'success'));
        };
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && overlay.classList.contains('open')) closeMsgFullscreen();
        });
    }
    const src = bubble.querySelector('.markdown-content');
    document.getElementById('msgFsBody').innerHTML = src ? src.innerHTML : bubble.innerHTML;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeMsgFullscreen() {
    const overlay = document.getElementById('msgFullscreenOverlay');
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
}

function toggleChatFocusMode() {
    document.body.classList.toggle('chat-focus-mode');
    const on = document.body.classList.contains('chat-focus-mode');
    // Browser fullscreen for true focus
    try {
        if (on && !document.fullscreenElement) {
            document.documentElement.requestFullscreen?.();
        } else if (!on && document.fullscreenElement) {
            document.exitFullscreen?.();
        }
    } catch (_) {}
    // Subtle status only — avoid toast spam
    const btn = document.querySelector('[onclick="toggleChatFocusMode()"]');
    if (btn) btn.classList.toggle('active', on);
    const title = document.getElementById('chatTitle');
    if (title && !title.dataset.orig) title.dataset.orig = title.textContent;
}


window.addMessage = addMessage;
window.copyMessageText = copyMessageText;
window.toggleExpandMessage = toggleExpandMessage;
window.toggleChatFocusMode = toggleChatFocusMode;
window.closeMsgFullscreen = closeMsgFullscreen;
window.focusMessageFullscreen = focusMessageFullscreen;
window.zoomMessage = zoomMessage;
window.toggleWideMessage = toggleWideMessage;
window.editMessage = editMessage;
window.cancelEdit = cancelEdit;
window.sendEdit = sendEdit;


// ---- Mobile-friendly forced download (blob) ----
async function forceMobileDownload(url, suggestedName) {
    const token = localStorage.getItem('vision_ai_token') || localStorage.getItem('token') || '';
    const headers = {};
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const res = await fetch(url, { headers, credentials: 'same-origin' });
    if (!res.ok) throw new Error('Download failed: ' + res.status);
    const blob = await res.blob();
    let name = suggestedName;
    if (!name) {
        try {
            const cd = res.headers.get('Content-Disposition') || '';
            const m = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(cd);
            if (m) name = decodeURIComponent(m[1].replace(/"/g, ''));
        } catch (e) {}
    }
    if (!name) name = (url.split('/').pop() || 'download.bin').split('?')[0];
    const obj = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = obj;
    a.download = name;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(obj); a.remove(); }, 2000);
    if (typeof showToast === 'function') showToast('Download started: ' + name, 'success', 3000);
}

// ============================================================
// VOICE INPUT (Web Speech API) + VOICE OUTPUT (speechSynthesis)
// ============================================================
let _recognition = null;
let _listening = false;
let _currentUtterance = null;

function fillPrompt(text) {
    const ta = document.getElementById('message');
    if (!ta) return;
    ta.value = text;
    ta.focus();
    ta.dispatchEvent(new Event('input'));
}

let _micDenied = false;
let _micToastAt = 0;

function _micToast(msg, type, ms) {
    const now = Date.now();
    if (now - _micToastAt < 8000) return;
    _micToastAt = now;
    showToast(msg, type || "error", ms || 8000);
}

function _getSpeechRecognition() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}


function toggleVoiceInput() {
    if (_listening) {
        stopVoiceInput();
        return;
    }
    startVoiceInput();
}

async function startVoiceInput() {
    const ta = document.getElementById('message');
    const status = document.getElementById('voiceStatus');
    const mic = document.getElementById('micBtn');

    if (_micDenied) {
        _micToast('Microphone still blocked. Click the lock icon in the address bar → Site settings → Microphone → Allow, then reload this page.', 'error', 10000);
        return;
    }

    // Secure context required (localhost or https)
    if (typeof window.isSecureContext === 'boolean' && !window.isSecureContext) {
        _micToast('Mic only works on HTTPS or localhost (your Railway URL is HTTPS — reload and Allow mic).', 'error', 9000);
        return;
    }

    const Rec = _getSpeechRecognition();
    if (!Rec) {
        showToast('Voice input needs Chrome, Edge, or Safari.', 'error', 5000);
        return;
    }

    // Permissions API (Chrome) — avoid repeated getUserMedia failures
    try {
        if (navigator.permissions && navigator.permissions.query) {
            const st = await navigator.permissions.query({ name: 'microphone' });
            if (st.state === 'denied') {
                _micDenied = true;
                _micToast('Microphone blocked in browser settings. Address bar lock → Microphone → Allow → Reload.', 'error', 10000);
                return;
            }
        }
    } catch (_) {}

    try {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(t => t.stop());
        }
    } catch (permErr) {
        console.warn(permErr);
        _micDenied = true;
        _micToast('Microphone blocked. Address bar lock → Site settings → Microphone → Allow → Reload.', 'error', 10000);
        return;
    }

    try {
        const rec = new Rec();
        // continuous=false is more reliable on mobile Chrome after permission grant
        rec.continuous = false;
        rec.interimResults = true;
        rec.maxAlternatives = 1;
        const sttLang = localStorage.getItem('vision_ai_stt_lang')
            || localStorage.getItem('vision_ai_voice_lang')
            || 'ur-PK';
        rec.lang = sttLang;

        let finalText = ta ? ta.value : '';

        rec.onstart = () => {
            _listening = true;
            if (status) { status.hidden = false; status.textContent = 'Listening… tap mic again to stop'; }
            if (mic) mic.classList.add('mic-active');
            showToast('Listening…', 'info', 1500);
        };
        rec.onresult = (event) => {
            let interim = '';
            let piece = finalText;
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const r = event.results[i];
                if (r.isFinal) piece = (piece ? piece + ' ' : '') + r[0].transcript;
                else interim += r[0].transcript;
            }
            finalText = piece;
            if (ta) {
                ta.value = (piece + (interim ? ' ' + interim : '')).trim();
                ta.dispatchEvent(new Event('input', { bubbles: true }));
            }
        };
        rec.onerror = (e) => {
            console.warn('speech error', e);
            if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
                _micDenied = true;
                _listening = false;
                _micToast('Mic permission denied. Address bar lock → Microphone → Allow → Reload page.', 'error', 10000);
                stopVoiceInput();
            } else if (e.error === 'no-speech') {
                showToast('No speech heard — try again closer to the mic', 'info', 2500);
            } else if (e.error !== 'aborted') {
                showToast('Voice error: ' + e.error, 'error');
                stopVoiceInput();
            }
        };
        rec.onend = () => {
            // Do not auto-restart if denied or user stopped — prevents toast spam
            if (_micDenied || !_listening) {
                stopVoiceInput();
                return;
            }
            stopVoiceInput();
        };
        _recognition = rec;
        rec.start();
    } catch (err) {
        showToast('Could not start microphone: ' + (err && err.message ? err.message : err), 'error');
        stopVoiceInput();
    }
}


function stopVoiceInput() {
    _listening = false;
    try { if (_recognition) _recognition.stop(); } catch (_) {}
    _recognition = null;
    const status = document.getElementById('voiceStatus');
    const mic = document.getElementById('micBtn');
    if (status) status.hidden = true;
    if (mic) mic.classList.remove('mic-active');
}

function _detectSpeechLang(text) {
    const t = text || '';
    // Prefer user preference when set
    const pref = localStorage.getItem('vision_ai_tts_lang')
        || localStorage.getItem('vision_ai_voice_lang');
    if (pref) return pref;
    // Script detection for common languages
    if (/[؀-ۿ]/.test(t)) return 'ur-PK';          // Arabic script → Urdu default (also works for ar)
    if (/[ऀ-ॿ]/.test(t)) return 'hi-IN';          // Devanagari → Hindi
    if (/[\u0E00-\u0E7F]/.test(t)) return 'th-TH'; // Thai
    if (/[\u0600-\u06FF]/.test(t) && /[\u064B-\u065F]/.test(t)) return 'ar-SA';
    if (/[\u4E00-\u9FFF]/.test(t)) return 'zh-CN'; // Chinese
    if (/[\u3040-\u30FF]/.test(t)) return 'ja-JP'; // Japanese
    if (/[\uAC00-\uD7AF]/.test(t)) return 'ko-KR'; // Korean
    if (/[\u0400-\u04FF]/.test(t)) return 'ru-RU'; // Cyrillic
    if (/[àâçéèêëîïôùûü]/i.test(t) && /\b(le|la|les|des|une|est)\b/i.test(t)) return 'fr-FR';
    if (/[äöüß]/i.test(t)) return 'de-DE';
    if (/[ñáéíóú¿¡]/i.test(t)) return 'es-ES';
    return 'en-US';
}

function speakMessage(btn) {
    if (!window.speechSynthesis) {
        showToast('Speech not supported in this browser. Use Chrome or Edge.', 'error');
        return;
    }
    // Toggle off if already speaking
    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        document.querySelectorAll('.speak-btn.speaking').forEach(b => b.classList.remove('speaking'));
        if (btn && btn.classList.contains('speaking')) {
            btn.classList.remove('speaking');
            return;
        }
    }

    // Find message bubble: actual DOM uses .message-bubble
    let bubble = null;
    if (btn) {
        bubble = btn.closest('.message-bubble')
            || btn.closest('.message-row')
            || btn.closest('.message, .ai-msg, .msg-ai, .bubble');
    }
    let text = '';
    if (bubble) {
        // Prefer markdown body only (skip buttons / badges)
        const body = bubble.querySelector('.markdown-content')
            || bubble.querySelector('.msg-fs-body')
            || bubble;
        const clone = body.cloneNode(true);
        clone.querySelectorAll('button, .msg-actions, .msg-action-btn, .speak-btn, .model-used, script, style').forEach(n => n.remove());
        text = (clone.innerText || clone.textContent || '').trim();
        // Strip common UI chrome
        text = text.replace(/^\s*(Copy|Speak|Height|Width|Full|Narrow|Collapse)\s*/gim, '').trim();
    }
    if (!text) {
        // Last resort: any text in the row
        const row = btn && btn.closest('.message-row');
        if (row) text = (row.innerText || '').replace(/Copy|Speak|Height|Width|Full/g, '').trim();
    }
    if (!text) {
        showToast('Nothing to read — no message text found', 'info');
        return;
    }

    // Chrome: voices often empty until loaded
    const voices = window.speechSynthesis.getVoices() || [];
    const lang = _detectSpeechLang(text);
    const u = new SpeechSynthesisUtterance(text.slice(0, 12000));
    u.lang = lang;
    u.rate = 0.95;
    u.pitch = 1;
    const langBase = (lang || 'en').split('-')[0].toLowerCase();
    let match = voices.find(v => (v.lang || '') === lang)
        || voices.find(v => (v.lang || '').toLowerCase().startsWith(langBase + '-'))
        || voices.find(v => (v.lang || '').toLowerCase().startsWith(langBase))
        || voices.find(v => /urdu|pakistan/i.test(v.name || ''))
        || voices.find(v => /arabic/i.test(v.name || '') && langBase === 'ur')
        || voices.find(v => /hindi/i.test(v.name || '') && (langBase === 'ur' || langBase === 'hi'));
    if (!match && voices.length) match = voices[0];
    if (match) {
        u.voice = match;
        if (!u.lang) u.lang = match.lang || lang;
    }
    if (langBase === 'ur') {
        const hasUr = voices.some(v =>
            /^ur/i.test(v.lang || '') || /urdu|pakistan/i.test(v.name || '')
        );
        if (!hasUr) {
            showToast(
                'Urdu system voice not found. Install Urdu language pack in phone/PC settings for better speech.',
                'info',
                7000
            );
        }
        u.rate = 0.9;
    }
    if (!voices.length) {
        window.speechSynthesis.onvoiceschanged = function () {
            window.speechSynthesis.cancel();
            speakMessage(btn);
        };
        window.speechSynthesis.getVoices();
    }

    u.onstart = () => { if (btn) btn.classList.add('speaking'); };
    u.onend = () => { if (btn) btn.classList.remove('speaking'); };
    u.onerror = (e) => {
        console.warn('speak error', e);
        if (btn) btn.classList.remove('speaking');
        showToast('Speak failed: ' + (e.error || 'unknown'), 'error');
    };

    // Cancel any queue then speak (Chrome quirk)
    window.speechSynthesis.cancel();
    setTimeout(() => window.speechSynthesis.speak(u), 50);
}


function stopSpeaking() {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    document.querySelectorAll('.speak-btn.speaking').forEach(b => b.classList.remove('speaking'));
}

window.fillPrompt = fillPrompt;
window.toggleVoiceInput = toggleVoiceInput;
window.startVoiceInput = startVoiceInput;
window.stopVoiceInput = stopVoiceInput;
window.speakMessage = speakMessage;
window.stopSpeaking = stopSpeaking;

window.sendMessage = sendMessage;
window.renderUserProfile = renderUserProfile;
window.toggleProfileDropdown = toggleProfileDropdown;
window.checkAuth = checkAuth;
window.performLogout = performLogout;
window.updateStatus = updateStatus;
window.updateThemeIcon = updateThemeIcon;
window.toggleTheme = toggleTheme;
window.renderFilePreview = renderFilePreview;
window.removeSelectedFile = removeSelectedFile;
window.toggleHelpModal = toggleHelpModal;
window.toggleFavorite = toggleFavorite;
window.toggleFavorites = toggleFavorites;
window.copyPrompt = copyPrompt;
window.copyAndChat = copyAndChat;
window.filterByCategory = filterByCategory;
window.handleSearchInput = handleSearchInput;
window.clearSearch = clearSearch;
window.showRecentPrompts = showRecentPrompts;
window.filterByTag = filterByTag;
window.renderTagChips = renderTagChips;

console.log('👁️ Vision AI v2.0 - Ready');
// Prefetch voices for Urdu/Arabic TTS
if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = function() { window.speechSynthesis.getVoices(); };
    try { window.speechSynthesis.getVoices(); } catch (_) {}
}

(function preloadSpeechVoices() {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = function () {
        window.speechSynthesis.getVoices();
    };
})();

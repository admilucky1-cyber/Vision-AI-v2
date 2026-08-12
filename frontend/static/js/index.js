
/* Avatar gender preference */
function getUserAvatarGender() {
  try { return localStorage.getItem('vision_avatar_gender') || 'neutral'; } catch (e) { return 'neutral'; }
}
function setUserAvatarGender(g) {
  try { localStorage.setItem('vision_avatar_gender', g); } catch (e) {}
  document.querySelectorAll('.avatar-gender-bar button').forEach(function(b) {
    b.classList.toggle('active', b.getAttribute('data-gender') === g);
  });
  document.querySelectorAll('.msg-avatar.user').forEach(function(el) {
    el.classList.remove('male', 'female', 'neutral');
    el.classList.add(g);
  });
}
function avatarEmoji(role) {
  /* Visuals come from CSS ::after — keep DOM empty for cleaner 3D orb */
  return '';
}
window.getUserAvatarGender = getUserAvatarGender;
window.setUserAvatarGender = setUserAvatarGender;


function visionImageToolbar(img) {
  const src = (img && (img.url || img.image_url || (img.image_data ? ("data:image/png;base64," + img.image_data) : ""))) || "";
  let h = "";
  if (src) {
    h += '<a class="img-act" href="' + src + '" download="vision-image.png" target="_blank" rel="noopener">Download</a>';
    h += '<a class="img-act" href="' + src + '" target="_blank" rel="noopener">Full</a>';
  }
  if (img && img.svg_data) {
    h += '<a class="img-act" href="data:image/svg+xml;base64,' + img.svg_data + '" download="vision-graph.svg">SVG</a>';
  }
  return h ? ('<div class="ai-image-actions">' + h + '</div>') : "";
}


function visionSvgDownloadBtn(img) {
  if (!img || !img.svg_data) return '';
  try {
    const href = 'data:image/svg+xml;base64,' + img.svg_data;
    return '<a class="img-act" href="' + href + '" download="vision-graph.svg" title="Download SVG">📄 SVG</a>';
  } catch (e) { return ''; }
}


/* v2.7.6: overlay cleanup on load only — resize must not kill hamburger */
(function visionUiBoot(){
  function clearDimOnce() {
    try {
      var ov = document.getElementById('sidebar-overlay');
      if (ov) {
        ov.classList.remove('active');
        if (window.innerWidth > 768) ov.style.display = 'none';
      }
      document.body.classList.remove('sidebar-open');
      var sb = document.getElementById('sidebar');
      if (sb && window.innerWidth > 768) {
        sb.classList.remove('open-mobile');
        sb.classList.remove('rail-mode');
      }
    } catch (e) {}
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', clearDimOnce);
  else clearDimOnce();
  var _rz;
  window.addEventListener('resize', function() {
    clearTimeout(_rz);
    _rz = setTimeout(function() {
      if (window.innerWidth > 768) {
        var ov = document.getElementById('sidebar-overlay');
        if (ov) { ov.classList.remove('active'); ov.style.display = 'none'; }
        document.body.classList.remove('sidebar-open');
        var sb = document.getElementById('sidebar');
        if (sb) sb.classList.remove('open-mobile');
      }
    }, 150);
  });
})();


// ============================================================
// VISION AI v3.2.0 - INDEX LOGIC (Production Ready)
// ============================================================

// ============================================================
// 🌙 THEME SYNC
// ============================================================
function applyTheme(theme) {
    const root = document.documentElement;
    let resolved = theme || 'dark';
    if (resolved === 'system') {
        resolved = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    }
    if (resolved !== 'light' && resolved !== 'dark') resolved = 'dark';
    root.setAttribute('data-theme', resolved);
    if (document.body) document.body.setAttribute('data-theme', resolved);
    if (typeof updateThemeIcon === 'function') updateThemeIcon(resolved);
}

// ============================================================
// AUTHENTICATION & TOKEN MANAGEMENT
// ============================================================

function getClientId() {
    try {
        var id = localStorage.getItem("vision_ai_client_id");
        if (id && id.length >= 8) return id;
        id = (typeof crypto !== "undefined" && crypto.randomUUID)
            ? crypto.randomUUID()
            : ("c" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10));
        localStorage.setItem("vision_ai_client_id", id);
        return id;
    } catch (e) {
        return "anon";
    }
}

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

function getUserKeyHeaders() {
    try {
        const raw = localStorage.getItem('vision_ai_user_keys');
        if (!raw) return {};
        const k = JSON.parse(raw);
        if (!k || !k.override) return {};
        const h = { 'X-Vision-Key-Override': '1' };
        if (k.GOOGLE_API_KEY) h['X-Vision-Key-Google'] = k.GOOGLE_API_KEY;
        if (k.GROQ_API_KEY) h['X-Vision-Key-Groq'] = k.GROQ_API_KEY;
        if (k.DEEPSEEK_API_KEY) h['X-Vision-Key-Deepseek'] = k.DEEPSEEK_API_KEY;
        if (k.OPENROUTER_API_KEY) h['X-Vision-Key-Openrouter'] = k.OPENROUTER_API_KEY;
        if (k.OPENAI_COMPAT_BASE) h['X-Vision-Key-Compat-Base'] = k.OPENAI_COMPAT_BASE;
        if (k.OPENAI_COMPAT_KEY) h['X-Vision-Key-Compat-Key'] = k.OPENAI_COMPAT_KEY;
        if (k.OPENAI_COMPAT_MODEL) h['X-Vision-Key-Compat-Model'] = k.OPENAI_COMPAT_MODEL;
        return h;
    } catch (e) { return {}; }
}

async function authenticatedFetch(url, options = {}) {
    let token = getAccessToken();
    const headers = { 
        ...options.headers, 
        ...getUserKeyHeaders(),
        'X-Vision-Client-Id': getClientId(),
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
    try {
      var sb = document.getElementById('sidebar');
      setTimeout(function() {
        var open = sb && (sb.classList.contains('open-mobile') || (window.innerWidth > 768 && !sb.classList.contains('rail-mode')));
        document.documentElement.setAttribute('data-sidebar', open ? 'open' : 'closed');
      }, 0);
    } catch (e) {}

    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
        const willOpen = !sidebar.classList.contains('open-mobile');
        sidebar.classList.toggle('open-mobile', willOpen);
        document.body.classList.toggle('sidebar-open', willOpen);
        let overlay = document.getElementById('sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'sidebar-overlay';
            overlay.setAttribute('aria-hidden', 'true');
            document.body.appendChild(overlay);
        }
        // Always (re)bind close handler so overlay never becomes a dead trap
        overlay.onclick = function(ev) {
          ev.preventDefault();
          if (typeof closeMobileSidebar === 'function') closeMobileSidebar();
        };
        overlay.classList.toggle('active', willOpen);
        overlay.style.display = willOpen ? 'block' : 'none';
        overlay.style.pointerEvents = willOpen ? 'auto' : 'none';
        // Keep header / hamburger above overlay — CSS also enforces this
        var hdr = document.querySelector('.main-header');
        if (hdr) hdr.style.zIndex = '60';
    } else {
        sidebar.classList.toggle('rail-mode');
        sidebar.classList.toggle('collapsed-true', sidebar.classList.contains('rail-mode'));
        const toolbar = document.getElementById('collapsedToolbar');
        if (toolbar) {
            if (sidebar.classList.contains('rail-mode')) toolbar.classList.add('active');
            else toolbar.classList.remove('active');
        }
    }
};

window.closeMobileSidebar = function() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    sidebar.classList.remove('open-mobile');
    document.body.classList.remove('sidebar-open');
    const overlay = document.getElementById('sidebar-overlay');
    if (overlay) {
        overlay.classList.remove('active');
        overlay.style.display = 'none';
        overlay.style.pointerEvents = 'none';
    }
    try { document.documentElement.setAttribute('data-sidebar', 'closed'); } catch (e) {}
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
function _safeLoadHistory() {
    try {
        const raw = localStorage.getItem('vision_ai_history_v2') || '[]';
        const data = JSON.parse(raw);
        return Array.isArray(data) ? data : [];
    } catch (e) {
        console.warn('history parse failed', e);
        try { localStorage.removeItem('vision_ai_history_v2'); } catch (_) {}
        return [];
    }
}
let chatHistory = _safeLoadHistory();

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
    if (chatHistory.length > 40) chatHistory = chatHistory.slice(0, 40);
    saveHistory();
    renderHistory();
    const output = ensureChatOutput();
    if (output) output.innerHTML = '';
    const titleEl = document.getElementById('chatTitle');
    if (titleEl) titleEl.textContent = 'New Chat';
    const input = document.getElementById('message');
    if (input) { input.value = ''; input.style.height = 'auto'; try { input.focus(); } catch (_) {} }
    if (window.innerWidth <= 768 && typeof closeMobileSidebar === 'function') closeMobileSidebar();
}

function _slimMessages(messages) {
    return (messages || []).slice(-40).map(m => {
        const out = {
            role: m.role,
            text: (m.text || '').length > 12000 ? (m.text.slice(0, 12000) + '…') : (m.text || ''),
            modelUsed: m.modelUsed || null,
            filesCount: m.filesCount || 0,
            fileNames: m.fileNames || undefined,
        };
        // Never persist huge base64 images in localStorage (quota ~5MB)
        if (m.images && Array.isArray(m.images) && m.images.length) {
            out.imageCount = m.images.length;
            out.images = m.images.map(img => ({
                provider: img && img.provider,
                diagram_type: img && img.diagram_type,
                omitted: true,
            }));
        }
        return out;
    });
}

function _slimHistory(history) {
    return (history || []).slice(0, 50).map(c => ({
        id: c.id,
        title: (c.title || 'New Chat').slice(0, 80),
        timestamp: c.timestamp || Date.now(),
        messages: _slimMessages(c.messages),
    }));
}

function saveHistory() {
    try {
        const slim = _slimHistory(chatHistory);
        localStorage.setItem('vision_ai_history_v2', JSON.stringify(slim));
    } catch (e) {
        console.warn('saveHistory quota', e);
        try {
            // Aggressive: keep 8 chats, no images, short text
            const tiny = (chatHistory || []).slice(0, 8).map(c => ({
                id: c.id,
                title: (c.title || 'Chat').slice(0, 40),
                timestamp: c.timestamp || Date.now(),
                messages: (c.messages || []).slice(-12).map(m => ({
                    role: m.role,
                    text: (m.text || '').slice(0, 2000),
                    modelUsed: m.modelUsed || null,
                })),
            }));
            localStorage.setItem('vision_ai_history_v2', JSON.stringify(tiny));
            if (typeof showToast === 'function') {
                showToast('Storage almost full — old images removed from history (chat still works)', 'info', 5000);
            }
        } catch (e2) {
            try { localStorage.removeItem('vision_ai_history_v2'); } catch (_) {}
            try { localStorage.removeItem('vision_ai_recent'); } catch (_) {}
            if (typeof showToast === 'function') {
                showToast('Browser storage cleared to recover chat. Continue messaging.', 'info', 6000);
            }
        }
    }
}

function loadChat(id) {
    const chat = chatHistory.find(c => c.id === id);
    if (!chat) return;
    currentChatId = id;
    const output = ensureChatOutput();
    if (!output) return;
    hideWelcomeEmpty();
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
    const output = ensureChatOutput();
    if (!output) return;
    hideWelcomeEmpty();
    
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    const gender = getUserAvatarGender();
    const avClass = (role === 'user')
      ? ('msg-avatar user ' + gender)
      : 'msg-avatar ai';
    const avIcon = avatarEmoji(role);
    
    let html = `<div class="${avClass}" title="${role}">${avIcon}</div><div class="message-bubble" onclick="${role === 'user' ? 'editMessage(this)' : ''}">`;
    
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
        // Soft-format + math normalization
        let src = text;
        src = src
            .replace(/```(?:math|latex|tex)\s*([\s\S]*?)```/gi, function (_, body) {
                return '\n$$\n' + String(body).trim() + '\n$$\n';
            })
            .replace(/\\begin\{equation\}([\s\S]*?)\\end\{equation\}/gi, '\n$$\n$1\n$$\n')
            .replace(/\\begin\{align\*?\}([\s\S]*?)\\end\{align\*?\}/gi, '\n$$\n$1\n$$\n');

        // Pre-render $$ and $ math with KaTeX so marked cannot break LaTeX
        const mathHolders = [];
        function stashMath(tex, display) {
            var html = '';
            try {
                if (window.katex && typeof katex.renderToString === 'function') {
                    html = katex.renderToString(tex, { displayMode: !!display, throwOnError: false, strict: 'ignore' });
                } else {
                    html = display
                        ? ('<div class="katex-fallback">$$' + escapeHtml(tex) + '$$</div>')
                        : ('<span class="katex-fallback">$' + escapeHtml(tex) + '$</span>');
                }
            } catch (e) {
                html = '<code>' + escapeHtml(tex) + '</code>';
            }
            var key = 'MATHHOLD' + mathHolders.length + 'X';
            mathHolders.push(html);
            return key;
        }
        src = src.replace(/\$\$([\s\S]+?)\$\$/g, function (_, tex) {
            return '\n\n' + stashMath(String(tex).trim(), true) + '\n\n';
        });
        src = src.replace(/(^|[^$])\$([^\n$]+?)\$(?!\$)/g, function (_, pre, tex) {
            return pre + stashMath(String(tex).trim(), false);
        });

        const looksPlain = !/(^|\n)#{1,3}\s|(^|\n)[-*]\s|(^|\n)\d+\.\s|```|MATHHOLD/.test(src);
        if (looksPlain && src.length > 600) {
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
        // Restore KaTeX HTML after sanitize
        mathHolders.forEach(function (html, i) {
            var key = 'MATHHOLD' + i + 'X';
            cleanHtml = cleanHtml.split(key).join(html);
            cleanHtml = cleanHtml.replace(new RegExp('<p>\\s*' + key + '\\s*<\\/p>', 'g'), html);
        });
        const isLong = text.length > 1800;
        const hasRtl = /[\u0600-\u06FF]/.test(text) && ((text.match(/[\u0600-\u06FF]/g) || []).length > 20);
        const bodyClass = (isLong ? 'markdown-content msg-long-body' : 'markdown-content') + (hasRtl ? ' rtl' : '');
        // Force mobile-friendly download links (?dl=1 + data-force-download)
        cleanHtml = cleanHtml.replace(
            /href="([^"]*\/upload\/downloads\/[^"]+)"/g,
            function (_, href) {
                var h = href;
                if (h.indexOf('dl=') === -1) {
                    h += (h.indexOf('?') >= 0 ? '&' : '?') + 'dl=1';
                }
                return 'href="' + h + '" download target="_blank" rel="noopener" class="dl-file-link" data-force-download="1"';
            }
        );
        html += `<div class="${bodyClass}"${hasRtl ? ' dir="rtl" lang="ur"' : ''}>${cleanHtml}</div>`;
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
        // Single image → large hero; multi → responsive grid (no more 150px thumbs)
        const cols = images.length === 1
            ? 'minmax(280px, 1fr)'
            : 'repeat(auto-fill, minmax(240px, 1fr))';
        html += `<div class="ai-image-grid" style="display:grid;grid-template-columns:${cols};gap:14px;margin-top:14px;width:100%;"></div>`;
    }
    html += '</div>';
    row.innerHTML = html;
    if (typeof bindDownloadLinks === 'function') {
        bindDownloadLinks(row);
    } else {
        row.querySelectorAll('a[href*="/upload/downloads/"]').forEach(function (a) {
            a.setAttribute('download', '');
            a.classList.add('dl-file-link');
            a.setAttribute('data-force-download', '1');
            a.addEventListener('click', function (ev) {
                const href = a.getAttribute('href');
                if (!href) return;
                ev.preventDefault();
                forceMobileDownload(href, a.getAttribute('download') || '').catch(function () {
                    window.open(href, '_blank');
                });
            });
        });
    }

    if (hasImages) {
        const grid = row.querySelector('.ai-image-grid');
        const single = images.length === 1;
        images.forEach(img => {
            // svg export button available via visionSvgDownloadBtn(img)
            const raw = (img && typeof img.data === 'string') ? img.data : '';
            const isDataUri = /^data:image\/(png|jpe?g|gif|webp);base64,[A-Za-z0-9+/=]+$/.test(raw);
            const isBareBase64 = /^[A-Za-z0-9+/=]+$/.test(raw) && raw.length > 0;
            const src = isDataUri ? raw : (isBareBase64 ? `data:image/png;base64,${raw}` : '');
            if (!src) return;
            const wrap = document.createElement('div');
            wrap.className = 'ai-image-wrap';
            wrap.style.cssText = single ? 'width:100%;max-width:720px;' : 'width:100%;';
            const imgEl = document.createElement('img');
            imgEl.src = src;
            imgEl.alt = (img && img.caption) || 'Generated image';
            imgEl.loading = 'lazy';
            imgEl.style.cssText = single
                ? 'width:100%;max-height:640px;height:auto;object-fit:contain;border-radius:12px;cursor:zoom-in;border:1px solid rgba(255,255,255,0.12);background:rgba(0,0,0,0.25);display:block;'
                : 'width:100%;max-height:420px;height:auto;object-fit:contain;border-radius:10px;cursor:zoom-in;border:1px solid rgba(255,255,255,0.12);background:rgba(0,0,0,0.25);display:block;';
            imgEl.addEventListener('click', () => openImageLightbox(src, imgEl.alt));
            wrap.appendChild(imgEl);
            const bar = document.createElement('div');
            bar.className = 'ai-image-actions';
            bar.innerHTML = `
              <button type="button" class="img-act" data-act="download" title="Download">⬇️ Download</button>
              <button type="button" class="img-act" data-act="open" title="Open full size">⛶ Full</button>
              <button type="button" class="img-act" data-act="zoom" title="Zoom preview">🔍 Zoom</button>
            `;
            bar.querySelector('[data-act="download"]').onclick = () => downloadDataUrl(src, 'vision-ai-image.png');
            bar.querySelector('[data-act="open"]').onclick = () => window.open(src, '_blank');
            bar.querySelector('[data-act="zoom"]').onclick = () => openImageLightbox(src, imgEl.alt);
            wrap.appendChild(bar);
            grid.appendChild(wrap);
        });
    }
    
    output.appendChild(row);
    output.scrollTop = output.scrollHeight;
    
    row.querySelectorAll('pre code').forEach((block) => {
        if (window.hljs) hljs.highlightElement(block);
    });

    // Render LaTeX math / physics formulas (KaTeX)
    if (window.renderMathInElement) {
        try {
            renderMathInElement(row, {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false},
                    {left: '\\(', right: '\\)', display: false},
                    {left: '\\[', right: '\\]', display: true}
                ],
                throwOnError: false,
                ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
            });
        } catch (e) {
            console.warn('KaTeX render failed:', e);
        }
    }
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
    const output = ensureChatOutput();
    if (!output) return;
    hideWelcomeEmpty();

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
    (function(){ var el=document.getElementById('message'); if(el){ el.value=''; el.style.height='auto'; } })();
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
    if (stopBtn) { stopBtn.hidden = false; stopBtn.disabled = false; }
    const _msgInput = document.getElementById('message');
    if (_msgInput) { /* already captured text above */ }
    const _sendEarly = document.getElementById('sendBtn');
    if (_sendEarly) _sendEarly.disabled = true;
    showLoading();

    const formData = new FormData();
    formData.append('message', msg);
    // Short context so "what is this chat about" uses this thread
    try {
        const recent = (chat.messages || []).slice(-6).map(m => (m.role + ': ' + (m.text || '').slice(0, 200))).join('\n');
        if (recent) formData.append('history_hint', recent.slice(0, 1500));
    } catch (_) {}
    const modelSelector = document.getElementById('modelSelector');
    const modelVal = modelSelector ? modelSelector.value : (localStorage.getItem('vision_ai_model') || 'auto');
    if (modelSelector) localStorage.setItem('vision_ai_model', modelSelector.value);
    formData.append('model', modelVal === 'default' ? 'auto' : modelVal);
    formData.append('generate_images', 'true');
    const chatLang = localStorage.getItem('vision_ai_chat_lang') || 'auto';
    if (chatLang && chatLang !== 'auto') {
        formData.append('preferred_language', chatLang);
    }
    
    for (const file of filesToUpload) {
        formData.append('files', file); 
    }

    // Exam / document / YouTube / uploads need long client timeout (server budget up to 150s)
    const isHeavy = filesToUpload.length > 0 || /download|transcript|youtube\.com|youtu\.be|mp3|1080p|720p|\bpdf\b|\bsolve\b|question paper|mark scheme|past paper|this paper|this document|answer all|work through|exam\b/i.test(userMessage || '') || /\bpdf\b|\bsolve\b|question paper|mark scheme|past paper|this paper|this document|answer all|work through|exam\b/i.test(msg || '');
    const isImage = /\b(draw|image|picture|photo|generate|create|diagram|logo|illustration|photorealistic|architecture|mosque|masjid|building|graph|plot|chart|flowchart)\b/i.test(userMessage || '');
    try {
        updateLoadingStatus(isImage ? "Generating image (GPU may take 1–2 min)…" : (isHeavy ? "Working on document / long answer (may take 1–3 min)…" : "Contacting AI model..."));
        const controller = new AbortController();
        window._activeChatAbort = controller;
        const timeoutMs = isHeavy ? 300000 : (isImage ? 300000 : 90000);
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        let res;
        try {
            res = await authenticatedFetch('/chat/send', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
        } catch (fetchErr) {
            // One retry on transient network / Railway cold start
            if (fetchErr && fetchErr.name !== 'AbortError') {
                updateLoadingStatus("Reconnecting…");
                await new Promise(r => setTimeout(r, 1000));
                res = await authenticatedFetch('/chat/send', {
                    method: 'POST',
                    body: formData,
                    signal: controller.signal
                });
            } else {
                throw fetchErr;
            }
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
                data.images || null, /* images */ 
                data.model_used || null,
                data.rag_files_loaded || 0,
                data.search_performed || false,
                data.images_generated || 0
            );
            maybeHonestNoImage(message, data.images);
            chat.messages.push({ 
                role: 'ai', 
                text: data.answer, 
                images: data.images,
                modelUsed: data.model_used,
                imageCount: (data.images && data.images.length) || 0,
            });
            saveHistory();
            let _toastMsg = `Response from ${data.model_used} in ${data.response_time}s`;
            if ((data.rag_files_loaded || 0) > 0 || (data.context_length || 0) > 8000) {
                _toastMsg += ' · document context used';
            }
            showToast(_toastMsg, 'success', 2800);
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
            showToast(isImage ? 'Image timed out — wait for Colab warmup (GPU model loaded), keep Boost tab open, retry.' : 'Request timed out. Try again.', 'error', 6000);
        } else {
            const hint = (err.message || '').includes('Failed to fetch')
                ? ' Server may be waking up (Railway) or offline. Wait 10s and retry.'
                : '';
            addMessage('ai', '❌ Connection error: ' + err.message + hint);
            showToast('Connection error — retry in a few seconds.', 'error');
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
            <a class="footer-signin" href="/login.html">Sign In</a>
            <button type="button" class="sidebar-link footer-dl" onclick="downloadCurrentChat()">Download chat</button>
        `;
        return;
    }

    const nameToUse = userData.full_name || userData.username || 'User';
    const initials = nameToUse.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    const planLabel = String(plan).charAt(0).toUpperCase() + String(plan).slice(1);

    footer.innerHTML = `
        <div class="user-profile-container" onclick="window.toggleProfileDropdown()" role="button" tabindex="0" aria-haspopup="true">
            <div class="user-avatar">${escapeHtml(initials)}</div>
            <div class="user-meta">
                <div class="user-name">${escapeHtml(nameToUse)}</div>
                <div class="user-plan">${escapeHtml(planLabel)}</div>
            </div>
            <span class="user-caret">▾</span>
        </div>
        <div id="profileDropdown" class="profile-dropdown" style="display:none;" role="menu">
            <div class="avatar-gender-bar" role="group" aria-label="Avatar style" onclick="event.stopPropagation()">
              <button type="button" data-gender="male" onclick="event.stopPropagation();setUserAvatarGender('male')">Male</button>
              <button type="button" data-gender="female" onclick="event.stopPropagation();setUserAvatarGender('female')">Female</button>
              <button type="button" data-gender="neutral" onclick="event.stopPropagation();setUserAvatarGender('neutral')">Neutral</button>
            </div>
            <a href="/settings.html" role="menuitem">Settings</a>
            <a href="/upgrade.html" role="menuitem">Upgrade Plan</a>
            <button type="button" class="dl-item" onclick="downloadCurrentChat()" role="menuitem">Download chat</button>
            <button type="button" class="logout-item" onclick="window.performLogout()" role="menuitem">Log out</button>
        </div>
    `;
}

window.toggleProfileDropdown = function(ev) {
    if (ev) ev.stopPropagation();
    const dropdown = document.getElementById('profileDropdown');
    if (dropdown) {
        const open = dropdown.style.display === 'flex';
        dropdown.style.display = open ? 'none' : 'flex';
        if (!open) {
          try { setUserAvatarGender(getUserAvatarGender()); } catch (e) {}
        }
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
    const icon = theme === 'light' ? '☀️' : '🌙';
    ['floatingThemeToggle', 'headerThemeBtn', 'themeToggle'].forEach((id) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.textContent = icon;
            btn.setAttribute('aria-label', theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode');
        }
    });
}

function toggleTheme() {
    try {
        const stored = localStorage.getItem('vision_ai_theme') || 'dark';
        const next = (stored === 'light' || document.documentElement.getAttribute('data-theme') === 'light')
            ? 'dark' : 'light';
        localStorage.setItem('vision_ai_theme', next);
        applyTheme(next);
        if (typeof showToast === 'function') showToast(next === 'dark' ? 'Dark mode' : 'Light mode', 'info', 1200);
    } catch (e) {
        console.error(e);
        const cur = document.documentElement.getAttribute('data-theme');
        const next = cur === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('vision_ai_theme', next);
        if (typeof updateThemeIcon === 'function') updateThemeIcon(next);
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

const PROMPT_LIBRARY = window.PROMPT_LIBRARY = {
    "Featured": {
        icon: "⭐", color: "#34d399", tags: ["featured"],
        prompts: [
            { title: "Master exam solver", featured: true, t: "You are a Cambridge/FBISE physics examiner. Solve the uploaded paper or pasted questions step by step:\n1) Given data\n2) Formula\n3) Substitution\n4) Final answer with units\n5) One-line check.\nMark uncertain figures clearly. Reply in the same language as the user (English or simple Urdu).", tags: ["physics","exam"] },
            { title: "Explain simply", featured: true, t: "Explain [topic] in simple words a college student can understand. Use short paragraphs, one analogy, and 3 key points. Avoid jargon unless you define it.", tags: ["study"] },
            { title: "PDF / notes to Q&A", featured: true, t: "From the uploaded document only, create clear study Q&A:\n- 10 important questions\n- Detailed answers with examples from the text\nDo not invent chapters that are not in the document.", tags: ["study","exam"] }
        ]
    },
    "Physics / Exam": {
        icon: "⚛️", color: "#2dd4bf", tags: ["physics","exam"],
        prompts: [
            { title: "Step-by-step MCQ pack", t: "For each MCQ: state the concept, eliminate wrong options, give the correct letter, and a 2-sentence reason.\n\nQuestions:\n[paste]", tags: ["exam"] },
            { title: "Derive + numeric", t: "Derive the working formula from first principles, then compute with: [data]. Show units at every step. Use $$ for equations.", tags: ["physics"] },
            { title: "Past paper full solve", t: "Solve this past paper in order. For each question: marks-aware depth, working, final answer box. If a diagram is needed, describe it clearly.\n\n[paste or upload]", tags: ["exam","physics"] },
            { title: "Formula sheet", t: "Make a clean formula sheet for [chapter/topic]: formula, symbols, SI units, and one example each.", tags: ["physics","study"] }
        ]
    },
    "Study": {
        icon: "📚", color: "#38bdf8", tags: ["study"],
        prompts: [
            { title: "Summarize notes", t: "Summarize the following notes into bullet points + a 5-line revision box:\n\n[paste]", tags: ["study"] },
            { title: "Flashcards", t: "Create 15 flashcards (front/back) for:\n[topic or paste notes]", tags: ["study"] },
            { title: "Teach me like I'm new", t: "Teach [topic] from zero. Use everyday examples, then slightly harder ones. End with 3 practice questions.", tags: ["study"] }
        ]
    },
    "Urdu": {
        icon: "🇵🇰", color: "#a78bfa", tags: ["urdu"],
        prompts: [
            { title: "Easy Urdu explanation", t: "اس موضوع کو آسان پاکستانی اردو میں سمجھاؤ۔ مشکل الفاظ سے بچو۔ طریقہ، مثال، اور خلاصہ دو۔ موضوع: [topic]", tags: ["urdu","study"] },
            { title: "Accurate Urdu translation", t: "Translate into clear everyday Pakistani Urdu. Keep technical terms in English in parentheses when needed:\n\n[text]", tags: ["urdu"] },
            { title: "Urdu study notes", t: "اس موضوع پر آسان اردو نوٹس لکھیں: تعریف، فارمولے (انگریزی میں ٹھیک)، اور تین مثالیں۔ موضوع: [topic]", tags: ["urdu"] }
        ]
    },
    "YouTube": {
        icon: "🎥", color: "#f472b6", tags: ["youtube"],
        prompts: [
            { title: "Video summary + timestamps", t: "Summarize this YouTube video with timestamps, key claims, and 5 action items:\n[URL]", tags: ["youtube"] },
            { title: "Quiz from video", t: "From the transcript only, create 10 MCQs with answers and short explanations.\n[URL]", tags: ["youtube","quiz"] },
            { title: "Download helper", t: "I want to download this YouTube video as [mp3/mp4 720p]. Confirm the title and give clear next steps in the app.\n[URL]", tags: ["youtube"] }
        ]
    },
    "Code": {
        icon: "💻", color: "#60a5fa", tags: ["code"],
        prompts: [
            { title: "Debugger", t: "Find the bug, explain root cause, and provide a minimal fixed version.\nLanguage: [lang]\n\n```\n[code]\n```", tags: ["code"] },
            { title: "Explain this code", t: "Explain this code line by line in simple terms, then suggest 2 improvements:\n\n```\n[code]\n```", tags: ["code"] },
            { title: "Write a function", t: "Write a clean, documented [lang] function that does: [task]. Include example usage and edge cases.", tags: ["code"] }
        ]
    },
    "Writing": {
        icon: "✍️", color: "#fbbf24", tags: ["writing"],
        prompts: [
            { title: "Professional email", t: "Draft a clear email about [topic] for [audience]: subject line, body, and CTA. Tone: [formal/friendly].", tags: ["writing"] },
            { title: "Scene polish", t: "Rewrite this scene with stronger sensory detail and tighter dialogue. Keep the original meaning:\n\n[paste]", tags: ["writing"] },
            { title: "LinkedIn / CV bullet", t: "Turn this experience into 3 strong CV bullets with metrics where possible:\n\n[paste]", tags: ["writing"] }
        ]
    },
    "Image": {
        icon: "🖼️", color: "#fb7185", tags: ["image"],
        prompts: [
            { title: "Diagram request", t: "Create a clear labeled diagram for: [physics/biology concept]. Keep labels readable.", tags: ["image","physics"] },
            { title: "Creative image", t: "Generate an image of: [description]. Style: [realistic/illustration].", tags: ["image"] }
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

function closePromptStudio() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('ps-open', 'open', 'ps-drawer-root');
        modal.setAttribute('aria-hidden', 'true');
        // Clear any leftover transform that could hide the panel next open
        const panel = modal.querySelector('.ps-panel');
        if (panel) {
            panel.style.transform = 'none';
            panel.style.opacity = '1';
            panel.style.visibility = 'visible';
        }
    }
    document.body.classList.remove('ps-drawer-open', 'sidebar-open', 'chat-focus-mode');
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
    // Also close alternate drawer from prompt_studio.js
    const drawer = document.getElementById('promptStudioDrawer');
    if (drawer) {
        drawer.classList.remove('open');
        drawer.setAttribute('aria-hidden', 'true');
    }
    // Kill any leftover full-screen dim layers (never leave blurred page)
    document.querySelectorAll('.ps-backdrop, .prompt-studio-overlay, #sidebar-overlay').forEach(function (el) {
        el.classList.remove('active', 'open');
        if (el.id === 'sidebar-overlay') {
            el.style.display = 'none';
            el.style.pointerEvents = 'none';
            el.style.opacity = '0';
        }
    });
}

function toggleHelpModal() {
    const modal = document.getElementById('helpModal');
    const isOpen = modal && (modal.style.display === 'flex' || modal.classList.contains('ps-open'));
    if (isOpen) {
        closePromptStudio();
        return;
    }
    if (!modal) {
        createHelpModal();
    }
    const hm = document.getElementById('helpModal');
    if (!hm) return;
    hm.classList.add('ps-drawer-root', 'ps-open');
    hm.style.display = 'flex';
    hm.style.visibility = 'visible';
    hm.style.opacity = '1';
    hm.style.pointerEvents = 'auto';
    hm.setAttribute('aria-hidden', 'false');
    // Ensure panel is not left off-screen by older drawer CSS
    const panel = hm.querySelector('.ps-panel');
    if (panel) {
        panel.style.transform = 'none';
        panel.style.opacity = '1';
        panel.style.visibility = 'visible';
        panel.style.display = 'flex';
    }
    document.body.classList.add('ps-drawer-open');
    // Do NOT lock body overflow permanently — only while open, restored on close
    document.body.style.overflow = 'hidden';
    try {
        renderCategories();
        renderTagChips();
        renderPrompts();
        updateStats();
    } catch (err) {
        console.warn('Prompt Studio render:', err);
    }
    setTimeout(function () {
        const s = document.getElementById('promptSearch');
        if (s) s.focus();
    }, 50);
}
window.closePromptStudio = closePromptStudio;

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
                        <button onclick="closePromptStudio()" aria-label="Close" style="background:var(--bg-tertiary); border:1px solid var(--border-color); color:var(--text-muted); width:36px; height:36px; border-radius:10px; cursor:pointer; font-size:18px; line-height:1;">✕</button>
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
    modal.addEventListener('click', (e) => { if (e.target === modal) closePromptStudio(); });
    document.addEventListener('keydown', function _psEsc(ev) {
        if (ev.key === 'Escape') { closePromptStudio(); }
    });
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
        document.body.classList.remove('sidebar-open');
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
        var cacheChip = document.getElementById('adminCacheChip');
        var payChip = document.getElementById('adminPayChip');
        if (cacheChip) { cacheChip.hidden = false; cacheChip.style.display = 'inline-flex'; }
        if (payChip) { payChip.hidden = false; payChip.style.display = 'inline-flex'; }
    }
})();

    console.log('👁️ Vision AI v3.2.5 - Ready');
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
    document.documentElement.setAttribute('data-focus', on ? '1' : '0');
    // Browser fullscreen for true focus
    try {
        if (on && !document.fullscreenElement) {
            document.documentElement.requestFullscreen?.();
        } else if (!on && document.fullscreenElement) {
            document.exitFullscreen?.();
        }
    } catch (_) {}
    // Ensure overlays never trap clicks after focus exit
    if (!on) {
        if (typeof closeMobileSidebar === 'function') closeMobileSidebar();
        document.body.style.overflow = '';
        document.body.classList.remove('sidebar-open');
    }
    const btn = document.querySelector('[onclick="toggleChatFocusMode()"]');
    if (btn) btn.classList.toggle('active', on);
    const title = document.getElementById('chatTitle');
    if (title && !title.dataset.orig) title.dataset.orig = title.textContent;
}
// Keep class in sync when user exits fullscreen via Esc
document.addEventListener('fullscreenchange', function () {
    if (!document.fullscreenElement && document.body.classList.contains('chat-focus-mode')) {
        document.body.classList.remove('chat-focus-mode');
        document.documentElement.setAttribute('data-focus', '0');
        document.body.style.overflow = '';
        const btn = document.querySelector('[onclick="toggleChatFocusMode()"]');
        if (btn) btn.classList.remove('active');
    }
});


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
function hideWelcomeEmpty() {
    try {
        var w = document.getElementById('welcomeEmpty');
        if (w) w.style.display = 'none';
    } catch (e) {}
}
function ensureChatOutput() {
    var output = document.getElementById('chatOutput') || document.getElementById('output');
    if (output) return output;
    var main = document.querySelector('.main-content');
    if (!main) return null;
    output = document.createElement('div');
    output.id = 'chatOutput';
    output.className = 'chat-container';
    output.setAttribute('role', 'log');
    var inputArea = document.querySelector('.input-area');
    if (inputArea) main.insertBefore(output, inputArea);
    else main.appendChild(output);
    return output;
}

async function forceMobileDownload(url, suggestedName) {
    if (!url) throw new Error('No download URL');
    // Resolve relative paths; force ?dl=1 so server returns octet-stream + attachment
    var absolute = url;
    var name = (suggestedName || '').trim();
    try {
        var u = new URL(url, window.location.origin);
        if (/\/upload\/downloads\//.test(u.pathname)) {
            u.searchParams.set('dl', '1');
        }
        absolute = u.href;
        if (!name || name === 'true' || name === 'download') {
            name = (u.pathname.split('/').pop() || 'download.bin');
        }
    } catch (e) {
        if (!name) name = 'download.bin';
    }

    var isMobile = /Android|iPhone|iPad|iPod|Mobile|webOS|BlackBerry/i.test(navigator.userAgent || '') ||
        (window.matchMedia && window.matchMedia('(pointer: coarse)').matches);
    var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent || '') ||
        (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

    // CRITICAL: Do NOT load large media into a JS blob on mobile (70MB+ kills the tab).
    // Use a real <a download> navigation so the browser streams the file to disk.
    if (typeof showToast === 'function') showToast('Starting download…', 'info', 2500);

    // Prefer same-tab anchor with download attribute (keeps user-gesture for mobile browsers)
    var a = document.createElement('a');
    a.href = absolute;
    a.download = name;
    a.rel = 'noopener';
    a.style.display = 'none';
    document.body.appendChild(a);
    try {
        a.click();
    } catch (e) {
        // Fallback: open in new tab — server Content-Disposition: attachment should still save
        window.location.href = absolute;
    }
    setTimeout(function () {
        try { a.remove(); } catch (e) {}
    }, 2000);

    // Optional: for small desktop files only, try blob path in background (non-blocking)
    if (!isMobile) {
        try {
            var token =
                localStorage.getItem('vision_ai_access_token') ||
                localStorage.getItem('vision_ai_access') ||
                localStorage.getItem('vision_ai_token') ||
                localStorage.getItem('token') || '';
            var headers = { 'Accept': '*/*' };
            if (token) headers['Authorization'] = 'Bearer ' + token;
            // HEAD to check size — only blob-fetch if under 15MB
            var head = await fetch(absolute, { method: 'HEAD', headers: headers, credentials: 'include', cache: 'no-store' });
            var len = parseInt(head.headers.get('Content-Length') || '0', 10);
            if (len > 0 && len < 15 * 1024 * 1024) {
                var res = await fetch(absolute, { method: 'GET', headers: headers, credentials: 'include', cache: 'no-store' });
                if (res.ok) {
                    var blob = new Blob([await res.blob()], { type: 'application/octet-stream' });
                    var obj = URL.createObjectURL(blob);
                    var a2 = document.createElement('a');
                    a2.href = obj;
                    a2.download = name;
                    a2.style.display = 'none';
                    document.body.appendChild(a2);
                    a2.click();
                    setTimeout(function () {
                        try { URL.revokeObjectURL(obj); } catch (e) {}
                        try { a2.remove(); } catch (e) {}
                    }, 4000);
                }
            }
        } catch (e) { /* primary anchor path already fired */ }
    }

    if (typeof showToast === 'function') {
        showToast(isIOS
            ? 'If the file does not save, use the browser Share / Download menu'
            : 'Download started — check your Downloads folder',
            'success', 4000);
    }
}

function bindDownloadLinks(root) {
    var scope = root || document;
    var nodes = scope.querySelectorAll(
        'a[href*="/upload/downloads/"], a.dl-file-link, a[data-force-download], button[data-download-url]'
    );
    nodes.forEach(function (el) {
        if (el.dataset.dlBound === '1') return;
        el.dataset.dlBound = '1';
        el.addEventListener('click', function (ev) {
            var href = el.getAttribute('href') || el.getAttribute('data-download-url') || '';
            if (!href || href === '#') return;
            // Always use blob path for same-origin media downloads on touch / mobile
            var force = el.hasAttribute('data-force-download') ||
                /Android|iPhone|iPad|iPod|Mobile|webOS|BlackBerry/i.test(navigator.userAgent || '') ||
                (window.matchMedia && window.matchMedia('(pointer: coarse)').matches);
            if (!force && el.tagName === 'A' && !/\/upload\/downloads\//.test(href)) return;
            if (!/\/upload\/downloads\//.test(href) && !el.hasAttribute('data-force-download')) return;
            ev.preventDefault();
            ev.stopPropagation();
            var suggested = el.getAttribute('download') || el.getAttribute('data-filename') || '';
            // Ensure ?dl=1 on chat download links
            var hrefDl = href;
            try {
                if (/\/upload\/downloads\//.test(href)) {
                    var uu = new URL(href, window.location.origin);
                    uu.searchParams.set('dl', '1');
                    hrefDl = uu.href;
                }
            } catch (e) {}
            forceMobileDownload(hrefDl, suggested).catch(function (err) {
                console.warn('forceMobileDownload failed', err);
                // Last resort: navigate same tab so Content-Disposition attachment can fire
                window.location.href = hrefDl;
            });
        }, { passive: false });
    });
}

// Re-bind after chat mutations
document.addEventListener('DOMContentLoaded', function () {
    bindDownloadLinks(document);
    try {
        var chat = document.getElementById('chatBox') || document.getElementById('messages');
        if (chat && typeof MutationObserver !== 'undefined') {
            var mo = new MutationObserver(function () { bindDownloadLinks(chat); });
            mo.observe(chat, { childList: true, subtree: true });
        }
    } catch (e) {}
});

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
    if (now - _micToastAt < 6000) return;
    _micToastAt = now;
    showToast(msg, type || "error", ms || 9000);
}

function _micSiteHelp() {
    const host = (location && location.hostname) ? location.hostname : 'this site';
    return (
        'Mic blocked for ' + host + '. ' +
        'Click the lock/tune icon LEFT of the address bar → Permissions / Site permissions → Microphone → Allow → Reload. ' +
        '(Edge global Settings → Privacy is NOT enough — it must be allowed for THIS site.)'
    );
}

function _getSpeechRecognition() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}


function toggleVoiceInput() {
    if (_listening) {
        stopVoiceInput();
        return;
    }
    // Always allow a fresh attempt (user may have just fixed site permission)
    _micDenied = false;
    startVoiceInput();
}

async function startVoiceInput() {
    const ta = document.getElementById('message');
    const status = document.getElementById('voiceStatus');
    const mic = document.getElementById('micBtn');

    // Secure context required (localhost or https)
    if (typeof window.isSecureContext === 'boolean' && !window.isSecureContext) {
        _micToast('Mic only works on HTTPS or localhost.', 'error', 9000);
        return;
    }

    const Rec = _getSpeechRecognition();
    if (!Rec) {
        showToast('Voice input needs Chrome, Edge, or Safari (not Facebook/Telegram in-app browsers).', 'error', 6000);
        return;
    }

    // Do NOT trust Permissions API "denied" alone (Edge often reports denied while site is still promptable).
    // Always call getUserMedia — that is the real site-level permission gate.
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            _micToast('This browser cannot access the microphone (mediaDevices missing).', 'error', 8000);
            return;
        }
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
            }
        });
        stream.getTracks().forEach(t => t.stop());
        _micDenied = false;
    } catch (permErr) {
        console.warn('getUserMedia', permErr);
        _micDenied = true;
        const name = (permErr && (permErr.name || permErr.message)) || '';
        if (/NotFound|DevicesNotFound/i.test(name)) {
            _micToast('No microphone found on this device.', 'error', 8000);
        } else if (/NotReadable|TrackStart/i.test(name)) {
            _micToast('Microphone is in use by another app. Close Zoom/Teams and retry.', 'error', 9000);
        } else {
            _micToast(_micSiteHelp(), 'error', 14000);
        }
        return;
    }

    try {
        const rec = new Rec();
        rec.continuous = false;
        rec.interimResults = true;
        rec.maxAlternatives = 1;
        // Prefer user STT lang; en-US is safest default if Urdu pack missing
        let sttLang = localStorage.getItem('vision_ai_stt_lang')
            || localStorage.getItem('vision_ai_voice_lang')
            || 'en-US';
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
                _micToast(_micSiteHelp(), 'error', 14000);
                stopVoiceInput();
            } else if (e.error === 'language-not-supported') {
                try {
                    rec.lang = 'en-US';
                    rec.start();
                    showToast('STT language not supported — switched to English', 'info', 3000);
                } catch (_) {
                    showToast('Speech language not supported on this device', 'error');
                    stopVoiceInput();
                }
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
document.addEventListener('DOMContentLoaded', function(){ try { setUserAvatarGender(getUserAvatarGender()); } catch(e){} });
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

console.log('👁️ Vision AI v3.2.0 - Ready');
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


(function restoreModelSelector() {
  function run() {
    const sel = document.getElementById('modelSelector');
    if (!sel) return;
    const saved = localStorage.getItem('vision_ai_model');
    if (saved) {
      const opt = [...sel.options].find(o => o.value === saved);
      if (opt) sel.value = saved;
    }
    sel.addEventListener('change', () => localStorage.setItem('vision_ai_model', sel.value));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
})();


// Reset mic deny flag when user returns (after changing site permissions)
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && typeof _micDenied !== 'undefined') {
    _micDenied = false;
  }
});


function downloadCurrentChat() {
  try {
    const chat = window.currentChat || window.chat || null;
    let text = "";
    if (chat && Array.isArray(chat.messages) && chat.messages.length) {
      text = chat.messages.map(function(m) {
        const role = (m.role || m.sender || "msg").toUpperCase();
        return role + ":\n" + (m.text || m.content || "") + "\n";
      }).join("\n");
    } else {
      const out = document.getElementById("chatOutput") || document.getElementById("output");
      if (out) text = out.innerText || out.textContent || "";
    }
    if (!text || !String(text).trim()) {
      if (typeof showToast === "function") showToast("Nothing to download yet", "info", 2000);
      return;
    }
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "vision-ai-chat.txt";
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function() { URL.revokeObjectURL(url); }, 1500);
    if (typeof showToast === "function") showToast("Chat download started", "success", 2000);
  } catch (e) {
    console.error(e);
    if (typeof showToast === "function") showToast("Download failed", "error", 3000);
  }
}

window.downloadCurrentChat = downloadCurrentChat;

function maybeHonestNoImage(userText, images) {
  try {
    const wants = /\b(image|picture|photo|draw|generate|illustration|1080p|logo)\b/i.test(userText || '');
    if (!wants) return;
    if (images && images.length) return;
    const output = ensureChatOutput();
    if (!output) return;
    const tip = document.createElement('div');
    tip.className = 'message-row ai';
    tip.innerHTML = '<div class="message-bubble" style="border:1px solid rgba(248,113,113,0.45)"><strong>No image was generated.</strong> Text-only reply is not a picture. Open <a href="/boost.html">/boost.html</a>, keep Colab GPU online (warmed), ensure HF_TOKEN, then try a shorter prompt.</div>';
    output.appendChild(tip);
  } catch (e) {}
}
window.maybeHonestNoImage = maybeHonestNoImage;


/* Theme presets */
function applyThemePreset(name) {
  const n = (name || 'default').trim();
  const val = (n === 'default') ? '' : n;
  document.documentElement.setAttribute('data-theme-preset', val);
  if (document.body) document.body.setAttribute('data-theme-preset', val);
  try { localStorage.setItem('vision_theme_preset', n); } catch (e) {}
  const lightPresets = ['soft-sepia', 'sand'];
  if (lightPresets.indexOf(n) >= 0) {
    document.documentElement.setAttribute('data-theme', 'light');
    try { localStorage.setItem('vision_ai_theme', 'light'); } catch (e) {}
  } else if (n && n !== 'default') {
    document.documentElement.setAttribute('data-theme', 'dark');
    try { localStorage.setItem('vision_ai_theme', 'dark'); } catch (e) {}
  }
  try { document.documentElement.style.setProperty('--theme-tick', String(Date.now())); } catch (e2) {}
}
function toggleGlassMode(level) {
  const levels = ['off', 'soft', 'strong'];
  let next = level;
  if (!next) {
    const cur = document.documentElement.getAttribute('data-glass') || 'strong';
    const i = levels.indexOf(cur);
    next = levels[(i + 1) % levels.length];
  }
  document.documentElement.setAttribute('data-glass', next);
  try { localStorage.setItem('vision_glass_mode', next); } catch (e) {}
  if (typeof showToast === 'function') showToast('Glass: ' + next, 'info', 1200);
  return next;
}
window.toggleGlassMode = toggleGlassMode;

function initThemePreset() {
  try {
    const n = localStorage.getItem('vision_theme_preset') || 'humanly';
    applyThemePreset(n);
  } catch (e) {}
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initThemePreset);
} else { initThemePreset(); }
window.applyThemePreset = applyThemePreset;


/* Theme picker UI */
function initThemePicker() {
  var root = document.getElementById("themePicker");
  var btn = document.getElementById("themePickerBtn");
  if (!root || !btn) return;
  btn.addEventListener("click", function(e) {
    e.stopPropagation();
    root.classList.toggle("open");
    btn.setAttribute("aria-expanded", root.classList.contains("open") ? "true" : "false");
  });
  root.querySelectorAll(".theme-swatch").forEach(function(sw) {
    sw.addEventListener("click", function(e) {
      e.stopPropagation();
      var preset = sw.getAttribute("data-preset") || "default";
      if (typeof applyThemePreset === "function") applyThemePreset(preset);
      // Humanly works best with dark base
      if (preset === "humanly" || preset === "nord" || preset === "sunset") {
        try { localStorage.setItem("vision_ai_theme", "dark"); } catch (err) {}
        if (typeof applyTheme === "function") applyTheme("dark");
      }
      if (preset === "soft-sepia" || preset === "sand") {
        try { localStorage.setItem("vision_ai_theme", "light"); } catch (err) {}
        if (typeof applyTheme === "function") applyTheme("light");
      } else if (["humanly","nord","ocean","forest","violet","rose","midnight","sunset","default","high-contrast","emerald","frost","ember"].indexOf(preset) >= 0) {
        try { localStorage.setItem("vision_ai_theme", "dark"); } catch (err) {}
        if (typeof applyTheme === "function") applyTheme("dark");
      }
      root.classList.remove("open");
      if (typeof showToast === "function") showToast("Theme: " + preset, "info", 1500);
    });
  });
  document.addEventListener("click", function() { root.classList.remove("open"); });
}
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initThemePicker);
} else { initThemePicker(); }

// Default preset: humanly if none saved
(function() {
  try {
    if (!localStorage.getItem("vision_theme_preset")) {
      localStorage.setItem("vision_theme_preset", "humanly");
    }
  } catch (e) {}
})();

(function(){
  function syncSidebarAttr(){
    try {
      var sb = document.getElementById('sidebar');
      var open = window.innerWidth > 768 || (sb && sb.classList.contains('open-mobile'));
      document.documentElement.setAttribute('data-sidebar', open ? 'open' : 'closed');
        /* keep search title visible */
    } catch(e){}
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncSidebarAttr);
  else syncSidebarAttr();
  window.addEventListener('resize', syncSidebarAttr);
})();


// Sync browser tab title + meta with live server version
(function syncLiveVersion(){
  function apply(ver) {
    if (!ver) return;
    try {
      document.title = "Vision AI v" + ver + " — Chat";
      var m = document.querySelector('meta[name="app-version"]');
      if (m) m.setAttribute("content", ver);
      window.__VISION_VERSION__ = ver;
    } catch (e) {}
  }
  function run() {
    fetch("/api/version").then(function(r){ return r.json(); }).then(function(d){
      apply(d.version || d.current);
    }).catch(function(){ apply("3.2.0"); });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();


// Escape always dismisses Prompt Studio overlay
document.addEventListener('keydown', function (ev) {
  if (ev.key === 'Escape' && typeof closePromptStudio === 'function') closePromptStudio();
});

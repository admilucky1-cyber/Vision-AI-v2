
function showAuthToast(message, type) {
    type = type || 'success';
    var existing = document.querySelector('.auth-toast');
    if (existing) existing.remove();
    var el = document.createElement('div');
    el.className = 'auth-toast ' + type;
    el.innerHTML = '<span class="toast-icon">' + (type === 'success' ? '✓' : '!') + '</span><span>' + message + '</span>';
    document.body.appendChild(el);
    requestAnimationFrame(function () {
        requestAnimationFrame(function () { el.classList.add('show'); });
    });
    setTimeout(function () {
        el.classList.remove('show');
        setTimeout(function () { el.remove(); }, 500);
    }, 3200);
}

// ============================================================
// VISION AI v2.0 - AUTH FRONTEND (Production Ready)
// ============================================================

const API_BASE = '';

// ============================================================
// 🛡️ SECURITY UTILITIES
// ============================================================

// Prevent XSS in error messages and user inputs
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Validate email format
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ============================================================
// 🌙 THEME SUPPORT
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

// Apply saved theme on load
const savedTheme = localStorage.getItem('vision_ai_theme') || 'dark';
applyTheme(savedTheme);

// Listen for system theme changes if using system theme
if (savedTheme === 'system') {
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
        applyTheme('system');
    });
}

// ============================================================
// 🚀 DOM READY
// ============================================================
let domReady = false;

document.addEventListener('DOMContentLoaded', function() {
    if (domReady) return;
    domReady = true;

    // Check if user is already logged in
    const token = localStorage.getItem('vision_ai_access_token');
    if (token && window.location.pathname.includes('login.html')) {
        showAuthToast('Login successful — welcome back!', 'success'); setTimeout(function(){ window.location.href = '/'; }, 900);
        return;
    }

    // Auto-focus first input
    const firstInput = document.querySelector('input:not([type="hidden"])');
    if (firstInput) firstInput.focus();

    // Add enter key support for forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) submitBtn.click();
            }
        });
    });

    console.log('👁️ Vision AI Auth - Ready');
});

// ============================================================
// 📋 TAB SWITCHING
// ============================================================
function switchTab(tab, event) {
    // Guard against missing elements
    const tabs = document.querySelectorAll('.tab-btn');
    const sections = document.querySelectorAll('.form-section');
    const errorEl = document.getElementById('errorMsg');
    
    if (!tabs.length || !sections.length) return;
    
    tabs.forEach(btn => btn.classList.remove('active'));
    sections.forEach(sec => sec.classList.remove('active'));
    
    // Ensure event.target exists
    if (event && event.target) {
        event.target.classList.add('active');
    } else {
        // Fallback: find tab by data attribute
        const tabBtn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
        if (tabBtn) tabBtn.classList.add('active');
    }
    
    const targetSection = document.getElementById(tab + 'Section');
    if (targetSection) targetSection.classList.add('active');
    
    if (errorEl) errorEl.style.display = 'none';
    
    // Clear form errors
    document.querySelectorAll('.input-error').forEach(el => el.remove());
    
    // Focus first input in active section
    const firstInput = targetSection?.querySelector('input:not([type="hidden"])');
    if (firstInput) setTimeout(() => firstInput.focus(), 100);
}

// ============================================================
// 👁️ PASSWORD TOGGLE
// ============================================================
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    if (btn) btn.textContent = isPassword ? '🙈' : '👁️';
}

// ============================================================
// ❌ ERROR HANDLING
// ============================================================
function showError(msg) {
    const errorEl = document.getElementById('errorMsg');
    const errorText = document.getElementById('errorText');
    
    if (errorEl && errorText) {
        errorText.textContent = escapeHtml(msg);
        errorEl.style.display = 'flex';
        // Add shake animation for better UX
        errorEl.style.animation = 'none';
        setTimeout(() => {
            errorEl.style.animation = 'shake 0.5s ease';
        }, 10);
    } else {
        // Fallback to alert if DOM elements missing
        alert('Error: ' + msg);
    }
}

function hideError() {
    const errorEl = document.getElementById('errorMsg');
    if (errorEl) errorEl.style.display = 'none';
}

// ============================================================
// ⏳ LOADING STATE
// ============================================================
function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    
    btn.disabled = loading;
    btn.classList.toggle('loading', loading);
    
    // Store original text if not already stored
    if (loading && !btn.dataset.originalText) {
        btn.dataset.originalText = btn.textContent;
        btn.textContent = '⏳ Please wait...';
    } else if (!loading && btn.dataset.originalText) {
        btn.textContent = btn.dataset.originalText;
        delete btn.dataset.originalText;
    }
}

// ============================================================
// 🔐 LOGIN HANDLER (UPDATED)
// ============================================================
async function handleLogin(event) {
    if (event) event.preventDefault();
    hideError();
    
    const usernameInput = document.getElementById('loginUsername');
    const passwordInput = document.getElementById('loginPassword');
    const loginBtn = document.getElementById('loginBtn');
    
    if (!usernameInput || !passwordInput) {
        showError('Form elements not found. Please refresh.');
        return;
    }
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    
    // Validation
    if (!username || !password) {
        showError('Please enter both username and password.');
        usernameInput.focus();
        return;
    }
    
    if (username.length < 3) {
        showError('Username must be at least 3 characters.');
        usernameInput.focus();
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters.');
        passwordInput.focus();
        return;
    }

    setLoading('loginBtn', true);
    hideError();

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        // Add timeout for fetch
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/x-www-form-urlencoded', 
                'Accept': 'application/json' 
            },
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const data = await res.json();

        if (res.ok) {
            // Store tokens
            localStorage.setItem('vision_ai_access_token', data.access_token);
            if (data.refresh_token) {
                localStorage.setItem('vision_ai_refresh_token', data.refresh_token);
            }
            
            // ✅ UPDATED: Store user info (username, full_name, and email)
            localStorage.setItem('vision_ai_user', JSON.stringify({ 
                username: data.username || username,
                full_name: data.full_name || username,
                email: data.email || '' 
            }));
            
            // Plan is intentionally not set here -- /auth/login doesn't return
            // it. index.js's checkAuth() fetches the real plan from /auth/me
            // right after redirect, avoiding a wrong "Free" flash for paid
            // users logging back in.
            showToast('✅ Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 500);
        } else {
            const errorMsg = data.detail || 'Login failed. Check your credentials.';
            showError(errorMsg);
            setLoading('loginBtn', false);
            if (passwordInput) passwordInput.value = '';
            if (passwordInput) passwordInput.focus();
        }
    } catch (err) {
        setLoading('loginBtn', false);
        if (err.name === 'AbortError') {
            showError('Request timed out. Please check your connection.');
        } else if (err.message === 'Failed to fetch') {
            showError('Cannot connect to server. Is it running?');
        } else {
            showError('Connection error: ' + err.message);
        }
        console.error('Login error:', err);
    }
}

// ============================================================
// 📝 REGISTER HANDLER (UPDATED)
// ============================================================
async function handleRegister(event) {
    if (event) event.preventDefault();
    hideError();
    
    const usernameInput = document.getElementById('regUsername');
    const fullNameInput = document.getElementById('regFullName');
    const emailInput = document.getElementById('regEmail');
    const passwordInput = document.getElementById('regPassword');
    const registerBtn = document.getElementById('registerBtn');
    
    if (!usernameInput || !fullNameInput || !emailInput || !passwordInput) {
        showError('Form elements not found. Please refresh.');
        return;
    }
    
    const username = usernameInput.value.trim();
    const fullName = fullNameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    
    // Validation
    if (!username || !fullName || !email || !password) {
        showError('All fields are required.');
        usernameInput.focus();
        return;
    }
    
    if (username.length < 3) {
        showError('Username must be at least 3 characters.');
        usernameInput.focus();
        return;
    }
    
    if (!isValidEmail(email)) {
        showError('Please enter a valid email address.');
        emailInput.focus();
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters.');
        passwordInput.focus();
        return;
    }

    setLoading('registerBtn', true);
    hideError();

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000);

        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                username, 
                full_name: fullName, 
                email, 
                password 
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const data = await res.json();

        if (res.ok) {
            showToast('✅ Account created! Logging you in...', 'success');
            
            // Auto-login after registration
            const loginFormData = new URLSearchParams();
            loginFormData.append('username', username);
            loginFormData.append('password', password);

            const loginRes = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: loginFormData,
            });
            
            const loginData = await loginRes.json();
            if (loginRes.ok) {
                localStorage.setItem('vision_ai_access_token', loginData.access_token);
                if (loginData.refresh_token) {
                    localStorage.setItem('vision_ai_refresh_token', loginData.refresh_token);
                }
                
                // ✅ UPDATED: Store email during auto-login
                localStorage.setItem('vision_ai_user', JSON.stringify({ 
                    username: loginData.username || username,
                    full_name: fullName,
                    email: loginData.email || email
                }));
                
                localStorage.setItem('vision_ai_plan', 'Free');
                setTimeout(() => {
                    window.location.href = '/';
                }, 500);
            } else {
                showError('Account created! Please login manually.');
                setLoading('registerBtn', false);
                switchTab('login');
                const loginUsername = document.getElementById('loginUsername');
                if (loginUsername) {
                    loginUsername.value = username;
                    loginUsername.focus();
                }
            }
        } else {
            const errorMsg = data.detail || 'Registration failed.';
            showError(errorMsg);
            setLoading('registerBtn', false);
        }
    } catch (err) {
        setLoading('registerBtn', false);
        if (err.name === 'AbortError') {
            showError('Request timed out. Please check your connection.');
        } else if (err.message === 'Failed to fetch') {
            showError('Cannot connect to server. Is it running?');
        } else {
            showError('Connection error: ' + err.message);
        }
        console.error('Registration error:', err);
    }
}

// ============================================================
// 🔵 GOOGLE LOGIN
// ============================================================
function handleGoogleLogin() {
    try {
        localStorage.setItem('vision_ai_plan', 'Free');
        window.location.href = '/auth/google';
    } catch (err) {
        console.error('Google login error:', err);
        showError('Failed to initiate Google login. Please try again.');
    }
}

// ============================================================
// 🟢 TOAST NOTIFICATIONS (Reused from main app)
// ============================================================
function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = `
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
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { error: '⚠️', success: '✅', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${escapeHtml(String(message))}</span>`;
    toast.style.cssText = `
        padding: 12px 16px;
        border-radius: 10px;
        background: var(--bg-secondary, #ffffff);
        border: 1px solid var(--border-color, #e5e7eb);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        display: flex;
        align-items: center;
        gap: 10px;
        animation: toastIn 0.3s ease-out;
        backdrop-filter: blur(8px);
        font-size: 14px;
        color: var(--text-main, #1a1a1a);
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

// ============================================================
// 🎨 ADD TOAST ANIMATIONS
// ============================================================
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
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        .loading {
            opacity: 0.7;
            cursor: not-allowed;
        }
        .input-error {
            border-color: #ef4444 !important;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
        }
        .tab-btn.active {
            background: rgba(0, 198, 255, 0.15);
            color: #00C6FF;
            border-color: #00C6FF;
        }
        .form-section {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        .form-section.active {
            display: block;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
}

// ============================================================
// 🔄 EXPORT FUNCTIONS FOR GLOBAL ACCESS
// ============================================================
window.applyTheme = applyTheme;
window.switchTab = switchTab;
window.togglePassword = togglePassword;
window.showError = showError;
window.hideError = hideError;
window.setLoading = setLoading;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.handleGoogleLogin = handleGoogleLogin;
window.showToast = showToast;
window.escapeHtml = escapeHtml;
window.isValidEmail = isValidEmail;

// ============================================================
// 🟢 ADDITIONAL SAFEGUARDS
// ============================================================

// Prevent multiple initializations
if (window._visionAuthInitialized) {
    console.warn('Vision AI Auth already initialized!');
} else {
    window._visionAuthInitialized = true;
}

// Global error handler
window.onerror = function(msg, url, line, col, error) {
    console.error('Global error:', msg, error);
    showToast('An unexpected error occurred. Please refresh the page.', 'error');
    return true;
};

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred.', 'error');
});

// Handle visibility change to refresh theme
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        const theme = localStorage.getItem('vision_ai_theme') || 'dark';
        applyTheme(theme);
    }
});

console.log('👁️ Vision AI Auth v2.0 - Ready');
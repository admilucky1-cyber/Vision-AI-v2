// ============================================================
// VISION AI v2.0 - AUTH FRONTEND
// ============================================================

const API_BASE = '';

// ============================================================
// THEME SUPPORT
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

document.addEventListener('DOMContentLoaded', function() {
    // Ensure DOM is ready before attaching events
});

function switchTab(tab, event) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.form-section').forEach(sec => sec.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tab + 'Section').classList.add('active');
    document.getElementById('errorMsg').style.display = 'none';
}

function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    btn.textContent = isPassword ? '🙈' : '👁️';
}

function showError(msg) {
    const errorEl = document.getElementById('errorMsg');
    document.getElementById('errorText').textContent = msg;
    errorEl.style.display = 'flex';
}

function hideError() {
    document.getElementById('errorMsg').style.display = 'none';
}

function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    btn.disabled = loading;
    btn.classList.toggle('loading', loading);
}

async function handleLogin(event) {
    event.preventDefault();
    hideError();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showError('Please enter both username and password.');
        return;
    }

    setLoading('loginBtn', true);

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json' },
            body: formData,
        });

        const data = await res.json();

        if (res.ok) {
            localStorage.setItem('vision_ai_access_token', data.access_token);
            localStorage.setItem('vision_ai_refresh_token', data.refresh_token);
            
            localStorage.setItem('vision_ai_user', JSON.stringify({ 
                name: data.username, 
                full_name: data.username 
            }));
            
            localStorage.setItem('vision_ai_plan', 'Free');
            window.location.href = '/';
        } else {
            showError(data.detail || 'Login failed. Check your credentials.');
            setLoading('loginBtn', false);
        }
    } catch (err) {
        showError('Connection error. Is the server running?');
        setLoading('loginBtn', false);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    hideError();
    
    const username = document.getElementById('regUsername').value.trim();
    const fullName = document.getElementById('regFullName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    
    if (!username || !fullName || !email || !password) {
        showError('All fields are required.');
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters.');
        return;
    }

    setLoading('registerBtn', true);

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, full_name: fullName, email, password }),
        });

        const data = await res.json();

        if (res.ok) {
            const loginRes = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ username, password }),
            });
            
            const loginData = await loginRes.json();
            if (loginRes.ok) {
                localStorage.setItem('vision_ai_access_token', loginData.access_token);
                localStorage.setItem('vision_ai_refresh_token', loginData.refresh_token);
                
                localStorage.setItem('vision_ai_user', JSON.stringify({ 
                    name: loginData.username, 
                    full_name: fullName 
                }));
                
                localStorage.setItem('vision_ai_plan', 'Free');
                window.location.href = '/';
            } else {
                showError('Account created! Please login.');
                switchTab('login');
                setLoading('registerBtn', false);
            }
        } else {
            showError(data.detail || 'Registration failed.');
            setLoading('registerBtn', false);
        }
    } catch (err) {
        showError('Connection error. Is the server running?');
        setLoading('registerBtn', false);
    }
}

function handleGoogleLogin() {
    localStorage.setItem('vision_ai_plan', 'Free');
    window.location.href = '/auth/google';
}
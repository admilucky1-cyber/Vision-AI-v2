/**
 * VisionAuth — single logout / token path (Container-level shared service)
 */
(function (global) {
  const KEY_ACCESS = 'vision_ai_access_token';
  const KEY_REFRESH = 'vision_ai_refresh_token';

  function getAccessToken() {
    return localStorage.getItem(KEY_ACCESS);
  }
  function getRefreshToken() {
    return localStorage.getItem(KEY_REFRESH);
  }
  function setTokens(access, refresh) {
    if (access) localStorage.setItem(KEY_ACCESS, access);
    if (refresh) localStorage.setItem(KEY_REFRESH, refresh);
  }
  function clearTokens() {
    localStorage.removeItem(KEY_ACCESS);
    localStorage.removeItem(KEY_REFRESH);
    try {
      sessionStorage.removeItem(KEY_ACCESS);
    } catch (_) {}
  }

  async function logout() {
    clearTokens();
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
    } catch (_) {
      /* offline ok */
    }
    window.location.href = '/login.html';
  }

  const VisionAuth = {
    getAccessToken,
    getRefreshToken,
    setTokens,
    clearTokens,
    logout,
  };

  global.VisionAuth = VisionAuth;
  // Back-compat for older callers
  global.getAccessToken = getAccessToken;
  global.getRefreshToken = getRefreshToken;
  global.setTokens = setTokens;
  global.performLogout = logout;
})(typeof window !== 'undefined' ? window : globalThis);

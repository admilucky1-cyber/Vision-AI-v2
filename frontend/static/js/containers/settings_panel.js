/**
 * Container: SettingsPanel helpers (shared logout)
 */
(function (global) {
  function mount(el) {
    if (!el || el.dataset.vaMounted === 'true') return;
    el.dataset.vaMounted = 'true';
    el.classList.add('container-settings-panel');
    el.querySelectorAll('[data-action="logout"]').forEach((btn) => {
      if (btn.dataset.vaLogoutBound) return;
      btn.dataset.vaLogoutBound = '1';
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        if (global.VisionAuth && global.VisionAuth.logout) {
          await global.VisionAuth.logout();
        } else if (typeof global.performLogout === 'function') {
          await global.performLogout();
        }
      });
    });
  }

  global.VAContainers = global.VAContainers || {};
  global.VAContainers.SettingsPanel = { mount };
})(typeof window !== 'undefined' ? window : globalThis);

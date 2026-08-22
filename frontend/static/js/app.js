/**
 * Vision AI v5.1.0 — Container & Widget boot
 * Load AFTER auth.js + sidebar.js. Does not rewrite backend APIs.
 */
(function (global) {
  function boot() {
    const C = global.VAContainers || {};
    const W = global.VAWidgets || {};

    if (global.__vaSidebar && typeof global.__vaSidebar.bind === 'function') {
      global.__vaSidebar.bind();
    }

    document.querySelectorAll('[data-container="chat-shell"]').forEach((el) => {
      C.ChatShell && C.ChatShell.mount(el);
    });
    // Fallback: main chat area
    const chat = document.querySelector('.chat-container, #chatContainer, main.main-content');
    if (chat && C.ChatShell) C.ChatShell.mount(chat);

    const side = document.getElementById('sidebar');
    if (side && C.WorkspaceSidebar) C.WorkspaceSidebar.mount(side);

    document.querySelectorAll('[data-container="settings-panel"]').forEach((el) => {
      C.SettingsPanel && C.SettingsPanel.mount(el);
    });

    document.querySelectorAll('[data-widget="composer"], .composer, .input-area, #composer').forEach((el) => {
      W.Composer && W.Composer.mount(el);
    });

    const profile =
      document.querySelector('[data-widget="profile-menu"]') ||
      document.getElementById('profileButton') ||
      document.querySelector('.sidebar-footer');
    if (profile && W.ProfileMenu) W.ProfileMenu.mount(profile);

    document.documentElement.setAttribute('data-va-version', '5.1.0');
    console.info('[Vision AI] 5.1.0 Container/Widget boot OK');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  global.VABoot = boot;
})(typeof window !== 'undefined' ? window : globalThis);

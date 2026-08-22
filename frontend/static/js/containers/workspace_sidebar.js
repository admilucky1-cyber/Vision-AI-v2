/**
 * Container: WorkspaceSidebar — delegates ONLY to __vaSidebar
 */
(function (global) {
  function mount(el) {
    if (!el || el.dataset.vaMounted === 'true') return;
    el.dataset.vaMounted = 'true';
    el.classList.add('container-workspace-sidebar');
    const api = global.__vaSidebar;
    el.querySelectorAll('[data-action="toggle-sidebar"]').forEach((btn) => {
      if (btn.dataset.vaSideBound) return;
      btn.dataset.vaSideBound = '1';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (api && typeof api.toggleSidebar === 'function') api.toggleSidebar();
        else if (typeof global.toggleSidebar === 'function') global.toggleSidebar();
      });
    });
  }

  global.VAContainers = global.VAContainers || {};
  global.VAContainers.WorkspaceSidebar = { mount };
})(typeof window !== 'undefined' ? window : globalThis);

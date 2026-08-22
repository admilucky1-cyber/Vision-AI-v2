/**
 * __vaSidebar — single sidebar state machine
 * ≤900 drawer · ≥901 desktop
 * Nothing else should toggle open-mobile / overlay classes.
 */
(function (global) {
  const MQ = window.matchMedia('(max-width: 900px)');
  let sidebar, overlay;

  function els() {
    sidebar = sidebar || document.getElementById('sidebar');
    overlay = overlay || document.getElementById('sidebar-overlay');
    return { sidebar, overlay };
  }

  function isMobile() {
    return MQ.matches;
  }

  function openSidebar() {
    const { sidebar, overlay } = els();
    if (!sidebar) return;
    if (isMobile()) {
      sidebar.classList.add('open-mobile');
      sidebar.classList.add('sidebar-open');
      if (overlay) overlay.classList.add('active');
      document.body.classList.add('sidebar-open');
      sidebar.setAttribute('data-sidebar', 'open');
    } else {
      sidebar.classList.remove('rail-collapsed');
      sidebar.classList.add('sidebar-open');
      sidebar.setAttribute('data-sidebar', 'open');
    }
  }

  function closeSidebar() {
    const { sidebar, overlay } = els();
    if (!sidebar) return;
    sidebar.classList.remove('open-mobile', 'sidebar-open');
    if (overlay) overlay.classList.remove('active');
    document.body.classList.remove('sidebar-open');
    sidebar.setAttribute('data-sidebar', 'closed');
    if (!isMobile()) {
      /* desktop may use rail collapse separately */
    }
  }

  function toggleSidebar() {
    const { sidebar } = els();
    if (!sidebar) return;
    if (isMobile()) {
      if (sidebar.classList.contains('open-mobile')) closeSidebar();
      else openSidebar();
    } else {
      sidebar.classList.toggle('rail-collapsed');
      const open = !sidebar.classList.contains('rail-collapsed');
      sidebar.setAttribute('data-sidebar', open ? 'open' : 'rail');
    }
  }

  function reconcileSidebarLayout() {
    const { sidebar, overlay } = els();
    if (!sidebar) return;
    if (!isMobile()) {
      sidebar.classList.remove('open-mobile');
      if (overlay) overlay.classList.remove('active');
      document.body.classList.remove('sidebar-open');
    }
  }

  function bind() {
    els();
    MQ.addEventListener('change', reconcileSidebarLayout);
    window.addEventListener('orientationchange', () => {
      setTimeout(reconcileSidebarLayout, 100);
    });
    const { overlay } = els();
    if (overlay && !overlay.dataset.vaBound) {
      overlay.dataset.vaBound = '1';
      overlay.addEventListener('click', closeSidebar);
    }
    document.querySelectorAll('[data-action="toggle-sidebar"]').forEach((btn) => {
      if (btn.dataset.vaBound) return;
      btn.dataset.vaBound = '1';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        toggleSidebar();
      });
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isMobile()) closeSidebar();
    });
    reconcileSidebarLayout();
  }

  const api = {
    openSidebar,
    closeSidebar,
    toggleSidebar,
    reconcileSidebarLayout,
    isMobile,
    bind,
  };

  global.__vaSidebar = api;
  global.visionSidebarController = api;
  global.openSidebar = openSidebar;
  global.closeSidebar = closeSidebar;
  global.toggleSidebar = toggleSidebar;
  global.closeMobileSidebar = closeSidebar;
  global.reconcileSidebarLayout = reconcileSidebarLayout;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})(typeof window !== 'undefined' ? window : globalThis);

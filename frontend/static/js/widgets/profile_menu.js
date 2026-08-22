/**
 * Widget: ProfileMenu — accessible dropdown, no inline onclick required
 */
(function (global) {
  function mount(root) {
    if (!root || root.dataset.vaMounted === 'true') return;
    root.dataset.vaMounted = 'true';
    root.classList.add('widget-profile-menu');

    const trigger =
      root.querySelector('[data-action="toggle-profile"]') ||
      root.querySelector('#profileButton') ||
      root;
    let menu =
      root.querySelector('[role="menu"]') ||
      root.querySelector('.profile-dropdown') ||
      document.getElementById('profileDropdown');

    if (!trigger) return;

    trigger.setAttribute('role', 'button');
    trigger.setAttribute('tabindex', '0');
    trigger.setAttribute('aria-haspopup', 'true');
    trigger.setAttribute('aria-expanded', 'false');

    function open() {
      if (!menu) return;
      menu.hidden = false;
      menu.classList.add('open', 'show');
      trigger.setAttribute('aria-expanded', 'true');
    }
    function close() {
      if (!menu) return;
      menu.hidden = true;
      menu.classList.remove('open', 'show');
      trigger.setAttribute('aria-expanded', 'false');
    }
    function toggle(e) {
      if (e) e.stopPropagation();
      if (!menu) return;
      const isOpen = trigger.getAttribute('aria-expanded') === 'true';
      if (isOpen) close();
      else open();
    }

    trigger.addEventListener('click', toggle);
    trigger.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggle(e);
      }
      if (e.key === 'Escape') close();
    });
    document.addEventListener('click', (e) => {
      if (!root.contains(e.target) && menu && !menu.contains(e.target)) close();
    });

    // Logout action inside menu
    if (menu) {
      menu.querySelectorAll('[data-action="logout"]').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
          e.preventDefault();
          if (global.VisionAuth) await global.VisionAuth.logout();
          else if (global.performLogout) await global.performLogout();
        });
      });
    }

    global.ProfileController = { open, close, toggle };
  }

  global.VAWidgets = global.VAWidgets || {};
  global.VAWidgets.ProfileMenu = { mount };
})(typeof window !== 'undefined' ? window : globalThis);

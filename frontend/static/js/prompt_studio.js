/**
 * Vision AI v2.7.6 — Prompt Studio drawer
 * Load AFTER frontend/static/js/index.js
 * Requires: PROMPT_LIBRARY, usePromptInChat, renderPrompts (from index.js)
 * Opens as a right-side drawer over chat (no full page reload).
 */
(function (global) {
  'use strict';

  const DRAWER_ID = 'helpModal';

  function ensureDrawerClass() {
    const modal = document.getElementById(DRAWER_ID);
    if (!modal) return null;
    modal.classList.add('ps-drawer-root');
    const panel = modal.querySelector('.ps-panel');
    if (panel) panel.classList.add('ps-drawer-panel');
    return modal;
  }

  function openPromptStudio() {
    if (typeof global.createHelpModal === 'function' && !document.getElementById(DRAWER_ID)) {
      global.createHelpModal();
    }
    let modal = document.getElementById(DRAWER_ID);
    if (!modal && typeof global.toggleHelpModal === 'function') {
      global.toggleHelpModal();
      modal = document.getElementById(DRAWER_ID);
    }
    if (!modal) return;

    ensureDrawerClass();
    modal.style.display = 'flex';
    modal.classList.add('ps-open');
    document.body.classList.add('ps-drawer-open');

    if (typeof global.renderCategories === 'function') global.renderCategories();
    if (typeof global.renderTagChips === 'function') global.renderTagChips();
    if (typeof global.renderPrompts === 'function') global.renderPrompts();
    if (typeof global.updateStats === 'function') global.updateStats();

    setTimeout(() => {
      const s = document.getElementById('promptSearch');
      if (s) s.focus();
    }, 40);
  }

  function closePromptStudio() {
    const modal = document.getElementById(DRAWER_ID);
    if (!modal) return;
    modal.classList.remove('ps-open');
    modal.style.display = 'none';
    document.body.classList.remove('ps-drawer-open');
  }

  function togglePromptStudio() {
    const modal = document.getElementById(DRAWER_ID);
    if (modal && (modal.style.display === 'flex' || modal.classList.contains('ps-open'))) {
      closePromptStudio();
    } else {
      openPromptStudio();
    }
  }

  // Prefer drawer close when a prompt is applied
  const prevUse = global.usePromptInChat;
  if (typeof prevUse === 'function') {
    global.usePromptInChat = function (text) {
      prevUse(text);
      closePromptStudio();
    };
  }

  // Override top-bar entry point
  global.toggleHelpModal = togglePromptStudio;
  global.openPromptStudio = openPromptStudio;
  global.closePromptStudio = closePromptStudio;
  global.togglePromptStudio = togglePromptStudio;

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePromptStudio();
    if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
      e.preventDefault();
      togglePromptStudio();
    }
  });
})(window);

/* v2.8.6 full-page drawer class */
(function(){
  function mark(){
    var el = document.getElementById("promptStudioDrawer") || document.querySelector(".ps-drawer");
    if (el) el.classList.add("prompt-studio-drawer");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mark);
  else mark();
})();

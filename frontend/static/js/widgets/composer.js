/**
 * Widget: Composer — elevated input shell styling hooks
 */
(function (global) {
  function mount(el) {
    if (!el || el.dataset.vaMounted === 'true') return;
    el.dataset.vaMounted = 'true';
    el.classList.add('widget-composer');
    el.dataset.widget = 'composer';
    const ta = el.querySelector('textarea, #messageInput, #userInput');
    if (ta) {
      ta.setAttribute('rows', ta.getAttribute('rows') || '1');
      const autoGrow = () => {
        ta.style.height = 'auto';
        ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
      };
      ta.addEventListener('input', autoGrow);
    }
  }

  global.VAWidgets = global.VAWidgets || {};
  global.VAWidgets.Composer = { mount };
})(typeof window !== 'undefined' ? window : globalThis);

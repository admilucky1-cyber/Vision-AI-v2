/**
 * Container: ChatShell — message list + composer region
 */
(function (global) {
  function mount(el) {
    if (!el || el.dataset.vaMounted === 'true') return;
    el.dataset.vaMounted = 'true';
    el.classList.add('container-chat-shell');
    el.dataset.container = 'chat-shell';
    const list = el.querySelector('#chatBox, [data-role="message-list"]');
    if (list) {
      list.setAttribute('role', 'log');
      list.setAttribute('aria-live', 'polite');
      list.setAttribute('aria-relevant', 'additions');
    }
  }

  global.VAContainers = global.VAContainers || {};
  global.VAContainers.ChatShell = { mount };
})(typeof window !== 'undefined' ? window : globalThis);

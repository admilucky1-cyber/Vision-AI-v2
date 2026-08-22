/**
 * Widget: MessageBubble helpers
 */
(function (global) {
  function enhance(node, { role } = {}) {
    if (!node) return node;
    node.classList.add('widget-message-bubble');
    if (role) node.classList.add('widget-message-bubble--' + role);
    return node;
  }

  global.VAWidgets = global.VAWidgets || {};
  global.VAWidgets.MessageBubble = { enhance };
})(typeof window !== 'undefined' ? window : globalThis);

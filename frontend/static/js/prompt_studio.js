/**
 * Vision AI — Prompt Studio marketplace drawer
 */
(function () {
  "use strict";

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function ensureDrawer() {
    var d = $("#promptStudioDrawer");
    if (d) return d;
    d = document.createElement("div");
    d.id = "promptStudioDrawer";
    d.className = "ps-drawer";
    d.setAttribute("aria-hidden", "true");
    d.innerHTML =
      '<div class="ps-backdrop" data-ps-close="1"></div>' +
      '<aside class="ps-panel glass-panel" role="dialog" aria-label="Prompt Studio">' +
      '  <header class="ps-header">' +
      '    <div><h2>Prompt Studio</h2><p class="ps-sub">Premium prompts · one tap to chat</p></div>' +
      '    <button type="button" class="ps-close" data-ps-close="1" aria-label="Close">×</button>' +
      "  </header>" +
      '  <div class="ps-search-wrap"><input type="search" id="psSearch" class="ps-search" placeholder="Search prompts…" autocomplete="off" /></div>' +
      '  <div class="ps-chips" id="psChips"></div>' +
      '  <div class="ps-featured" id="psFeatured"></div>' +
      '  <div class="ps-grid" id="psGrid"></div>' +
      "</aside>";
    document.body.appendChild(d);
    d.addEventListener("click", function (e) {
      if (e.target && e.target.getAttribute("data-ps-close")) closeDrawer();
    });
    var search = $("#psSearch", d);
    if (search) search.addEventListener("input", function () { render(search.value || ""); });
    return d;
  }

  function library() {
    return window.PROMPT_LIBRARY || {};
  }

  function openDrawer() {
    var d = ensureDrawer();
    d.classList.add("open");
    d.setAttribute("aria-hidden", "false");
    render("");
    setTimeout(function () {
      var s = $("#psSearch", d);
      if (s) s.focus();
    }, 200);
  }

  function closeDrawer() {
    var d = $("#promptStudioDrawer");
    if (!d) return;
    d.classList.remove("open");
    d.setAttribute("aria-hidden", "true");
  }

  function usePrompt(text) {
    var ta = document.getElementById("message") || document.getElementById("chatInput");
    if (ta) {
      ta.value = text;
      ta.focus();
      ta.dispatchEvent(new Event("input", { bubbles: true }));
    }
    closeDrawer();
    if (typeof showToast === "function") showToast("Prompt loaded — edit then Send", "success", 2200);
  }

  function render(filter) {
    var d = ensureDrawer();
    var chips = $("#psChips", d);
    var grid = $("#psGrid", d);
    var featured = $("#psFeatured", d);
    var lib = library();
    var q = (filter || "").toLowerCase().trim();
    var cats = Object.keys(lib);
    chips.innerHTML = '<button type="button" class="ps-chip active" data-cat="*">All</button>';
    cats.forEach(function (c) {
      if (c === "Featured") return;
      var meta = lib[c] || {};
      chips.innerHTML +=
        '<button type="button" class="ps-chip" data-cat="' +
        c.replace(/"/g, "") +
        '">' +
        (meta.icon || "") +
        " " +
        c +
        "</button>";
    });
    $all(".ps-chip", chips).forEach(function (btn) {
      btn.onclick = function () {
        $all(".ps-chip", chips).forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        renderList(btn.getAttribute("data-cat"), q);
      };
    });

    // Featured
    featured.innerHTML = "";
    var feat = (lib.Featured && lib.Featured.prompts) || [];
    feat.forEach(function (p) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "ps-card ps-card-featured";
      card.innerHTML =
        '<div class="ps-card-top"><span class="ps-badge">Featured</span><strong>' +
        (p.title || "Prompt") +
        "</strong></div><p>" +
        (p.t || "").slice(0, 140) +
        (p.t && p.t.length > 140 ? "…" : "") +
        "</p>";
      card.onclick = function () { usePrompt(p.t); };
      featured.appendChild(card);
    });

    renderList("*", q);

    function renderList(cat, query) {
      grid.innerHTML = "";
      Object.keys(lib).forEach(function (c) {
        if (c === "Featured") return;
        if (cat && cat !== "*" && c !== cat) return;
        (lib[c].prompts || []).forEach(function (p) {
          var blob = ((p.title || "") + " " + (p.t || "") + " " + c).toLowerCase();
          if (query && blob.indexOf(query) === -1) return;
          var card = document.createElement("button");
          card.type = "button";
          card.className = "ps-card";
          card.innerHTML =
            '<div class="ps-card-top"><span>' +
            (lib[c].icon || "✦") +
            "</span><strong>" +
            (p.title || "Prompt") +
            '</strong></div><p class="ps-cat">' +
            c +
            "</p><p>" +
            (p.t || "").slice(0, 110) +
            (p.t && p.t.length > 110 ? "…" : "") +
            "</p>";
          card.onclick = function () { usePrompt(p.t); };
          grid.appendChild(card);
        });
      });
      if (!grid.children.length) {
        grid.innerHTML = '<p class="ps-empty">No prompts match your search.</p>';
      }
    }
  }

  window.openPromptStudio = openDrawer;
  window.closePromptStudio = closeDrawer;
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDrawer();
  });
})();

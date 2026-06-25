/**
 * Sidebar-Toggles (linke Nav, rechtes TOC): Zustand pro Session merken und
 * offene Overlays bei Klick daneben schliessen. Sichtbarkeit selbst steuert
 * weiterhin CSS (extra.css, html:has(#rt-*-toggle:checked)).
 */
(function () {
  var TOGGLES = [
    { id: "rt-nav-toggle", sidebar: ".md-sidebar--primary" },
    { id: "rt-toc-toggle", sidebar: ".md-sidebar--secondary" }
  ];

  function read(id) {
    try { return sessionStorage.getItem("rt:" + id); } catch (e) { return null; }
  }
  function save(id) {
    var cb = document.getElementById(id);
    if (!cb) return;
    try { sessionStorage.setItem("rt:" + id, cb.checked ? "1" : "0"); } catch (e) {}
  }

  function apply() {
    TOGGLES.forEach(function (t) {
      var cb = document.getElementById(t.id);
      if (!cb) return;
      var v = read(t.id);
      if (v === "1") cb.checked = true;
      else if (v === "0") cb.checked = false;
    });
  }

  document.addEventListener("change", function (ev) {
    var t = ev.target;
    if (t && (t.id === "rt-nav-toggle" || t.id === "rt-toc-toggle")) save(t.id);
  });

  document.addEventListener("click", function (ev) {
    TOGGLES.forEach(function (t) {
      var cb = document.getElementById(t.id);
      if (!cb || !cb.checked) return;
      var sb = document.querySelector(t.sidebar);
      if (!sb || getComputedStyle(sb).position !== "absolute") return;
      if (sb.contains(ev.target) || ev.target.closest(".rt-toolbar")) return;
      cb.checked = false;
      save(t.id);
    });
  });

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(apply);
  } else {
    apply();
    document.addEventListener("DOMContentLoaded", apply);
  }
})();

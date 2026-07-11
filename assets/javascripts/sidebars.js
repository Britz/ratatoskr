/**
 * Sidebar-Toggles (linke Nav, rechtes TOC): Zustand pro Session merken und
 * offene Overlays bei Klick daneben schliessen. Sichtbarkeit selbst steuert
 * weiterhin CSS (extra.css, html:has(#rt-*-toggle:checked)).
 *
 * Schliess-Regeln der Hover-Panels:
 *  - "Innen" = beide Sidebars + Knöpfe: geschlossen wird nur bei Klick auf
 *    die Seite selbst; das Bedienen des einen Panels lässt das andere offen
 *    (identisch zum Spalten-Modus, wo beide koexistieren).
 *  - AUSNAHME: würden sich die beiden offenen Panels überlappen (Bildschirm
 *    schmaler als zwei Panel-Breiten), schliessen sie sich gegenseitig aus —
 *    beim Öffnen gewinnt das zuletzt geöffnete, bei Load/Resize die Nav
 *    (links hat Vorrang). Geprüft wird geometrisch, keine Breiten-Konstante.
 *  - RESIZE über eine Semantik-Grenze (Nav 60em, TOC 76.25em — dort kehrt
 *    "checked" seine Bedeutung um: ausblenden <-> einblenden): Haken zurück
 *    auf Default der neuen Breite. Eine eingeklappte Spalte geht beim
 *    Verkleinern also NICHT als Hover-Panel auf; umgekehrt klappt ein offenes
 *    Hover-Panel beim Vergrößern zur (Default-)Spalte aus.
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
    enforceExclusion("rt-toc-toggle");
  }

  /* Unterhalb der Spalten-Grenze schweben die Panels über dem Text
     (gleiche Grenze wie in extra.css) */
  var HOVER_MQ = window.matchMedia("(max-width: 59.984375em)");

  /* Offenes Hover-Panel (sichtbar im Hover-Regime), sonst null */
  function hoverPanel(sel) {
    var sb = document.querySelector(sel);
    if (!sb || !HOVER_MQ.matches) return null;
    return getComputedStyle(sb).display !== "none" ? sb : null;
  }

  function panelsOverlap() {
    var nav = hoverPanel(".md-sidebar--primary");
    var toc = hoverPanel(".md-sidebar--secondary");
    return !!(nav && toc &&
      nav.getBoundingClientRect().right > toc.getBoundingClientRect().left);
  }

  function closeToggle(id) {
    var cb = document.getElementById(id);
    if (cb && cb.checked) { cb.checked = false; save(id); }
  }

  /* Ausnahme: überlappen beide offenen Panels, muss der Verlierer schliessen */
  function enforceExclusion(loserId) {
    if (panelsOverlap()) closeToggle(loserId);
  }

  document.addEventListener("change", function (ev) {
    var t = ev.target;
    if (!t || (t.id !== "rt-nav-toggle" && t.id !== "rt-toc-toggle")) return;
    save(t.id);
    if (t.checked) enforceExclusion(t.id === "rt-nav-toggle" ? "rt-toc-toggle" : "rt-nav-toggle");
  });

  document.addEventListener("click", function (ev) {
    if (!HOVER_MQ.matches) return;               /* nur Hover-Panels schliessen bei Klick daneben */
    if (ev.target.closest && ev.target.closest(".md-sidebar, .rt-toolbar")) return;
    TOGGLES.forEach(function (t) {
      var cb = document.getElementById(t.id);
      if (!cb || !cb.checked) return;
      if (!hoverPanel(t.sidebar)) return;
      cb.checked = false;
      save(t.id);
    });
  });

  window.addEventListener("resize", function () { enforceExclusion("rt-toc-toggle"); });

  /* Resize über die Semantik-Grenze eines Toggles -> Default (unchecked).
     Grenzen wie in extra.css: Nav 60em, TOC 76.25em (em = 16px, wie Media-Query). */
  [
    { id: "rt-nav-toggle", mq: window.matchMedia("(min-width: 60em)") },
    { id: "rt-toc-toggle", mq: window.matchMedia("(min-width: 76.25em)") }
  ].forEach(function (t) {
    t.mq.addEventListener("change", function () { closeToggle(t.id); });
  });

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(apply);
  } else {
    apply();
    document.addEventListener("DOMContentLoaded", apply);
  }
})();

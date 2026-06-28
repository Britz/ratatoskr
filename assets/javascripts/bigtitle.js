/**
 * Skaliert big-Callout-Ueberschriften (.admonition.big > .admonition-title) so,
 * dass die breiteste Zeile die verfuegbare Content-Breite ausfuellt:
 * font-size = Breite / Breite-der-breitesten-Zeile * REF. Gemessen wird mit
 * white-space:nowrap, daher zaehlen nur vorhandene <br> als Umbruch — ohne <br>
 * ist die breiteste Zeile der ganze Text (steht auf einer Zeile, wird bei
 * langem Text klein), mit <br> ist es das laengste Segment (Text wird groesser).
 * Pro Seite real gemessen, daher seitenunabhaengig. CSS ist nur JS-loser Fallback.
 */
(function () {
  var REF = 100, SAFETY = 0.992;

  function fit(el) {
    var parent = el.parentElement;
    if (!parent) return;
    var cs = getComputedStyle(parent);
    var avail = parent.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    if (avail <= 0) return;
    el.style.whiteSpace = "nowrap";
    el.style.fontSize = REF + "px";
    var widest = el.scrollWidth;
    if (!widest) return;
    el.style.fontSize = (REF * avail / widest * SAFETY) + "px";
  }

  function fitAll() {
    document.querySelectorAll(".admonition.big > .admonition-title").forEach(fit);
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(fitAll);
  } else {
    document.addEventListener("DOMContentLoaded", fitAll);
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitAll);

  var t;
  window.addEventListener("resize", function () {
    clearTimeout(t);
    t = setTimeout(fitAll, 100);
  });
})();

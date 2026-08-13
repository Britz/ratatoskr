/**
 * Karten-Touch-Steuerung (Zwei-Tap) für die interaktiven Inline-SVG-Karten.
 *
 * Desktop nutzt weiterhin CSS-:hover; die Navigation der als Gruppen eingebetteten
 * SVG-Links übernimmt dieses Skript auf allen Geräten.
 *
 * Modell (Zwei-Tap):
 *  - Erster Tap auf einen Marker enthüllt ihn (Label bzw. Satelliten-Stationen),
 *    OHNE dem Link zu folgen — dazu wird eine `.is-active`-Klasse gesetzt, die im
 *    jeweiligen SVG-Stylesheet dieselbe Aktiv-Deklaration bekommt wie `:hover`.
 *  - Zweiter Tap auf denselben (nun enthüllten) Marker/Link folgt dem Link.
 *  - Tap auf leere Kartenfläche oder außerhalb der Karte schließt (entfernt `.is-active`).
 *
 * Aktiv-Ziel:
 *  - Fundorte/Museen (`.fundorte-karte`): der statische Marker `#mk{i}` ist ein Link;
 *    aktiviert wird die im Ruhezustand unsichtbare Deck-Gruppe `#tp{i}` (Marker-Kopie
 *    + Label), die den `:hover`-Zustand nachbildet und über allen Punkten liegt.
 *  - Rundgang (`.rundgang-karte`): der Hub `.mk-grp` selbst wird aktiviert; seine
 *    Satelliten klappen per gespiegelter `.is-active`-Regel auf.
 */
(function () {
  var SEL = "svg.fundorte-karte, svg.rundgang-karte";

  function navigate(el) {
    var href = el && el.getAttribute("data-href");
    if (href) window.location.assign(href);
  }

  function clear(svg) {
    var on = svg.querySelectorAll(".is-active");
    for (var i = 0; i < on.length; i++) on[i].classList.remove("is-active");
  }

  function onCardClick(e) {
    var svg = e.currentTarget;
    var link = e.target.closest ? e.target.closest("[data-href]") : null;

    if (!window.matchMedia || !window.matchMedia("(hover: none)").matches) {
      navigate(link);
      return;
    }

    // Zweiter Tap: liegt der Klick in einem bereits aktiven Element, folgt der Link.
    var active = svg.querySelectorAll(".is-active");
    for (var i = 0; i < active.length; i++) {
      if (active[i].contains(e.target)) {
        navigate(link || active[i]);
        return;
      }
    }

    var grp = e.target.closest ? e.target.closest(".mk-grp") : null;
    clear(svg);
    if (!grp) return;                 // Tap daneben -> nur geschlossen

    e.preventDefault();               // erster Tap enthüllt, statt dem Link zu folgen
    var target = grp;                 // Rundgang: der Hub selbst
    if (svg.classList.contains("fundorte-karte") && /^mk\d+$/.test(grp.id)) {
      target = svg.querySelector("#tp" + grp.id.slice(2)) || grp;
    }
    target.classList.add("is-active");
  }

  function onKeyDown(e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var link = e.target.closest ? e.target.closest("[data-href]") : null;
    if (!link) return;
    e.preventDefault();
    navigate(link);
  }

  function init() {
    var cards = document.querySelectorAll(SEL);
    for (var i = 0; i < cards.length; i++) {
      cards[i].addEventListener("click", onCardClick);
      cards[i].addEventListener("keydown", onKeyDown);
    }
  }

  // Klick außerhalb aller Karten schließt offene Marker.
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest(SEL)) return;
    var cards = document.querySelectorAll(SEL);
    for (var i = 0; i < cards.length; i++) clear(cards[i]);
  });

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

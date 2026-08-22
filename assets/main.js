/* Nacréa by Cathy — comportements globaux (charte UI Phase 2 : calme et discret) */
(function () {
  "use strict";

  // Header : transparent en haut de page, ivoire translucide + blur après scroll
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("scrolled", window.scrollY > 8);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // Fiche produit : barre d'achat mobile quand le bouton principal sort de l'écran
  var stickyBuy = document.querySelector(".sticky-buy");
  var ctas = document.querySelector(".achat-ctas");
  if (stickyBuy && ctas && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      var en = entries[0];
      stickyBuy.classList.toggle("on", !en.isIntersecting && en.boundingClientRect.top < 0);
    }, { threshold: 0 }).observe(ctas);
  }

  // Photos lazy : arrivée en fondu sur le fond nude du placeholder (pas de blanc brutal)
  document.querySelectorAll(".carte-img img").forEach(function (img) {
    if (img.complete) return;
    img.classList.add("img-chargement");
    img.addEventListener("load", function () { img.classList.remove("img-chargement"); }, { once: true });
    img.addEventListener("error", function () { img.classList.remove("img-chargement"); }, { once: true });
  });

  // Fade-up des sections au scroll (désactivé si l'utilisateur préfère réduire les animations).
  // Le hero est exclu : il a sa propre entrée orchestrée au chargement (Phase 11 §4-5).
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches && "IntersectionObserver" in window) {
    var sections = document.querySelectorAll("main > section:not(.hero)");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("on");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -6% 0px" });
    sections.forEach(function (el) {
      el.classList.add("js-reveal");
      io.observe(el);
    });
  }
})();

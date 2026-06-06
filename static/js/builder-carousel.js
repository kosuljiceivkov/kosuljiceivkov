/**
 * Page builder karusel — autoplay, strelice, tačkice, touch, performanse.
 */
(function () {
  "use strict";

  var initialized = new WeakSet();

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function initCarousel(root) {
    if (initialized.has(root)) return;
    initialized.add(root);

    var slides = Array.prototype.slice.call(root.querySelectorAll("[data-slide]"));
    if (!slides.length) return;

    var index = 0;
    var autoplayEnabled = root.dataset.autoplay === "true" && !prefersReducedMotion();
    var intervalMs = (parseInt(root.dataset.interval, 10) || 5) * 1000;
    var speedMs = parseInt(root.dataset.speed, 10) || 500;
    var showArrows = root.dataset.arrows !== "false";
    var showDots = root.dataset.dots !== "false";
    var timer = null;
    var touchStartX = 0;
    var touchDeltaX = 0;

    root.style.setProperty("--carousel-speed", speedMs + "ms");

    var dots = showDots
      ? Array.prototype.slice.call(root.querySelectorAll("[data-carousel-dot]"))
      : [];
    var prevBtn = showArrows ? root.querySelector("[data-carousel-prev]") : null;
    var nextBtn = showArrows ? root.querySelector("[data-carousel-next]") : null;

    function setActiveDot(nextIndex) {
      dots.forEach(function (dot, dotIndex) {
        var active = dotIndex === nextIndex;
        dot.classList.toggle("is-active", active);
        dot.setAttribute("aria-selected", active ? "true" : "false");
      });
    }

    function show(nextIndex) {
      if (slides.length <= 1) return;

      slides[index].classList.remove("is-active");
      slides[index].setAttribute("aria-hidden", "true");

      index = (nextIndex + slides.length) % slides.length;

      slides[index].classList.add("is-active");
      slides[index].setAttribute("aria-hidden", "false");
      setActiveDot(index);
    }

    function next() {
      show(index + 1);
    }

    function prev() {
      show(index - 1);
    }

    function stopAutoplay() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    function startAutoplay() {
      stopAutoplay();
      if (autoplayEnabled && slides.length > 1) {
        timer = window.setInterval(next, intervalMs);
      }
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        prev();
        startAutoplay();
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        next();
        startAutoplay();
      });
    }

    dots.forEach(function (dot) {
      dot.addEventListener("click", function () {
        var target = parseInt(dot.getAttribute("data-carousel-dot"), 10);
        if (!Number.isNaN(target)) {
          show(target);
          startAutoplay();
        }
      });
    });

    root.addEventListener("mouseenter", stopAutoplay);
    root.addEventListener("mouseleave", startAutoplay);
    root.addEventListener("focusin", stopAutoplay);
    root.addEventListener("focusout", startAutoplay);

    root.addEventListener(
      "touchstart",
      function (event) {
        touchStartX = event.changedTouches[0].screenX;
        touchDeltaX = 0;
        stopAutoplay();
      },
      { passive: true }
    );

    root.addEventListener(
      "touchmove",
      function (event) {
        touchDeltaX = event.changedTouches[0].screenX - touchStartX;
      },
      { passive: true }
    );

    root.addEventListener(
      "touchend",
      function () {
        if (Math.abs(touchDeltaX) > 40) {
          if (touchDeltaX < 0) next();
          else prev();
        }
        startAutoplay();
      },
      { passive: true }
    );

    document.addEventListener("visibilitychange", function () {
      if (document.hidden) stopAutoplay();
      else startAutoplay();
    });

    if (slides.length > 1) {
      startAutoplay();
    } else {
      if (prevBtn) prevBtn.hidden = true;
      if (nextBtn) nextBtn.hidden = true;
      dots.forEach(function (dot) {
        dot.hidden = true;
      });
    }
  }

  function boot() {
    document.querySelectorAll("[data-builder-carousel]").forEach(initCarousel);
  }

  function observe() {
    if (!("IntersectionObserver" in window)) {
      boot();
      return;
    }

    var observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            initCarousel(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "120px 0px" }
    );

    document.querySelectorAll("[data-builder-carousel]").forEach(function (el) {
      observer.observe(el);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", observe);
  } else {
    observe();
  }
})();

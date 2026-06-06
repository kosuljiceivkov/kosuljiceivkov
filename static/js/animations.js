/**
 * Animacije — Intersection Observer (jednom, bez teških biblioteka)
 */
(function () {
    "use strict";

    var SELECTOR_SINGLE = "[data-animate], [data-animate-child]";
    var SELECTOR_STAGGER = "[data-animate-stagger]";
    var CLASS_ANIMATED = "is-animated";
    var STAGGER_MAX = 12;

    function prefersReducedMotion() {
        return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    function revealElement(el) {
        el.classList.add(CLASS_ANIMATED);
    }

    function setupStaggerChildren(container) {
        var children = Array.prototype.slice.call(container.children);
        var limit = Math.min(children.length, STAGGER_MAX);
        for (var i = 0; i < limit; i++) {
            children[i].style.setProperty("--stagger-index", String(i));
        }
    }

    function revealStagger(container) {
        setupStaggerChildren(container);
        container.classList.add(CLASS_ANIMATED);
    }

    function isInViewport(el) {
        var rect = el.getBoundingClientRect();
        return rect.top < window.innerHeight && rect.bottom > 0;
    }

    function revealInViewport() {
        document.querySelectorAll(SELECTOR_SINGLE).forEach(function (el) {
            if (el.closest(SELECTOR_STAGGER) && el.hasAttribute("data-animate-child")) {
                return;
            }
            if (isInViewport(el)) {
                revealElement(el);
            }
        });
        document.querySelectorAll(SELECTOR_STAGGER).forEach(function (el) {
            setupStaggerChildren(el);
            if (isInViewport(el)) {
                revealStagger(el);
            }
        });
    }

    function initAnimations() {
        if (prefersReducedMotion()) {
            document.documentElement.classList.add("js-animate");
            document.querySelectorAll(SELECTOR_SINGLE + ", " + SELECTOR_STAGGER).forEach(function (el) {
                el.classList.add(CLASS_ANIMATED);
            });
            document.querySelectorAll(SELECTOR_STAGGER).forEach(revealStagger);
            return;
        }

        revealInViewport();
        document.documentElement.classList.add("js-animate");

        if (!("IntersectionObserver" in window)) {
            document.querySelectorAll(SELECTOR_SINGLE).forEach(revealElement);
            document.querySelectorAll(SELECTOR_STAGGER).forEach(revealStagger);
            return;
        }

        var observer = new IntersectionObserver(
            function (entries, obs) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) {
                        return;
                    }

                    var target = entry.target;

                    if (target.matches(SELECTOR_STAGGER)) {
                        revealStagger(target);
                    } else {
                        revealElement(target);
                    }

                    obs.unobserve(target);
                });
            },
            {
                root: null,
                rootMargin: "0px 0px -5% 0px",
                threshold: 0.08,
            }
        );

        document.querySelectorAll(SELECTOR_STAGGER).forEach(function (el) {
            if (!el.classList.contains(CLASS_ANIMATED)) {
                setupStaggerChildren(el);
                observer.observe(el);
            }
        });

        document.querySelectorAll(SELECTOR_SINGLE).forEach(function (el) {
            if (el.closest(SELECTOR_STAGGER) && el.hasAttribute("data-animate-child")) {
                return;
            }
            if (!el.classList.contains(CLASS_ANIMATED)) {
                observer.observe(el);
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAnimations);
    } else {
        initAnimations();
    }
})();

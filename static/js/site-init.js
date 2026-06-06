/**
 * Uslovno učitavanje JS — karuseli i galerija lazy; animacije odmah.
 */
(function () {
    "use strict";

    var script = document.currentScript;
    var base = (script && script.getAttribute("data-static-base")) || "/static/js/";

    function loadScript(src) {
        return new Promise(function (resolve, reject) {
            var el = document.createElement("script");
            el.src = src;
            el.defer = true;
            el.onload = function () {
                resolve();
            };
            el.onerror = reject;
            document.body.appendChild(el);
        });
    }

    function whenVisible(selector, callback) {
        var node = document.querySelector(selector);
        if (!node) {
            return;
        }
        if (typeof IntersectionObserver === "undefined") {
            callback();
            return;
        }
        var observer = new IntersectionObserver(
            function (entries) {
                if (entries[0].isIntersecting) {
                    observer.disconnect();
                    callback();
                }
            },
            { rootMargin: "120px" }
        );
        observer.observe(node);
    }

    function loadDeferredScripts() {
        var hasShowcase = document.querySelector("[data-showcase-carousel]");
        var hasGallery = document.querySelector("[data-services-gallery]");
        var chain = Promise.resolve();

        if (hasShowcase) {
            chain = new Promise(function (resolve) {
                whenVisible("[data-showcase-carousel]", function () {
                    loadScript(base + "carousel-core.js")
                        .then(function () {
                            return loadScript(base + "project-showcase-carousel.js");
                        })
                        .then(resolve)
                        .catch(resolve);
                });
            });
        }

        if (hasGallery) {
            chain = chain.then(function () {
                return new Promise(function (resolve) {
                    whenVisible("[data-services-gallery]", function () {
                        loadScript(base + "gallery-lightbox.js").then(resolve).catch(resolve);
                    });
                });
            });
        }

        chain.catch(function () {
            /* tihi fallback */
        });
    }

    function boot() {
        var hasAnimate =
            document.querySelector("[data-animate]") ||
            document.querySelector("[data-animate-stagger]");

        if (hasAnimate) {
            loadScript(base + "animations.js?v=2").catch(function () {
                /* sadržaj ostaje vidljiv bez js-animate klase */
            });
        }

        if (typeof requestIdleCallback === "function") {
            requestIdleCallback(loadDeferredScripts, { timeout: 3000 });
        } else {
            setTimeout(loadDeferredScripts, 1);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();

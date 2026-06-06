/**
 * Galerija usluga — lightbox, touch, tastatura
 */
(function () {
    "use strict";

    var SWIPE_THRESHOLD = 48;
    var VELOCITY_THRESHOLD = 0.35;

    function prefersReducedMotion() {
        return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    function GalleryLightbox(root) {
        this.root = root;
        this.overlay = root.querySelector("[data-gallery-lightbox]");
        this.dialog = root.querySelector("[data-gallery-dialog]");
        this.stage = root.querySelector("[data-gallery-stage]");
        this.img = root.querySelector("[data-gallery-image]");
        this.captionEl = root.querySelector("[data-gallery-caption]");
        this.counterEl = root.querySelector("[data-gallery-counter]");
        this.triggers = Array.prototype.slice.call(
            root.querySelectorAll("[data-gallery-trigger]")
        );
        this.index = 0;
        this.length = this.triggers.length;
        this.lastFocus = null;
        this.reducedMotion = prefersReducedMotion();

        if (!this.overlay || this.length < 1) {
            return;
        }

        this.bind();
    }

    GalleryLightbox.prototype.bind = function () {
        var self = this;

        this.triggers.forEach(function (btn, i) {
            btn.addEventListener("click", function () {
                self.open(i);
            });
        });

        var backdrop = this.overlay.querySelector(".gallery-lightbox__backdrop");
        if (backdrop) {
            backdrop.addEventListener("click", function () {
                self.close();
            });
        }

        this.overlay.querySelectorAll("[data-gallery-close]").forEach(function (el) {
            el.addEventListener("click", function () {
                self.close();
            });
        });

        var prev = this.overlay.querySelector("[data-gallery-prev]");
        var next = this.overlay.querySelector("[data-gallery-next]");
        if (prev) {
            prev.addEventListener("click", function (e) {
                e.stopPropagation();
                self.go(-1);
            });
        }
        if (next) {
            next.addEventListener("click", function (e) {
                e.stopPropagation();
                self.go(1);
            });
        }

        document.addEventListener("keydown", function (e) {
            if (!self.isOpen()) {
                return;
            }
            if (e.key === "Escape") {
                e.preventDefault();
                self.close();
            } else if (e.key === "ArrowLeft") {
                e.preventDefault();
                self.go(-1);
            } else if (e.key === "ArrowRight") {
                e.preventDefault();
                self.go(1);
            }
        });

        if (this.stage && !this.reducedMotion) {
            this.bindTouch();
        }
    };

    GalleryLightbox.prototype.isOpen = function () {
        return this.overlay && !this.overlay.hidden;
    };

    GalleryLightbox.prototype.open = function (index) {
        this.lastFocus = document.activeElement;
        this.index = index;
        this.overlay.hidden = false;
        this.overlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("gallery-lightbox-open");
        this.showSlide();
        var closeBtn = this.overlay.querySelector(".gallery-lightbox__close");
        if (closeBtn) {
            closeBtn.focus();
        }
    };

    GalleryLightbox.prototype.close = function () {
        this.overlay.hidden = true;
        this.overlay.setAttribute("aria-hidden", "true");
        document.body.classList.remove("gallery-lightbox-open");
        if (this.lastFocus && this.lastFocus.focus) {
            this.lastFocus.focus();
        }
    };

    GalleryLightbox.prototype.go = function (delta) {
        this.index = (this.index + delta + this.length) % this.length;
        this.showSlide();
    };

    GalleryLightbox.prototype.showSlide = function () {
        var btn = this.triggers[this.index];
        if (!btn || !this.img) {
            return;
        }

        var src = btn.getAttribute("data-gallery-src");
        var alt = btn.getAttribute("data-gallery-alt") || "";
        var caption = btn.getAttribute("data-gallery-caption") || "";
        var w = parseInt(btn.getAttribute("data-gallery-width"), 10);
        var h = parseInt(btn.getAttribute("data-gallery-height"), 10);

        this.img.alt = alt;
        if (w > 0 && h > 0) {
            this.img.width = w;
            this.img.height = h;
            this.stage.style.aspectRatio = w + " / " + h;
        } else {
            this.img.removeAttribute("width");
            this.img.removeAttribute("height");
            this.stage.style.removeProperty("aspect-ratio");
        }

        this.img.classList.remove("is-loaded");
        this.img.src = src;

        if (this.captionEl) {
            if (caption) {
                this.captionEl.textContent = caption;
                this.captionEl.hidden = false;
            } else {
                this.captionEl.textContent = "";
                this.captionEl.hidden = true;
            }
        }

        if (this.counterEl && this.length > 1) {
            this.counterEl.textContent =
                String(this.index + 1) + " / " + String(this.length);
        } else if (this.counterEl) {
            this.counterEl.textContent = "";
        }

        var self = this;
        function onLoad() {
            self.img.classList.add("is-loaded");
        }
        if (this.img.complete) {
            onLoad();
        } else {
            this.img.addEventListener("load", onLoad, { once: true });
        }
    };

    GalleryLightbox.prototype.bindTouch = function () {
        var self = this;
        var startX = 0;
        var startY = 0;
        var lastX = 0;
        var lastT = 0;
        var deltaX = 0;
        var velocityX = 0;
        var axisLock = null;

        this.stage.addEventListener(
            "touchstart",
            function (e) {
                var t = e.changedTouches[0];
                startX = t.screenX;
                startY = t.screenY;
                lastX = startX;
                lastT = e.timeStamp;
                deltaX = 0;
                velocityX = 0;
                axisLock = null;
            },
            { passive: true }
        );

        this.stage.addEventListener(
            "touchmove",
            function (e) {
                var t = e.changedTouches[0];
                var dx = t.screenX - startX;
                var dy = t.screenY - startY;
                if (axisLock === null && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
                    axisLock = Math.abs(dx) > Math.abs(dy) * 1.15 ? "x" : "y";
                }
                if (axisLock !== "x") {
                    return;
                }
                deltaX = dx;
                var dt = e.timeStamp - lastT;
                if (dt > 0) {
                    velocityX = (t.screenX - lastX) / dt;
                }
                lastX = t.screenX;
                lastT = e.timeStamp;
            },
            { passive: true }
        );

        this.stage.addEventListener(
            "touchend",
            function () {
                if (axisLock !== "x") {
                    return;
                }
                if (
                    deltaX < -SWIPE_THRESHOLD ||
                    velocityX < -VELOCITY_THRESHOLD
                ) {
                    self.go(1);
                } else if (
                    deltaX > SWIPE_THRESHOLD ||
                    velocityX > VELOCITY_THRESHOLD
                ) {
                    self.go(-1);
                }
                axisLock = null;
            },
            { passive: true }
        );
    };

    function initAll() {
        document.querySelectorAll("[data-services-gallery], [data-lb-gallery]").forEach(function (root) {
            if (root._galleryInit) {
                return;
            }
            root._galleryInit = true;
            new GalleryLightbox(root);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAll);
    } else {
        initAll();
    }
})();

/**
 * Showcase karusel — adaptivna visina, fade, srcset, touch (CarouselCore)
 */
(function () {
    "use strict";

    var Core = window.CarouselCore;
    var SELECTOR = "[data-showcase-carousel]";
    var IMG = "[data-carousel-img]";
    var DEFAULT_INTERVAL = 6000;

    function ShowcaseCarousel(root) {
        this.root = root;
        this.viewport = root.querySelector("[data-showcase-viewport]");
        this.slides = Array.prototype.slice.call(
            root.querySelectorAll("[data-showcase-slide]")
        );
        this.prevBtn = root.querySelector("[data-showcase-prev]");
        this.nextBtn = root.querySelector("[data-showcase-next]");
        this.dots = Array.prototype.slice.call(
            root.querySelectorAll("[data-showcase-dot]")
        );
        this.counter = root.querySelector("[data-showcase-counter]");
        this.progress = root.querySelector("[data-showcase-progress]");

        this.index = 0;
        this.length = this.slides.length;
        this.reducedMotion = Core.prefersReducedMotion();

        this.autoplayEnabled =
            !this.reducedMotion &&
            root.getAttribute("data-autoplay") !== "false" &&
            this.length > 1;
        this.interval = parseInt(
            root.getAttribute("data-interval") || String(DEFAULT_INTERVAL),
            10
        );

        var self = this;
        this.height = Core.createHeightManager({
            root: root,
            viewport: this.viewport,
            getSlide: function () {
                return self.slides[self.index];
            },
            imgSelector: IMG,
            metaSelector: ".showcase-carousel__caption-wrap",
            minHeight: 140,
            maxHeightRatio: 0.65,
            reducedMotion: this.reducedMotion,
        });

        if (this.reducedMotion) {
            root.classList.add("is-reduced-motion");
        }

        this.init();
    }

    ShowcaseCarousel.prototype.init = function () {
        var self = this;

        if (this.length < 1) {
            return;
        }

        var activeIndex = function () {
            return self.index;
        };

        Core.bindImages(this.slides, IMG, activeIndex, function () {
            self.height.measure(self.index);
        });

        this.height.reserveInitial(0);

        if (this.length < 2) {
            if (this.slides[0]) {
                this.slides[0].classList.add("is-active");
            }
            return;
        }

        this.root.setAttribute("role", "region");
        this.root.setAttribute("aria-roledescription", "karusel");
        this.root.style.setProperty("--showcase-interval", this.interval + "ms");

        if (this.autoplayEnabled) {
            this.root.classList.add("is-autoplay");
        }

        this.goTo(0, true);

        this.autoplay = Core.bindAutoplay({
            enabled: this.autoplayEnabled,
            interval: this.interval,
            root: this.root,
            progressEl: this.progress,
            onTick: function () {
                self.goTo(self.index + 1);
            },
        });

        if (this.prevBtn) {
            this.prevBtn.addEventListener("click", function () {
                self.goTo(self.index - 1);
                self.autoplay.restart();
            });
        }

        if (this.nextBtn) {
            this.nextBtn.addEventListener("click", function () {
                self.goTo(self.index + 1);
                self.autoplay.restart();
            });
        }

        this.dots.forEach(function (dot, i) {
            dot.addEventListener("click", function () {
                self.goTo(i);
                self.autoplay.restart();
            });
        });

        this.viewport.addEventListener("keydown", function (e) {
            if (e.key === "ArrowLeft") {
                e.preventDefault();
                self.goTo(self.index - 1);
                self.autoplay.restart();
            } else if (e.key === "ArrowRight") {
                e.preventDefault();
                self.goTo(self.index + 1);
                self.autoplay.restart();
            } else if (e.key === "Home") {
                e.preventDefault();
                self.goTo(0);
                self.autoplay.restart();
            } else if (e.key === "End") {
                e.preventDefault();
                self.goTo(self.length - 1);
                self.autoplay.restart();
            }
        });

        this.root.addEventListener("mouseenter", function () {
            self.autoplay.pause();
        });
        this.root.addEventListener("mouseleave", function () {
            self.autoplay.resume();
        });
        this.root.addEventListener("focusin", function () {
            self.autoplay.pause();
        });
        this.root.addEventListener("focusout", function (e) {
            if (!self.root.contains(e.relatedTarget)) {
                self.autoplay.resume();
            }
        });

        Core.createTouchController({
            viewport: this.viewport,
            reducedMotion: this.reducedMotion,
            onInteractionStart: function () {
                self.autoplay.pause();
            },
            onSwipeLeft: function () {
                self.goTo(self.index + 1);
                self.autoplay.restart();
            },
            onSwipeRight: function () {
                self.goTo(self.index - 1);
                self.autoplay.restart();
            },
            onDrag: function (dx) {
                self.root.classList.add("is-drag-offset");
                self.root.style.setProperty(
                    "--carousel-drag-x",
                    Math.max(-56, Math.min(56, dx * 0.4)) + "px"
                );
            },
            onDragEnd: function () {
                self.root.classList.remove("is-drag-offset");
                self.root.style.removeProperty("--carousel-drag-x");
            },
        });

        if (window.ResizeObserver && this.viewport) {
            this.resizeObserver = new ResizeObserver(function () {
                self.height.measure(self.index);
            });
            this.resizeObserver.observe(this.viewport);
        }

        if (this.autoplayEnabled) {
            this.autoplay.start();
        }

        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                self.autoplay.pause();
            } else {
                self.autoplay.resume();
            }
        });
    };

    ShowcaseCarousel.prototype.goTo = function (i, immediate) {
        this.index = ((i % this.length) + this.length) % this.length;

        this.slides.forEach(
            function (slide, j) {
                var active = j === this.index;
                slide.classList.toggle("is-active", active);
                slide.setAttribute("aria-hidden", active ? "false" : "true");
                slide.setAttribute("aria-current", active ? "true" : "false");
            }.bind(this)
        );

        this.dots.forEach(
            function (dot, j) {
                var active = j === this.index;
                dot.classList.toggle("is-active", active);
                dot.setAttribute("aria-current", active ? "true" : "false");
            }.bind(this)
        );

        if (this.counter) {
            this.counter.textContent =
                String(this.index + 1) + " / " + String(this.length);
        }

        Core.preloadAdjacent(this.slides, this.index, IMG);
        this.height.measure(this.index);

        if (!immediate && this.autoplay) {
            this.autoplay.restart();
        }
    };

    function initAll() {
        document.querySelectorAll(SELECTOR).forEach(function (root) {
            if (root._showcaseInit) {
                return;
            }
            root._showcaseInit = true;
            new ShowcaseCarousel(root);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAll);
    } else {
        initAll();
    }
})();

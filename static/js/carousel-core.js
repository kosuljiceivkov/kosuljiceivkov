/**
 * Deljeni modul za adaptivne karusele — visina, touch, slike, CLS
 */
(function (global) {
    "use strict";

    var DEFAULT_SWIPE = 44;
    var VELOCITY_THRESHOLD = 0.35;

    function prefersReducedMotion() {
        return global.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    function parseAspect(slide, img) {
        if (img && img.naturalWidth > 0 && img.naturalHeight > 0) {
            return { w: img.naturalWidth, h: img.naturalHeight };
        }
        if (img) {
            var nw = parseFloat(img.getAttribute("data-aspect-nw"));
            var nh = parseFloat(img.getAttribute("data-aspect-nh"));
            if (nw > 0 && nh > 0) {
                return { w: nw, h: nh };
            }
            var iw = parseInt(img.getAttribute("width"), 10);
            var ih = parseInt(img.getAttribute("height"), 10);
            if (iw > 0 && ih > 0) {
                return { w: iw, h: ih };
            }
        }
        if (slide) {
            var attr = slide.getAttribute("data-aspect");
            if (attr && attr.indexOf("/") > -1) {
                var parts = attr.split("/");
                var w = parseFloat(parts[0]);
                var h = parseFloat(parts[1]);
                if (w > 0 && h > 0) {
                    return { w: w, h: h };
                }
            }
        }
        return { w: 16, h: 9 };
    }

    function imageAreaHeight(containerWidth, aspect, minH, maxH) {
        var h = (containerWidth * aspect.h) / aspect.w;
        return Math.round(Math.min(maxH, Math.max(minH, h)));
    }

    function createHeightManager(config) {
        var viewport = config.viewport;
        var getSlide = config.getSlide;
        var imgSelector = config.imgSelector || "[data-carousel-img]";
        var metaSelector = config.metaSelector || null;
        var minHeight = config.minHeight || 160;
        var maxHeightRatio = config.maxHeightRatio || 0.7;
        var extraPad = config.extraPad || 0;
        var reducedMotion = config.reducedMotion;

        function metaHeight(slide) {
            if (!metaSelector || !slide) {
                return 0;
            }
            var meta = slide.querySelector(metaSelector);
            return meta ? meta.offsetHeight : 0;
        }

        function measure(index) {
            if (!viewport) {
                return;
            }
            var slide = getSlide(index);
            if (!slide) {
                return;
            }

            var width = viewport.clientWidth || viewport.offsetWidth;
            if (!width) {
                return;
            }

            var img = slide.querySelector(imgSelector);
            var aspect = parseAspect(slide, img);
            var maxH = global.innerHeight * maxHeightRatio;
            var imageH = imageAreaHeight(width, aspect, minHeight, maxH);
            var total = imageH + metaHeight(slide) + extraPad;

            viewport.style.setProperty("--carousel-stage-h", imageH + "px");
            viewport.style.height = total + "px";

            if (config.root) {
                config.root.classList.add("is-height-ready");
            }
        }

        function reserveInitial(index) {
            measure(index);
        }

        if (!reducedMotion && viewport) {
            viewport.style.transition =
                "height 420ms cubic-bezier(0.22, 1, 0.36, 1)";
        }

        return {
            measure: measure,
            reserveInitial: reserveInitial,
        };
    }

    function createTouchController(config) {
        var viewport = config.viewport;
        var onSwipeLeft = config.onSwipeLeft;
        var onSwipeRight = config.onSwipeRight;
        var onDrag = config.onDrag;
        var onDragEnd = config.onDragEnd;
        var threshold = config.threshold || DEFAULT_SWIPE;
        var reducedMotion = config.reducedMotion;

        if (!viewport || reducedMotion) {
            return { destroy: function () {} };
        }

        var startX = 0;
        var startY = 0;
        var deltaX = 0;
        var lastX = 0;
        var lastT = 0;
        var velocityX = 0;
        var dragging = false;
        var axisLock = null;

        function onStart(e) {
            var t = e.changedTouches[0];
            startX = t.screenX;
            startY = t.screenY;
            lastX = startX;
            lastT = e.timeStamp;
            deltaX = 0;
            velocityX = 0;
            dragging = true;
            axisLock = null;
            viewport.classList.add("is-dragging");
            if (config.onInteractionStart) {
                config.onInteractionStart();
            }
        }

        function onMove(e) {
            if (!dragging) {
                return;
            }
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

            if (onDrag) {
                onDrag(deltaX);
            }
        }

        function onEnd() {
            if (!dragging) {
                return;
            }
            dragging = false;
            viewport.classList.remove("is-dragging");

            if (onDragEnd) {
                onDragEnd();
            }

            if (axisLock !== "x") {
                return;
            }

            var goNext =
                deltaX < -threshold || velocityX < -VELOCITY_THRESHOLD;
            var goPrev =
                deltaX > threshold || velocityX > VELOCITY_THRESHOLD;

            if (goNext && onSwipeLeft) {
                onSwipeLeft();
            } else if (goPrev && onSwipeRight) {
                onSwipeRight();
            }

            deltaX = 0;
            velocityX = 0;
            axisLock = null;
        }

        viewport.addEventListener("touchstart", onStart, { passive: true });
        viewport.addEventListener("touchmove", onMove, { passive: true });
        viewport.addEventListener("touchend", onEnd, { passive: true });
        viewport.addEventListener("touchcancel", onEnd, { passive: true });

        return {
            destroy: function () {
                viewport.removeEventListener("touchstart", onStart);
                viewport.removeEventListener("touchmove", onMove);
                viewport.removeEventListener("touchend", onEnd);
                viewport.removeEventListener("touchcancel", onEnd);
            },
        };
    }

    function markImageLoaded(img) {
        if (!img) {
            return;
        }
        img.classList.add("is-loaded");
        img.closest("[data-carousel-stage]") &&
            img.closest("[data-carousel-stage]").classList.add("has-image");
    }

    function bindImages(slides, imgSelector, activeIndexRef, onActiveLoad) {
        slides.forEach(function (slide, i) {
            var img = slide.querySelector(imgSelector);
            if (!img) {
                return;
            }

            function handleLoad() {
                markImageLoaded(img);
                if (i === activeIndexRef()) {
                    onActiveLoad();
                }
            }

            if (img.complete && img.naturalWidth > 0) {
                handleLoad();
            } else {
                img.addEventListener("load", handleLoad, { once: true });
                img.addEventListener(
                    "error",
                    function () {
                        markImageLoaded(img);
                    },
                    { once: true }
                );
            }
        });
    }

    function preloadAdjacent(slides, index, imgSelector) {
        var next = (index + 1) % slides.length;
        var prev = (index - 1 + slides.length) % slides.length;
        [next, prev].forEach(function (i) {
            var img = slides[i] && slides[i].querySelector(imgSelector);
            if (!img || img.dataset.carouselPreloaded) {
                return;
            }
            if (img.loading === "lazy") {
                img.loading = "eager";
            }
            img.dataset.carouselPreloaded = "1";
            var preload = new Image();
            preload.decoding = "async";
            preload.src = img.currentSrc || img.src;
        });
    }

    function bindAutoplay(config) {
        var enabled = config.enabled;
        var interval = config.interval;
        var onTick = config.onTick;
        var root = config.root;
        var progressEl = config.progressEl;
        var timer = null;
        var paused = false;

        function clear() {
            if (timer) {
                global.clearInterval(timer);
                timer = null;
            }
        }

        function resetProgress() {
            if (!progressEl) {
                return;
            }
            progressEl.style.animation = "none";
            void progressEl.offsetWidth;
            progressEl.style.animation = "";
        }

        function start() {
            if (!enabled || paused) {
                return;
            }
            clear();
            timer = global.setInterval(onTick, interval);
            if (root) {
                root.classList.remove("is-paused");
            }
            resetProgress();
        }

        function pause() {
            paused = true;
            clear();
            if (root) {
                root.classList.add("is-paused");
            }
        }

        function resume() {
            paused = false;
            start();
        }

        function restart() {
            clear();
            start();
        }

        return {
            start: start,
            pause: pause,
            resume: resume,
            restart: restart,
            clear: clear,
        };
    }

    global.CarouselCore = {
        prefersReducedMotion: prefersReducedMotion,
        parseAspect: parseAspect,
        createHeightManager: createHeightManager,
        createTouchController: createTouchController,
        bindImages: bindImages,
        preloadAdjacent: preloadAdjacent,
        bindAutoplay: bindAutoplay,
        markImageLoaded: markImageLoaded,
    };
})(window);

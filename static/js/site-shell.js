/**
 * Site shell — navigacija + scroll/FAB kontrole (jedan HTTP zahtev umesto dva).
 */
(function () {
    "use strict";

    /* --- Navigacija --- */
    var MQ_DESKTOP = "(min-width: 64rem)";
    var OPEN_CLASS = "nav-open";
    var FOCUSABLE =
        'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

    var root = document.querySelector("[data-nav-root]");
    if (root) {
        var toggle = root.querySelector("[data-nav-toggle]");
        var panel = root.querySelector("[data-nav-panel]");
        var backdrop = root.querySelector("[data-nav-backdrop]");
        var closeBtn = root.querySelector("[data-nav-close]");
        var links = panel ? panel.querySelectorAll(".site-nav__link") : [];
        var main = document.getElementById("main-content");

        if (toggle && panel) {
            var isOpen = false;
            var lastFocus = null;
            var desktopMq = window.matchMedia(MQ_DESKTOP);

            function isDesktop() {
                return desktopMq.matches;
            }

            function getFocusable() {
                return Array.prototype.slice.call(panel.querySelectorAll(FOCUSABLE)).filter(function (el) {
                    return el.offsetParent !== null || el === closeBtn;
                });
            }

            function setOpen(open) {
                if (isDesktop()) {
                    open = false;
                }

                isOpen = open;
                toggle.setAttribute("aria-expanded", open ? "true" : "false");
                toggle.setAttribute("aria-label", open ? "Zatvori meni" : "Otvori meni");
                document.body.classList.toggle(OPEN_CLASS, open);

                if (backdrop) {
                    if (open) {
                        backdrop.removeAttribute("hidden");
                    } else {
                        backdrop.setAttribute("hidden", "");
                    }
                }

                panel.setAttribute("aria-hidden", open ? "false" : "true");

                if (main) {
                    main.setAttribute("aria-hidden", open ? "true" : "false");
                }

                if (open) {
                    lastFocus = document.activeElement;
                    var focusable = getFocusable();
                    var first = closeBtn || focusable[0];
                    if (first) {
                        first.focus();
                    }
                } else if (lastFocus && typeof lastFocus.focus === "function") {
                    lastFocus.focus();
                    lastFocus = null;
                }
            }

            function openMenu() {
                if (!isOpen) {
                    setOpen(true);
                }
            }

            function closeMenu() {
                if (isOpen) {
                    setOpen(false);
                }
            }

            function toggleMenu() {
                setOpen(!isOpen);
            }

            function onKeydown(e) {
                if (!isOpen) {
                    return;
                }

                if (e.key === "Escape") {
                    e.preventDefault();
                    closeMenu();
                    return;
                }

                if (e.key !== "Tab") {
                    return;
                }

                var focusable = getFocusable();
                if (focusable.length === 0) {
                    return;
                }

                var first = focusable[0];
                var last = focusable[focusable.length - 1];

                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }

            toggle.addEventListener("click", toggleMenu);

            var fabToggle = document.querySelector("[data-nav-fab]");
            if (fabToggle) {
                fabToggle.addEventListener("click", openMenu);
            }

            if (closeBtn) {
                closeBtn.addEventListener("click", closeMenu);
            }

            if (backdrop) {
                backdrop.addEventListener("click", closeMenu);
            }

            links.forEach(function (link) {
                link.addEventListener("click", closeMenu);
            });

            document.addEventListener("keydown", onKeydown);

            desktopMq.addEventListener("change", function () {
                if (isDesktop()) {
                    closeMenu();
                    panel.removeAttribute("aria-hidden");
                    if (main) {
                        main.removeAttribute("aria-hidden");
                    }
                } else if (!isOpen) {
                    panel.setAttribute("aria-hidden", "true");
                }
            });

            panel.setAttribute("role", "dialog");
            panel.setAttribute("aria-modal", "true");
            panel.setAttribute("aria-labelledby", "site-nav-title");
            panel.setAttribute("aria-hidden", "true");

            if (isDesktop()) {
                panel.removeAttribute("role");
                panel.removeAttribute("aria-modal");
                panel.removeAttribute("aria-hidden");
            }
        }
    }

    /* --- Scroll FAB --- */
    var MQ_MOBILE = "(max-width: 47.99rem)";
    var SCROLL_OFFSET = 80;
    var FOOTER_HIDE_LEAD = 24;
    var header = document.querySelector(".site-header");
    var sentinel = document.querySelector("[data-scroll-sentinel]");
    var footer = document.querySelector(".site-footer");
    var stickyTrigger = document.querySelector("[data-contact-sticky-trigger]");
    var mobileSticky = document.querySelector("[data-contact-sticky]");
    var navFab = document.querySelector("[data-scroll-nav-fab]");
    var desktopFab = document.querySelector("[data-scroll-fab]");
    var scrollTopBtn = document.querySelector("[data-scroll-top]");

    if (header) {
        var mqMobile = window.matchMedia(MQ_MOBILE);
        var skipMobileSticky = document.body.classList.contains("page-kontakt");
        var pastHeader = false;
        var pastStickyTrigger = false;
        var nearFooter = false;

        function footerHideLeadPx() {
            var measureEl = mqMobile.matches ? mobileSticky : null;
            if (!measureEl && desktopFab) {
                measureEl = desktopFab.querySelector(".scroll-fab__calls");
            }
            if (measureEl && measureEl.offsetHeight) {
                return measureEl.offsetHeight + FOOTER_HIDE_LEAD;
            }
            return 160;
        }

        function readNearFooterFromScroll() {
            if (!footer) {
                nearFooter = false;
                return;
            }
            var lead = footerHideLeadPx();
            nearFooter = footer.getBoundingClientRect().top <= window.innerHeight + lead;
        }

        function isStickyTriggerVisible() {
            if (!stickyTrigger) {
                return false;
            }
            var rect = stickyTrigger.getBoundingClientRect();
            return rect.bottom > 0 && rect.top < window.innerHeight;
        }

        function readPastStickyTriggerFromScroll() {
            if (!stickyTrigger) {
                pastStickyTrigger = document.body.classList.contains("page-home")
                    ? false
                    : pastHeader;
                return;
            }
            pastStickyTrigger = !isStickyTriggerVisible();
        }

        function shouldShowCallButtons() {
            if (skipMobileSticky && mqMobile.matches) {
                return false;
            }
            if (document.body.classList.contains("page-home")) {
                if (!stickyTrigger) {
                    return false;
                }
                return pastStickyTrigger && !nearFooter;
            }
            return pastHeader && !nearFooter;
        }

        function setMobileSticky(show) {
            if (!mobileSticky || skipMobileSticky || !mqMobile.matches) {
                if (mobileSticky) {
                    mobileSticky.classList.remove("is-visible");
                    mobileSticky.setAttribute("hidden", "");
                }
                document.body.classList.remove("has-contact-sticky");
                return;
            }
            if (show) {
                mobileSticky.removeAttribute("hidden");
                mobileSticky.classList.add("is-visible");
                document.body.classList.add("has-contact-sticky");
            } else {
                mobileSticky.classList.remove("is-visible");
                mobileSticky.setAttribute("hidden", "");
                document.body.classList.remove("has-contact-sticky");
            }
        }

        function setNavFab(show) {
            if (!navFab || !mqMobile.matches) {
                if (navFab) {
                    navFab.classList.remove("is-visible");
                    navFab.setAttribute("hidden", "");
                }
                return;
            }
            if (show) {
                navFab.removeAttribute("hidden");
                navFab.classList.add("is-visible");
            } else {
                navFab.classList.remove("is-visible");
                navFab.setAttribute("hidden", "");
            }
        }

        function setDesktopFab(showCalls, showTop) {
            if (!desktopFab || mqMobile.matches) {
                if (desktopFab) {
                    desktopFab.classList.remove("is-calls-visible", "is-top-visible");
                    desktopFab.setAttribute("hidden", "");
                    desktopFab.setAttribute("aria-hidden", "true");
                }
                return;
            }
            if (!showCalls && !showTop) {
                desktopFab.classList.remove("is-calls-visible", "is-top-visible");
                desktopFab.setAttribute("hidden", "");
                desktopFab.setAttribute("aria-hidden", "true");
                return;
            }
            desktopFab.removeAttribute("hidden");
            desktopFab.setAttribute("aria-hidden", "false");
            desktopFab.classList.toggle("is-calls-visible", showCalls);
            desktopFab.classList.toggle("is-top-visible", showTop);
        }

        function updateFabVisibility() {
            readPastStickyTriggerFromScroll();
            readNearFooterFromScroll();
            var showCalls = shouldShowCallButtons();
            setNavFab(pastHeader);
            setMobileSticky(showCalls);
            setDesktopFab(showCalls, pastHeader);
        }

        function readPastHeaderFromScroll() {
            var threshold = header.offsetHeight + SCROLL_OFFSET;
            pastHeader = window.scrollY > threshold;
            updateFabVisibility();
        }

        if (typeof IntersectionObserver !== "undefined") {
            if (sentinel) {
                var observer = new IntersectionObserver(
                    function (entries) {
                        pastHeader = !entries[0].isIntersecting;
                        updateFabVisibility();
                    },
                    { root: null, threshold: 0 }
                );
                observer.observe(sentinel);
            }

            if (footer) {
                var footerObserver = new IntersectionObserver(
                    function (entries) {
                        nearFooter = entries[0].isIntersecting;
                        updateFabVisibility();
                    },
                    {
                        root: null,
                        threshold: 0,
                        rootMargin: "0px 0px " + footerHideLeadPx() + "px 0px",
                    }
                );
                footerObserver.observe(footer);
            }

            window.addEventListener("scroll", readPastHeaderFromScroll, { passive: true });
        } else {
            window.addEventListener("scroll", readPastHeaderFromScroll, { passive: true });
        }

        mqMobile.addEventListener("change", updateFabVisibility);
        window.addEventListener("resize", updateFabVisibility, { passive: true });

        if (scrollTopBtn) {
            scrollTopBtn.addEventListener("click", function () {
                var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
                window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
            });
        }

        readPastHeaderFromScroll();
    }
})();

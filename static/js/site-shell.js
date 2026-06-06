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
    var header = document.querySelector(".site-header");
    var sentinel = document.querySelector("[data-scroll-sentinel]");
    var mobileSticky = document.querySelector("[data-contact-sticky]");
    var navFab = document.querySelector("[data-scroll-nav-fab]");
    var desktopFab = document.querySelector("[data-scroll-fab]");
    var scrollTopBtn = document.querySelector("[data-scroll-top]");

    if (header) {
        var mqMobile = window.matchMedia(MQ_MOBILE);
        var skipMobileSticky = document.body.classList.contains("page-kontakt");
        var pastHeader = false;

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

        function setDesktopFab(show) {
            if (!desktopFab || mqMobile.matches) {
                if (desktopFab) {
                    desktopFab.classList.remove("is-visible");
                    desktopFab.setAttribute("hidden", "");
                    desktopFab.setAttribute("aria-hidden", "true");
                }
                return;
            }
            if (show) {
                desktopFab.removeAttribute("hidden");
                desktopFab.setAttribute("aria-hidden", "false");
                desktopFab.classList.add("is-visible");
            } else {
                desktopFab.classList.remove("is-visible");
                desktopFab.setAttribute("hidden", "");
                desktopFab.setAttribute("aria-hidden", "true");
            }
        }

        function updateFabVisibility() {
            setNavFab(pastHeader);
            setMobileSticky(pastHeader);
            setDesktopFab(pastHeader);
        }

        function readPastHeaderFromScroll() {
            var threshold = header.offsetHeight + SCROLL_OFFSET;
            pastHeader = window.scrollY > threshold;
            updateFabVisibility();
        }

        if (sentinel && typeof IntersectionObserver !== "undefined") {
            var observer = new IntersectionObserver(
                function (entries) {
                    pastHeader = !entries[0].isIntersecting;
                    updateFabVisibility();
                },
                { root: null, threshold: 0 }
            );
            observer.observe(sentinel);
            window.addEventListener("scroll", readPastHeaderFromScroll, { passive: true });
        } else {
            window.addEventListener("scroll", readPastHeaderFromScroll, { passive: true });
        }

        mqMobile.addEventListener("change", updateFabVisibility);

        if (scrollTopBtn) {
            scrollTopBtn.addEventListener("click", function () {
                var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
                window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
            });
        }

        readPastHeaderFromScroll();
    }
})();

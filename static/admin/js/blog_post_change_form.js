/**
 * BlogPost change form — fioke, fokus, submit, prečice.
 */
(function () {
  "use strict";

  const DRAWER_TITLES = {
    details: "Detalji",
    seo: "SEO",
    publish: "Objava",
  };

  function dedupeDateTimeShortcuts(root) {
    root.querySelectorAll("input.vDateField, input.vTimeField").forEach((input) => {
      const parent = input.parentElement;
      if (!parent) {
        return;
      }
      const shortcuts = parent.querySelectorAll(":scope > .datetimeshortcuts");
      for (let index = 1; index < shortcuts.length; index += 1) {
        shortcuts[index].remove();
      }
    });
  }

  function elevateCalendarPopups() {
    document.querySelectorAll(".calendarbox, #calendarbox").forEach((node) => {
      node.style.zIndex = "10050";
    });
  }

  function initDrawers(postRoot) {
    const drawer = postRoot.querySelector("[data-blog-drawer]");
    const backdrop = postRoot.querySelector("[data-blog-drawer-backdrop]");
    const titleEl = postRoot.querySelector("[data-blog-drawer-title]");
    const panels = postRoot.querySelectorAll("[data-blog-drawer-panel]");
    const triggers = postRoot.querySelectorAll("[data-blog-drawer-trigger]");
    const closeButton = postRoot.querySelector("[data-blog-drawer-close]");

    if (!drawer) {
      return;
    }

    let activePanel = null;

    function closeDrawer() {
      drawer.hidden = true;
      drawer.setAttribute("aria-hidden", "true");
      drawer.classList.remove("blog-post-editor__drawer--wide");
      if (backdrop) {
        backdrop.hidden = true;
      }
      triggers.forEach((trigger) => trigger.classList.remove("is-active"));
      activePanel = null;
    }

    function openDrawer(name) {
      const panel = postRoot.querySelector(`[data-blog-drawer-panel="${name}"]`);
      if (!panel) {
        return;
      }

      panels.forEach((item) => {
        item.hidden = item !== panel;
      });

      if (titleEl) {
        titleEl.textContent = DRAWER_TITLES[name] || name;
      }

      triggers.forEach((trigger) => {
        trigger.classList.toggle("is-active", trigger.dataset.blogDrawerTrigger === name);
      });

      drawer.classList.toggle("blog-post-editor__drawer--wide", name === "seo");
      drawer.hidden = false;
      drawer.setAttribute("aria-hidden", "false");
      if (backdrop) {
        backdrop.hidden = false;
      }
      activePanel = name;
      dedupeDateTimeShortcuts(drawer);
      elevateCalendarPopups();
      if (name === "seo") {
        window.requestAnimationFrame(() => {
          if (window.SeoOgPreview) {
            const panel = postRoot.querySelector('[data-blog-drawer-panel="seo"]');
            window.SeoOgPreview.boot(panel || document);
          }
          document.dispatchEvent(new CustomEvent("seo-drawer-open"));
        });
      }
    }

    dedupeDateTimeShortcuts(postRoot);

    triggers.forEach((trigger) => {
      trigger.addEventListener("click", () => {
        const name = trigger.dataset.blogDrawerTrigger;
        if (activePanel === name) {
          closeDrawer();
          return;
        }
        openDrawer(name);
      });
    });

    closeButton?.addEventListener("click", closeDrawer);
    backdrop?.addEventListener("click", closeDrawer);

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !drawer.hidden) {
        closeDrawer();
      }
    });

    postRoot.blogDrawer = { open: openDrawer, close: closeDrawer };
  }

  function initShortcuts(postRoot) {
    const dialog = postRoot.querySelector("[data-blog-shortcuts-dialog]");
    const openButton = postRoot.querySelector("[data-blog-shortcuts-toggle]");
    const closeButton = postRoot.querySelector("[data-blog-shortcuts-close]");

    openButton?.addEventListener("click", () => {
      dialog?.showModal();
    });
    closeButton?.addEventListener("click", () => {
      dialog?.close();
    });
  }

  function slugifyTitle(text) {
    const map = {
      č: "c",
      ć: "c",
      đ: "dj",
      š: "s",
      ž: "z",
    };
    let value = (text || "").trim().toLowerCase();
    value = value.replace(/[čćđšž]/g, (char) => map[char] || char);
    value = value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return value.slice(0, 240) || "clanak";
  }

  function shouldAutoSyncSlug(postRoot, slugInput, title) {
    const placeholder = postRoot.dataset.draftTitlePlaceholder || "Bez naslova";
    const slugPrefix = postRoot.dataset.draftSlugPrefix || "nacrt-";
    const slug = (slugInput?.value || "").trim();

    if (!title || title === placeholder) {
      return false;
    }
    if (slugInput?.dataset.slugManual === "true") {
      return false;
    }
    if (!slug || slug.startsWith(slugPrefix)) {
      return true;
    }
    if (slug.includes("bez-naslova")) {
      return true;
    }
    if (slug === slugifyTitle(title)) {
      return true;
    }
    return slugInput?.dataset.autoSlug === "true";
  }

  function syncSlugFromTitle(postRoot) {
    const titleInput = document.getElementById("blog-post-title-input") || document.getElementById("id_title");
    const slugInput = document.getElementById("id_slug");
    if (!titleInput || !slugInput) {
      return;
    }

    const title = titleInput.value.trim();
    if (!shouldAutoSyncSlug(postRoot, slugInput, title)) {
      return;
    }

    const slug = slugifyTitle(title);
    if (slug && slugInput.value !== slug) {
      slugInput.value = slug;
      slugInput.dataset.autoSlug = "true";
      slugInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }

  function initTitleSlugSync(postRoot) {
    const titleInput = document.getElementById("blog-post-title-input") || document.getElementById("id_title");
    const slugInput = document.getElementById("id_slug");
    if (!titleInput || !slugInput) {
      return;
    }

    const slugPrefix = postRoot.dataset.draftSlugPrefix || "nacrt-";
    const slug = (slugInput.value || "").trim();
    const title = titleInput.value.trim();

    if (
      slug.startsWith(slugPrefix) ||
      slug.includes("bez-naslova") ||
      slug === slugifyTitle(title)
    ) {
      delete slugInput.dataset.slugManual;
      slugInput.dataset.autoSlug = "true";
    }

    slugInput.addEventListener("input", (event) => {
      if (!event.isTrusted) {
        return;
      }
      slugInput.dataset.slugManual = "true";
      delete slugInput.dataset.autoSlug;
    });

    const sync = () => syncSlugFromTitle(postRoot);
    titleInput.addEventListener("input", sync);
    titleInput.addEventListener("blur", sync);
    postRoot.blogTitleSlugSync = { sync };
    sync();
  }

  function getTitleValue() {
    const titleInput = document.getElementById("blog-post-title-input") || document.getElementById("id_title");
    return (titleInput?.value || "").trim();
  }

  function getSlugValue() {
    const slugInput = document.getElementById("id_slug");
    return (slugInput?.value || "").trim();
  }

  function isPublishingAttempt() {
    const publishField = document.getElementById("id_is_published");
    return Boolean(publishField && publishField.checked);
  }

  function checkPublishReadiness(postRoot) {
    syncSlugFromTitle(postRoot);

    const placeholder = postRoot.dataset.draftTitlePlaceholder || "Bez naslova";
    const slugPrefix = postRoot.dataset.draftSlugPrefix || "nacrt-";
    const title = getTitleValue();
    const slug = getSlugValue();

    if (!title || title === placeholder) {
      return {
        ok: false,
        message:
          "Objava je blokirana: unesite pravi naslov. Placeholder „Bez naslova” nije dozvoljen za objavljene članke.",
      };
    }

    if (slug.startsWith(slugPrefix)) {
      return {
        ok: false,
        message:
          "Objava je blokirana: URL slug još uvek koristi privremeni nacrt prefiks. Sačuvajte članak sa pravim naslovom da bi se slug ažurirao.",
      };
    }

    return { ok: true };
  }

  function showSubmitBlocker(postRoot, message) {
    if (window.BlogPageBuilderGlue && window.BlogPageBuilderGlue.showBlocker) {
      window.BlogPageBuilderGlue.showBlocker(postRoot, message);
      return;
    }
    window.alert(message);
  }

  function initSubmit(postRoot) {
    const form = postRoot.closest("form");
    const primaryButton = postRoot.querySelector(".blog-post-editor__primary-action");
    const publishField = document.getElementById("id_is_published");
    const hasPageBuilder = Boolean(postRoot.querySelector("[data-blog-page-builder]"));

    if (!form || !primaryButton) {
      return;
    }

    primaryButton.addEventListener("click", () => {
      const isPublished = postRoot.querySelector(".blog-post-editor__status-pill.is-published");
      if (!isPublished && publishField) {
        publishField.checked = true;
      }
    });

    if (!hasPageBuilder) {
      return;
    }

    form.addEventListener("submit", async (event) => {
      const builderState = postRoot.blogPageBuilderState;
      const glue = window.BlogPageBuilderGlue;
      const activeState = builderState;

      if (!activeState || !glue) {
        return;
      }

      if (form.dataset.blogSubmitting === "1") {
        event.preventDefault();
        return;
      }

      event.preventDefault();

      syncSlugFromTitle(postRoot);

      if (isPublishingAttempt()) {
        const readiness = checkPublishReadiness(postRoot);
        if (!readiness.ok) {
          showSubmitBlocker(postRoot, readiness.message);
          if (publishField) {
            publishField.checked = false;
          }
          return;
        }
      }

      form.dataset.blogSubmitting = "1";
      primaryButton.disabled = true;

      const flushResult = await glue.flushBeforeSubmit(activeState);
      if (!flushResult || !flushResult.ok) {
        delete form.dataset.blogSubmitting;
        primaryButton.disabled = false;
        showSubmitBlocker(
          postRoot,
          flushResult?.message || "Sadržaj nije sačuvan. Ispravite grešku i pokušajte ponovo.",
        );
        return;
      }

      form.submit();
    });
  }

  function resizeTitleField(titleInput) {
    if (!titleInput || titleInput.tagName !== "TEXTAREA") {
      return;
    }
    titleInput.style.height = "auto";
    titleInput.style.height = `${titleInput.scrollHeight}px`;
  }

  function initTitleFocus(postRoot) {
    const titleInput = document.getElementById("blog-post-title-input");
    const builderRoot = postRoot.querySelector("[data-blog-page-builder]");
    if (!titleInput || !builderRoot) {
      return;
    }

    resizeTitleField(titleInput);
    titleInput.addEventListener("input", () => resizeTitleField(titleInput));

    titleInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        builderRoot.focus();
      }
    });
  }

  function init() {
    document.querySelectorAll("[data-blog-post-editor]").forEach((postRoot) => {
      initDrawers(postRoot);
      initShortcuts(postRoot);
      initSubmit(postRoot);
      if (postRoot.querySelector("[data-blog-page-builder]")) {
        initTitleFocus(postRoot);
        initTitleSlugSync(postRoot);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

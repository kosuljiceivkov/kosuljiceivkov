(function () {
  "use strict";

  const BLOCK_TYPE_LABELS = {
    heading: "Naslov",
    text: "Tekst",
    image: "Slika",
    button: "Dugme",
    video: "Video",
    spacer: "Razmak",
    divider: "Linija",
    gallery: "Galerija",
    carousel: "Karusel",
  };

  const LEVEL_BADGES = {
    section: { className: "builder-node-badge--section", label: "Sekcija" },
    row: { className: "builder-node-badge--row", label: "Red" },
    column: { className: "builder-node-badge--column", label: "Kolona" },
    block: { className: "builder-node-badge--block", label: "Blok" },
  };

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function getInlineLevel(inline) {
    if (!inline) {
      return null;
    }
    if (inline.querySelector(":scope > fieldset.builder-section-inline")) {
      return "section";
    }
    if (inline.querySelector(":scope > fieldset.builder-row-inline")) {
      return "row";
    }
    if (inline.querySelector(":scope > fieldset.builder-column-inline")) {
      return "column";
    }
    if (inline.querySelector(":scope > fieldset.builder-block-root-marker")) {
      return "block";
    }
    return null;
  }

  function closestInlineRoot(element, markerClass) {
    const levelMap = {
      "builder-section-inline": "section",
      "builder-row-inline": "row",
      "builder-column-inline": "column",
      "builder-block-root-marker": "block",
    };
    const fieldset = element.closest("fieldset." + markerClass);
    if (!fieldset) {
      return null;
    }
    const inline = fieldset.closest(".inline-related");
    if (!inline || getInlineLevel(inline) !== levelMap[markerClass]) {
      return null;
    }
    return inline;
  }

  function getBlockRoot(selectEl) {
    const fieldset = selectEl.closest("fieldset.builder-block-root-marker");
    if (!fieldset) {
      return null;
    }
    const inline = fieldset.closest(".inline-related");
    return getInlineLevel(inline) === "block" ? inline : null;
  }

  function getOrderNumber(container) {
    const group = container.closest(".inline-group, .djn-group");
    if (group) {
      const siblings = group.querySelectorAll(":scope > .inline-related");
      for (let index = 0; index < siblings.length; index += 1) {
        if (siblings[index] === container) {
          return index + 1;
        }
      }
    }

    const orderInput = container.querySelector(':scope > fieldset input[name*="-order"]');
    if (orderInput && orderInput.value !== "") {
      const parsed = parseInt(orderInput.value, 10);
      if (!Number.isNaN(parsed)) {
        return parsed + 1;
      }
    }

    return 1;
  }

  function getParentInline(container, parentLevel) {
    const parentClass = "builder-inline-" + parentLevel;
    const parentGroup = container.closest(".inline-group." + parentClass);
    if (!parentGroup) {
      return null;
    }
    const parentInline = parentGroup.closest(".inline-related");
    if (getInlineLevel(parentInline) !== parentLevel) {
      return null;
    }
    return parentInline;
  }

  function countChildren(container, inlineClass) {
    return container.querySelectorAll(
      ":scope > .inline-group." + inlineClass + " > .inline-related"
    ).length;
  }

  function setInlineHeading(container, level, title, meta, number) {
    if (!container) {
      return;
    }

    const heading = container.querySelector(":scope > h3");
    if (!heading) {
      return;
    }

    const badge = LEVEL_BADGES[level];
    if (!badge) {
      return;
    }

    const num = number || getOrderNumber(container);
    container.dataset.builderLevel = level;
    container.dataset.builderNumber = String(num);

    heading.classList.add("builder-node-header", "djn-drag-handler");
    heading.innerHTML =
      '<span class="builder-node-badge ' +
      badge.className +
      '">' +
      badge.label +
      " #" +
      num +
      "</span>" +
      '<span class="builder-node-title">' +
      escapeHtml(title) +
      "</span>" +
      (meta
        ? '<span class="builder-node-meta">' + escapeHtml(meta) + "</span>"
        : "");

    ensureCollapseButton(container);
  }

  function ensureCollapseButton(container) {
    if (!container || container.dataset.collapseBound === "1") {
      return;
    }

    container.dataset.collapseBound = "1";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "builder-node-collapse";
    button.setAttribute("aria-expanded", "true");
    button.textContent = "Sakrij";

    const heading = container.querySelector(":scope > h3");
    if (heading) {
      heading.after(button);
    } else {
      container.prepend(button);
    }

    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      container.classList.toggle("is-collapsed");
      const collapsed = container.classList.contains("is-collapsed");
      button.textContent = collapsed ? "Prikaži" : "Sakrij";
      button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    });
  }

  function findNestedInlineGroup(blockRoot, markerClass) {
    const fieldset = blockRoot.querySelector("fieldset." + markerClass);
    if (!fieldset) {
      return null;
    }
    return fieldset.closest(".djn-group, .inline-group");
  }

  function setNestedInlineVisible(blockRoot, markerClass, visible) {
    const fieldset = blockRoot.querySelector("fieldset." + markerClass);
    const group = findNestedInlineGroup(blockRoot, markerClass);
    if (!group) {
      return;
    }
    group.style.display = visible ? "block" : "none";
    group.classList.toggle("builder-nested-visible", visible);
    if (fieldset) {
      fieldset.classList.toggle("builder-nested-visible", visible);
    }
  }

  function updateNestedInlineSaveHint(blockRoot, blockType) {
    blockRoot
      .querySelectorAll("[data-builder-nested-save-hint]")
      .forEach(function (node) {
        node.remove();
      });

    if (blockType !== "carousel" && blockType !== "gallery") {
      return;
    }

    const markerClass =
      blockType === "carousel"
        ? "builder-nested-inline--carousel"
        : "builder-nested-inline--gallery";
    if (findNestedInlineGroup(blockRoot, markerClass)) {
      return;
    }

    const hint = document.createElement("p");
    hint.className = "builder-block-save-hint";
    hint.dataset.builderNestedSaveHint = "1";
    hint.textContent =
      blockType === "carousel"
        ? "Sačuvajte stranicu (dugme „Sačuvaj” dole), zatim se ovde pojavi karusel sa stavkama za slike."
        : "Sačuvajte stranicu (dugme „Sačuvaj” dole), zatim se ovde pojavi galerija za slike.";

    const marker = blockRoot.querySelector(
      ":scope > fieldset.builder-block-root-marker"
    );
    if (marker) {
      marker.insertAdjacentElement("afterend", hint);
    }
  }

  function buildBlockContentTitle(blockRoot, blockType) {
    const label = BLOCK_TYPE_LABELS[blockType] || "Sadržaj";

    if (blockType === "heading") {
      const text = blockRoot
        .querySelector(':scope > fieldset input[name*="-heading_text"]')
        ?.value?.trim();
      return text ? label + ': "' + text + '"' : label;
    }

    if (blockType === "text") {
      const text = blockRoot
        .querySelector(':scope > fieldset textarea[name*="-text_content"]')
        ?.value?.trim();
      if (text) {
        const preview = text.slice(0, 48) + (text.length > 48 ? "…" : "");
        return label + ': "' + preview + '"';
      }
      return label;
    }

    if (blockType === "image") {
      const alt = blockRoot
        .querySelector(':scope > fieldset input[name*="-image_alt"]')
        ?.value?.trim();
      return alt ? label + ': "' + alt + '"' : label;
    }

    if (blockType === "button") {
      const text = blockRoot
        .querySelector(':scope > fieldset input[name*="-button_label"]')
        ?.value?.trim();
      return text ? label + ': "' + text + '"' : label;
    }

    if (blockType === "carousel") {
      return "Karusel";
    }

    if (blockType === "gallery") {
      const images = blockRoot.querySelectorAll(
        '.builder-nested-inline--gallery input[name*="-image"]'
      ).length;
      return images ? "Galerija · " + images + " sl." : "Galerija";
    }

    return label;
  }

  function updateBlockFields(blockRoot) {
    if (!blockRoot || getInlineLevel(blockRoot) !== "block") {
      return;
    }

    const typeSelect = blockRoot.querySelector(
      ':scope > fieldset.builder-block-root-marker select[name*="-block_type"]'
    );
    if (!typeSelect) {
      return;
    }

    const blockType = typeSelect.value;
    const number = getOrderNumber(blockRoot);
    const parentColumn = getParentInline(blockRoot, "column");
    const parentRow = getParentInline(blockRoot, "row");
    const parentSection = getParentInline(blockRoot, "section");

    blockRoot.querySelectorAll(":scope > fieldset.builder-block-fields").forEach(function (fieldset) {
      fieldset.style.display = "none";
      fieldset.classList.remove("open");
    });

    const activeFieldset = blockRoot.querySelector(
      ":scope > fieldset.builder-block-fields--" + blockType
    );
    if (activeFieldset) {
      activeFieldset.style.display = "";
      activeFieldset.classList.add("open");
    }

    setNestedInlineVisible(
      blockRoot,
      "builder-nested-inline--gallery",
      blockType === "gallery"
    );
    setNestedInlineVisible(
      blockRoot,
      "builder-nested-inline--carousel",
      blockType === "carousel"
    );
    updateNestedInlineSaveHint(blockRoot, blockType);

    const breadcrumb = [];
    if (parentSection) {
      breadcrumb.push("sekcija #" + getOrderNumber(parentSection));
    }
    if (parentRow) {
      breadcrumb.push("red #" + getOrderNumber(parentRow));
    }
    if (parentColumn) {
      breadcrumb.push("kolona #" + getOrderNumber(parentColumn));
    }

    setInlineHeading(
      blockRoot,
      "block",
      buildBlockContentTitle(blockRoot, blockType),
      (breadcrumb.length ? breadcrumb.join(" › ") + " · " : "") +
        "Tip: " +
        (BLOCK_TYPE_LABELS[blockType] || blockType),
      number
    );
  }

  function updateSectionTitle(sectionRoot) {
    if (!sectionRoot || getInlineLevel(sectionRoot) !== "section") {
      return;
    }

    const number = getOrderNumber(sectionRoot);
    const label = sectionRoot
      .querySelector(':scope > fieldset input[name*="-admin_label"]')
      ?.value?.trim();
    const rowCount = countChildren(sectionRoot, "builder-inline-row");
    const title = label ? label : "Deo stranice";
    const meta =
      (rowCount ? rowCount + " red" + (rowCount === 1 ? "" : "a") : "nema redova") +
      " · prevucite ⋮⋮";

    setInlineHeading(sectionRoot, "section", title, meta, number);
  }

  function updateRowTitle(rowRoot) {
    if (!rowRoot || getInlineLevel(rowRoot) !== "row") {
      return;
    }

    const number = getOrderNumber(rowRoot);
    const parentSection = getParentInline(rowRoot, "section");
    const columnCount = countChildren(rowRoot, "builder-inline-column");
    const meta =
      (parentSection ? "u sekciji #" + getOrderNumber(parentSection) + " · " : "") +
      (columnCount
        ? columnCount + " kolon" + (columnCount === 1 ? "a" : "e")
        : "nema kolona") +
      " · prevucite ⋮⋮";

    setInlineHeading(rowRoot, "row", "Horizontalni raspored kolona", meta, number);
  }

  function updateColumnTitle(columnRoot) {
    if (!columnRoot || getInlineLevel(columnRoot) !== "column") {
      return;
    }

    const number = getOrderNumber(columnRoot);
    const parentRow = getParentInline(columnRoot, "row");
    const desktop =
      columnRoot.querySelector(':scope > fieldset input[name*="-desktop_width"]')
        ?.value || "12";
    const tablet =
      columnRoot.querySelector(':scope > fieldset input[name*="-tablet_width"]')
        ?.value || "12";
    const mobile =
      columnRoot.querySelector(':scope > fieldset input[name*="-mobile_width"]')
        ?.value || "12";
    const blockCount = countChildren(columnRoot, "builder-inline-block");
    const meta =
      (parentRow ? "u redu #" + getOrderNumber(parentRow) + " · " : "") +
      (blockCount
        ? blockCount + " blok" + (blockCount === 1 ? "" : "a")
        : "nema blokova") +
      " · prevucite ⋮⋮";

    setInlineHeading(
      columnRoot,
      "column",
      "Širina D" + desktop + " · T" + tablet + " · M" + mobile,
      meta,
      number
    );
  }

  const WIDTH_BREAKPOINTS = [
    { key: "desktop", field: "desktop_width" },
    { key: "tablet", field: "tablet_width" },
    { key: "mobile", field: "mobile_width" },
  ];

  function renderWidthTrack(track, width) {
    track.innerHTML = "";
    for (let index = 1; index <= 12; index += 1) {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className =
        "builder-width-visual__cell" + (index <= width ? " is-active" : "");
      cell.dataset.width = String(index);
      cell.title = "Širina " + index + "/12";
      cell.setAttribute("aria-label", "Širina " + index + " od 12");
      track.appendChild(cell);
    }
  }

  function updateColumnWidthVisual(columnRoot) {
    if (!columnRoot || getInlineLevel(columnRoot) !== "column") {
      return;
    }

    WIDTH_BREAKPOINTS.forEach(function (breakpoint) {
      const input = columnRoot.querySelector(
        ':scope > fieldset input[name*="-' + breakpoint.field + '"]'
      );
      const track = columnRoot.querySelector(
        ':scope > fieldset [data-width-track="' + breakpoint.key + '"]'
      );
      if (!input || !track) {
        return;
      }

      const width = Math.min(
        12,
        Math.max(1, parseInt(input.value, 10) || 12)
      );
      renderWidthTrack(track, width);
    });
  }

  function bindColumnWidthVisual(columnRoot) {
    if (!columnRoot || getInlineLevel(columnRoot) !== "column") {
      return;
    }
    if (columnRoot.dataset.widthVisualBound === "1") {
      updateColumnWidthVisual(columnRoot);
      return;
    }

    columnRoot.dataset.widthVisualBound = "1";
    updateColumnWidthVisual(columnRoot);

    columnRoot.addEventListener("click", function (event) {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      const cell = target.closest(".builder-width-visual__cell");
      if (!cell) {
        return;
      }

      const track = cell.closest("[data-width-track]");
      if (!track) {
        return;
      }

      const breakpoint = track.getAttribute("data-width-track");
      const fieldName =
        breakpoint === "desktop"
          ? "desktop_width"
          : breakpoint === "tablet"
            ? "tablet_width"
            : "mobile_width";
      const input = columnRoot.querySelector(
        ':scope > fieldset input[name*="-' + fieldName + '"]'
      );
      if (!input) {
        return;
      }

      input.value = cell.dataset.width || "12";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
      updateColumnWidthVisual(columnRoot);
      updateColumnTitle(columnRoot);
    });
  }

  function updateInlineHeading(inline) {
    const level = getInlineLevel(inline);
    if (!level) {
      return;
    }

    switch (level) {
      case "section":
        updateSectionTitle(inline);
        break;
      case "row":
        updateRowTitle(inline);
        break;
      case "column":
        bindColumnWidthVisual(inline);
        updateColumnTitle(inline);
        break;
      case "block":
        updateBlockFields(inline);
        break;
      default:
        break;
    }
  }

  function refreshAllBuilderUI(root) {
    const scope = root || document;
    scope.querySelectorAll(".inline-related").forEach(updateInlineHeading);
  }

  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }

  onReady(function () {
    refreshAllBuilderUI();

    document.addEventListener("change", function (event) {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      if (target.matches('select[name*="-block_type"]')) {
        updateBlockFields(getBlockRoot(target));
        return;
      }

      if (target.matches('input[name*="-admin_label"], input[name*="-order"]')) {
        const sectionRoot = target.closest(".inline-related");
        if (getInlineLevel(sectionRoot) === "section") {
          updateSectionTitle(sectionRoot);
        }
        const rowRoot = target.closest(".inline-related");
        if (getInlineLevel(rowRoot) === "row") {
          updateRowTitle(rowRoot);
        }
        return;
      }

      if (
        target.matches(
          'input[name*="-desktop_width"], input[name*="-tablet_width"], input[name*="-mobile_width"], input[name*="-order"]'
        )
      ) {
        const columnRoot = target.closest(".inline-related");
        if (getInlineLevel(columnRoot) === "column") {
          updateColumnWidthVisual(columnRoot);
          updateColumnTitle(columnRoot);
        }
        return;
      }

      if (
        target.matches(
          'input[name*="-heading_text"], textarea[name*="-text_content"], input[name*="-image_alt"], input[name*="-button_label"], input[name*="-caption"], input[name*="-title"]'
        )
      ) {
        updateBlockFields(getBlockRoot(target));
      }
    });

    document.addEventListener("input", function (event) {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      if (target.matches('input[name*="-admin_label"]')) {
        const sectionRoot = target.closest(".inline-related");
        if (getInlineLevel(sectionRoot) === "section") {
          updateSectionTitle(sectionRoot);
        }
      }

      if (
        target.matches(
          'input[name*="-desktop_width"], input[name*="-tablet_width"], input[name*="-mobile_width"]'
        )
      ) {
        const columnRoot = target.closest(".inline-related");
        if (getInlineLevel(columnRoot) === "column") {
          updateColumnWidthVisual(columnRoot);
          updateColumnTitle(columnRoot);
        }
      }

      if (
        target.matches(
          'input[name*="-heading_text"], textarea[name*="-text_content"], input[name*="-image_alt"], input[name*="-button_label"], input[name*="-caption"], input[name*="-title"]'
        )
      ) {
        updateBlockFields(getBlockRoot(target));
      }
    });

    if (window.django && window.django.jQuery) {
      window.django.jQuery(document).on("formset:added", function (_event, row) {
        refreshAllBuilderUI(row && row[0] ? row[0] : document);
      });
    }

    document.addEventListener("click", function (event) {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      if (target.closest(".add-row a, .djn-add-handler, .grp-add-handler")) {
        window.setTimeout(function () {
          refreshAllBuilderUI();
        }, 120);
      }
    });
  });
})();

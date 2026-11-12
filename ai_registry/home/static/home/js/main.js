function debounce(func, timeout = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
}

function toggleFilterDropdown() {
  const filters = document.querySelector(".registry-filters");
  if (!filters) return;
  const button = filters.querySelector(".filter-button");
  const options = filters.querySelector(".filter-options");

  button.addEventListener("click", () => {
    const isHidden = window.getComputedStyle(options).display === "none";
    if (isHidden) {
      options.style.display = "";
      button.classList.add("active");
    } else {
      options.style.display = "none";
      button.classList.remove("active");
    }
  });
}

function toggleSortDropdown() {
  const filters = document.querySelector(".registry-filters");
  if (!filters) return;
  const button = filters.querySelector(".sort-button");
  const options = filters.querySelector(".sort-options");

  button.addEventListener("click", () => {
    const isHidden = window.getComputedStyle(options).display === "none";
    options.style.display = isHidden ? "" : "none";
  });
}

function checkCollapsibleEntry(entry) {
  const collapsible = entry.querySelector(".entry-collapsible");
  const content = entry.querySelector(".entry-content");
  const actions = entry.querySelector(".entry-actions");

  if (entry.classList.contains("collapsed")) {
    actions.style.display = "";
    collapsible.style.height = "";
    collapsible.offsetHeight; // force reflow

    if (content.offsetHeight < collapsible.offsetHeight) {
      actions.style.display = "none";
      collapsible.style.height = "auto";
    }
  }
}

function toggleRegistryEntries() {
  const entries = document.querySelectorAll(".registry-entry");
  entries.forEach(checkCollapsibleEntry);

  window.addEventListener(
    "resize",
    debounce(() => {
      entries.forEach(checkCollapsibleEntry);
    })
  );

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".registry-entry .expand-button");
    if (!button) return;

    const entry = button.closest(".registry-entry");
    const collapsible = entry.querySelector(".entry-collapsible");
    const content = entry.querySelector(".entry-content");

    if (entry.classList.contains("collapsed")) {
      collapsible.style.height = `${content.offsetHeight}px`;
      collapsible.addEventListener(
        "transitionend",
        () => {
          collapsible.style.height = "auto";
        },
        { once: true }
      );
      entry.classList.remove("collapsed");
    } else {
      collapsible.style.height = `${collapsible.offsetHeight}px`;
      collapsible.offsetHeight; // force reflow
      collapsible.style.height = "";
      entry.classList.add("collapsed");
    }

    const newText = button.dataset.toggleText;
    button.dataset.toggleText = button.textContent;
    button.textContent = newText;
  });
}

function togglePillTooltips() {
  document.addEventListener("focusin", (event) => {
    const pill = event.target.closest(".pill.has-tooltip");
    if (!pill) return;

    const tooltip = pill.querySelector(".pill-tooltip-container");
    if (!tooltip) return;

    tooltip.style.display = "";
    tooltip.style.top = "auto";
    tooltip.style.right = "auto";

    const left = pill.offsetLeft + pill.offsetWidth - tooltip.offsetWidth;
    const top = pill.offsetTop - window.scrollY;
    tooltip.style.position = "fixed";
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  });

  document.addEventListener("focusout", (event) => {
    const pill = event.target.closest(".pill.has-tooltip");
    if (!pill) return;

    const tooltip = pill.querySelector(".pill-tooltip-container");
    if (tooltip) tooltip.style.display = "none";
  });

  document.addEventListener("scroll", () => {
    if (document.activeElement.matches(".pill.has-tooltip")) {
      document.activeElement.blur();
    }
  });
}

(function main() {
  toggleFilterDropdown();
  toggleSortDropdown();
  toggleRegistryEntries();
  togglePillTooltips();
})();

(function () {
  function initMermaid() {
    if (typeof mermaid === "undefined") return;

    const isDark =
      document.body.getAttribute("data-md-color-scheme") === "slate";

    mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? "dark" : "default",
      securityLevel: "loose",
    });

    document.querySelectorAll(".mermaid").forEach((el) => {
      const graph = el.textContent;
      el.textContent = "";
      mermaid.render("mmd-" + Math.random().toString(16).slice(2), graph).then(({ svg }) => {
        el.innerHTML = svg;
      });
    });
  }

  // Initial load
  document.addEventListener("DOMContentLoaded", initMermaid);

  // Re-init on theme switch (Material swaps scheme attribute)
  const obs = new MutationObserver(() => initMermaid());
  obs.observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
})();

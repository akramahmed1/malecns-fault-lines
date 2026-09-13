/* MaleCNS Structural Atlas - shared helpers. No dependencies. */
(function () {
  "use strict";

  var DATA_URL = "data/atlas_data.json";

  function fmtInt(n) {
    if (n === null || n === undefined) return "n/a";
    return Math.round(n).toLocaleString("en-US");
  }

  function fmtFloat(n, digits) {
    if (n === null || n === undefined) return "n/a";
    return Number(n).toFixed(digits === undefined ? 2 : digits);
  }

  function pct(f, digits) {
    if (f === null || f === undefined) return "n/a";
    return (f * 100).toFixed(digits === undefined ? 2 : digits) + "%";
  }

  function loadData(cb) {
    fetch(DATA_URL)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(cb)
      .catch(function (err) {
        document.querySelectorAll(".loading").forEach(function (el) {
          el.textContent = "Could not load atlas data (" + err.message +
            "). Run docs/build_data.py to regenerate data/atlas_data.json.";
        });
      });
  }

  function setActiveNav() {
    var page = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll("nav a").forEach(function (a) {
      if (a.getAttribute("href") === page) a.classList.add("active");
    });
  }

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  }

  window.Atlas = {
    loadData: loadData,
    fmtInt: fmtInt,
    fmtFloat: fmtFloat,
    pct: pct,
    esc: esc,
    setActiveNav: setActiveNav
  };

  document.addEventListener("DOMContentLoaded", setActiveNav);
})();

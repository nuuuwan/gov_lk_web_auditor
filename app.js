(function () {
  var search = document.getElementById("q");
  var level = document.getElementById("f-level");
  var status = document.getElementById("f-status");
  var groups = Array.prototype.slice.call(document.querySelectorAll("tbody.group"));
  function filtered(groups) {
    var q = search.value.toLowerCase();
    var shown = 0;
    groups.forEach(function (tb) {
      var collapsed = tb.classList.contains("collapsed");
      Array.prototype.slice.call(tb.querySelectorAll("tr[data-search]")).forEach(function (row) {
        var ok =
          row.dataset.search.indexOf(q) !== -1 &&
          (level.value === "" || row.dataset.level === level.value) &&
          (status.value === "" || row.dataset.status === status.value);
        if (ok && !collapsed) {
          row.style.display = "";
          shown++;
        } else {
          row.style.display = "none";
        }
      });
    });
    var countEl = document.getElementById("result-count");
    if (countEl) countEl.textContent = shown + " sites shown";
  }
  function makeRowClickable() {
    document.querySelectorAll("tr[data-search]").forEach(function (row) {
      row.addEventListener("click", function (e) {
        if (e.target.tagName === "A") return;
        var link = row.querySelector("a");
        if (link) window.location.href = link.href;
      });
    });
  }
  function initGroups() {
    groups.forEach(function (tb) {
      var btn = tb.querySelector(".group-toggle");
      if (!btn) return;
      btn.addEventListener("click", function () {
        var collapsed = tb.classList.toggle("collapsed");
        btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
        filtered(groups);
      });
    });
  }
  function initCollapsibles() {
    document.querySelectorAll(".collapsible").forEach(function (el) {
      el.addEventListener("click", function () {
        var target = el.nextElementSibling;
        if (!target) return;
        var open = target.classList.toggle("open");
        el.setAttribute("aria-expanded", open ? "true" : "false");
      });
    });
  }
  [search, level, status].forEach(function (el) { el.addEventListener("input", function () { filtered(groups); }); });
  document.querySelectorAll("th button[data-sort]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.dataset.sort;
      var asc = btn.getAttribute("aria-sort") !== "ascending";
      groups.forEach(function (tb) {
        var rows = Array.prototype.slice.call(tb.querySelectorAll("tr[data-search]"));
        rows.sort(function (a, b) {
          var x = a.dataset[key], y = b.dataset[key];
          var nx = parseFloat(x), ny = parseFloat(y);
          if (!isNaN(nx) && !isNaN(ny)) return asc ? nx - ny : ny - nx;
          return asc ? x.localeCompare(y) : y.localeCompare(x);
        });
        rows.forEach(function (row) { tb.appendChild(row); });
      });
      btn.setAttribute("aria-sort", asc ? "ascending" : "descending");
    });
  });
  filtered(groups);
  makeRowClickable();
  initGroups();
  initCollapsibles();
})();

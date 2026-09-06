from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from ..classification.LevelEvaluator import LevelEvaluator
from ..time.SriLankaTime import SriLankaTime
from .DashboardLoader import COPIED_FILES, DashboardLoader
from .DashboardSummary import DashboardSummary

STATUS_ICON = {"pass": "\u2713", "fail": "\u2715", "inconclusive": "?"}
SCHEMA_VERSION = "1.0.0"
ROWS_PER_PAGE = 25

CSS = """\
:root {
  --ink: #1c2420;
  --muted: #4c5a54;
  --paper: #f5f6f3;
  --card: #ffffff;
  --line: #d4dad6;
  --accent: #0f5b3f;
  --red: #9c2b1e;
  --amber: #7a5200;
  --green: #0f5b3f;
  --focus: #0b3d8f;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
a { color: var(--accent); }
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 2px;
}
header.site, main, footer.site { width: min(1100px, calc(100% - 32px)); margin: auto; }
header.site { padding: 40px 0 16px; border-bottom: 3px solid var(--ink); }
.eyebrow {
  font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}
h1 { margin: 8px 0 4px; font-size: clamp(26px, 4.5vw, 44px); line-height: 1.1; }
h2 { margin-top: 40px; font-size: 22px; }
h3 { font-size: 17px; margin: 28px 0 8px; }
.lede { color: var(--muted); max-width: 70ch; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 20px 0; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
.card strong { display: block; font-size: 24px; line-height: 1.2; }
.card span { color: var(--muted); font-size: 13px; }
.level-counts { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 20px; padding: 0; list-style: none; }
.level-counts li { background: var(--card); border: 1px solid var(--line); border-radius: 999px; padding: 4px 12px; font-size: 14px; }
.filters { display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; align-items: flex-end; }
.filters label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 700; }
.filters input, .filters select { font: inherit; font-weight: 400; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); color: var(--ink); min-width: 200px; }
.search-field { position: relative; }
.search-field input { padding-left: 32px; min-width: 260px; }
.search-icon { position: absolute; left: 8px; bottom: 8px; width: 16px; height: 16px; color: var(--muted); pointer-events: none; }
.table-wrap { overflow-x: auto; background: var(--card); border: 1px solid var(--line); border-radius: 10px; }
table { width: 100%; border-collapse: collapse; font-size: 15px; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; background: #ecefec; }
th button { all: unset; cursor: pointer; font: inherit; text-transform: inherit; letter-spacing: inherit; }
th button:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
.badge { display: inline-block; white-space: nowrap; font-weight: 700; font-size: 13px; border: 1px solid currentColor; border-radius: 999px; padding: 1px 10px; }
.st-pass { color: var(--green); }
.st-fail { color: var(--red); }
.st-inconclusive { color: var(--amber); }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: baseline; }
.lv0 { background: #333; } .lv1 { background: #c0392b; } .lv2 { background: #d97a08; }
.lv3 { background: #1e8449; } .lv4 { background: #2471a3; } .lv5 { background: #7d3c98; }
.meta { display: flex; flex-wrap: wrap; gap: 8px 32px; margin: 16px 0; }
.meta div span { display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }
.meta div strong { font-size: 17px; }
.notice { background: var(--card); border: 1px solid var(--line); border-left: 6px solid var(--amber); border-radius: 8px; padding: 12px 16px; margin: 16px 0; }
footer.site { padding: 32px 0 56px; color: var(--muted); font-size: 14px; }
.skip { position: absolute; left: -9999px; }
.skip:focus { left: 8px; top: 8px; background: var(--card); padding: 8px 12px; z-index: 10; }
.group-heading { font-size: 15px; font-weight: 700; margin: 24px 0 4px; padding: 6px 12px; background: #ecefec; border-radius: 6px; }
tr[data-search] { cursor: pointer; }
tr[data-search]:hover { background: var(--card); }
tr[data-search] a { pointer-events: none; }
.pagination { display: flex; gap: 6px; flex-wrap: wrap; margin: 12px 0; align-items: center; }
.pagination button { all: unset; cursor: pointer; padding: 4px 10px; border: 1px solid var(--line); border-radius: 6px; background: var(--card); font-size: 14px; }
.pagination button[aria-current="page"] { background: var(--accent); color: #fff; border-color: var(--accent); }
.pagination button:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
.pagination-info { font-size: 13px; color: var(--muted); }
.collapsible { cursor: pointer; user-select: none; }
.collapsible::before { content: "\\25B6"; display: inline-block; margin-right: 6px; font-size: 11px; transition: transform 0.2s; }
.collapsible[aria-expanded="true"]::before { transform: rotate(90deg); }
.collapsible-content { display: none; }
.collapsible-content.open { display: block; }
@media (max-width: 640px) { th:nth-child(5), td:nth-child(5) { display: none; } th:nth-child(4), td:nth-child(4) { display: none; } }
@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e8edea;
    --muted: #a9b6b0;
    --paper: #121614;
    --card: #1b211e;
    --line: #333d38;
    --accent: #7fd6a8;
    --red: #f09688;
    --amber: #e8bd5a;
    --green: #7fd6a8;
    --focus: #9ec1ff;
  }
  th { background: #232b27; }
  .group-heading { background: #232b27; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
@media print {
  header.site, footer.site { border: none; padding: 0; }
  header.site { padding-bottom: 8px; }
  .filters, .pagination, .skip, form, nav { display: none !important; }
  .table-wrap { border: none; overflow: visible; }
  table { font-size: 11px; }
  th, td { padding: 4px 6px; }
  body { background: #fff; color: #000; }
  .card { border: 1px solid #ccc; }
  .group-heading { background: #eee; }
  a { color: #000; }
  a[href]::after { content: " (" attr(href) ")"; font-size: 10px; color: #666; }
  tr[data-search] a::after { content: none; }
}
"""

JS = """\
(function () {
  var search = document.getElementById("q");
  var level = document.getElementById("f-level");
  var status = document.getElementById("f-status");
  var rows = Array.prototype.slice.call(document.querySelectorAll("tbody tr[data-search]"));
  var page = 1;
  var perPage = parseInt(document.getElementById("page-size") ? document.getElementById("page-size").value : "25", 10);
  function pageRows() { return rows.filter(function (r) { return r.style.display !== "none"; }); }
  function apply() {
    var q = search.value.toLowerCase();
    rows.forEach(function (row) {
      var ok =
        row.dataset.search.indexOf(q) !== -1 &&
        (level.value === "" || row.dataset.level === level.value) &&
        (status.value === "" || row.dataset.status === status.value);
      row.style.display = ok ? "" : "none";
    });
    page = 1;
    paginate();
  }
  function paginate() {
    var shown = pageRows();
    var total = shown.length;
    var start = (page - 1) * perPage;
    var end = start + perPage;
    rows.forEach(function (row) {
      var vis = row.style.display !== "none";
      var idx = shown.indexOf(row);
      if (vis) row.style.display = (idx >= start && idx < end) ? "" : "none";
    });
    var countEl = document.getElementById("result-count");
    if (countEl) countEl.textContent = (total === rows.length ? rows.length : start + 1 + "\\u2013" + Math.min(end, total) + " of " + total) + " sites shown";
    renderPagination(total, start, end);
  }
  function renderPagination(total, start, end) {
    var wrap = document.getElementById("pagination");
    if (!wrap) return;
    if (total <= perPage) { wrap.innerHTML = ""; return; }
    var pages = Math.ceil(total / perPage);
    var html = "";
    if (page > 1) html += '<button data-pg="' + (page - 1) + '">Prev</button>';
    for (var i = 1; i <= pages; i++) {
      if (pages > 7 && i > 2 && i < pages - 1 && Math.abs(i - page) > 1) { if (i === 3 || i === pages - 2) html += '<span>...</span>'; continue; }
      html += '<button data-pg="' + i + '"' + (i === page ? ' aria-current="page"' : '') + '>' + i + '</button>';
    }
    if (page < pages) html += '<button data-pg="' + (page + 1) + '">Next</button>';
    wrap.innerHTML = html;
    wrap.querySelectorAll("button[data-pg]").forEach(function (b) {
      b.addEventListener("click", function () { page = parseInt(b.dataset.pg, 10); paginate(); });
    });
  }
  function makeRowClickable() {
    rows.forEach(function (row) {
      row.addEventListener("click", function (e) {
        if (e.target.tagName === "A") return;
        var link = row.querySelector("a");
        if (link) window.location.href = link.href;
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
  [search, level, status].forEach(function (el) { el.addEventListener("input", apply); });
  var ps = document.getElementById("page-size");
  if (ps) ps.addEventListener("change", function () { perPage = parseInt(ps.value, 10); page = 1; paginate(); });
  document.querySelectorAll("th button[data-sort]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.dataset.sort;
      var asc = btn.getAttribute("aria-sort") !== "ascending";
      var tbody = document.querySelector("tbody");
      rows.sort(function (a, b) {
        var x = a.dataset[key], y = b.dataset[key];
        var nx = parseFloat(x), ny = parseFloat(y);
        if (!isNaN(nx) && !isNaN(ny)) return asc ? nx - ny : ny - nx;
        return asc ? x.localeCompare(y) : y.localeCompare(x);
      });
      rows.forEach(function (row) { tbody.appendChild(row); });
      btn.setAttribute("aria-sort", asc ? "ascending" : "descending");
    });
  });
  apply();
  makeRowClickable();
  initCollapsibles();
})();
"""


class DashboardBuilder:
    def build(
        self,
        reports: Path = Path("latest_audit_reports"),
        output: Path = Path("site"),
        directory: Path | None = Path("static_data/websites.json"),
    ) -> dict:
        if directory is not None and not directory.is_file():
            directory = None
        sites, errors = DashboardLoader().load(reports, directory)
        summary = DashboardSummary().summarize(sites)
        output.mkdir(parents=True, exist_ok=True)
        (output / ".nojekyll").write_text("", encoding="utf-8")
        (output / "favicon.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
            '<circle cx="16" cy="16" r="14" fill="#0f5b3f"/>'
            '<text x="16" y="21" text-anchor="middle" font-size="16" '
            'font-family="system-ui" fill="#fff" font-weight="700">G</text></svg>',
            encoding="utf-8",
        )
        (output / "style.css").write_text(CSS, encoding="utf-8")
        (output / "app.js").write_text(JS, encoding="utf-8")
        (output / "data.json").write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "build_time": SriLankaTime.now().isoformat(),
                    "summary": summary,
                    "sites": [self._entry(site) for site in sites],
                    "errors": errors,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (output / "index.html").write_text(
            self._index(sites, errors, summary), encoding="utf-8"
        )
        for site in sites:
            folder = output / "sites" / site["host"]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_text(
                self._detail(site, summary), encoding="utf-8"
            )
            for name in COPIED_FILES:
                source = reports / site["host"] / name
                if source.is_file():
                    shutil.copyfile(source, folder / name)
        return {"summary": summary, "sites": len(sites), "errors": errors}

    def _entry(self, site: dict) -> dict:
        return {
            key: site[key]
            for key in (
                "host",
                "url",
                "normalized_url",
                "institution",
                "ministry",
                "level",
                "level_label",
                "score",
                "max_score",
                "completed_at",
                "failed_checks",
                "inconclusive_checks",
                "status_group",
                "files",
            )
        } | {"detail_url": f"sites/{site['host']}/"}

    def _index(self, sites: list, errors: list, summary: dict) -> str:
        if sites:
            groups = self._group_by_ministry(sites)
            rows_html = "\n".join(
                self._grouped_rows(label, group_sites)
                for label, group_sites in groups
            )
            table = f"""\
      <p id="result-count" aria-live="polite"></p>
      <div class="table-wrap" role="region" aria-label="Audited sites" tabindex="0">
      <table>
        <thead><tr>
          <th><button data-sort="site" aria-sort="none">Site &#9650;&#9660;</button></th>
          <th><button data-sort="level" aria-sort="none">Level &#9650;&#9660;</button></th>
          <th><button data-sort="score" aria-sort="none">Score &#9650;&#9660;</button></th>
          <th>Status</th>
          <th>Audited</th>
        </tr></thead>
        <tbody>
{rows_html}
        </tbody>
      </table>
      </div>
      <div class="pagination" id="pagination" aria-label="Pagination"></div>
      <div style="margin:8px 0">
        <label for="page-size" style="font-size:13px;color:var(--muted)">Rows per page</label>
        <select id="page-size" style="font:inherit;padding:4px 8px;border:1px solid var(--line);border-radius:6px">
          <option value="10">10</option><option value="25" selected>25</option>
          <option value="50">50</option><option value="100">100</option>
        </select>
      </div>
      <noscript><p>Search, filters and sorting need JavaScript. All sites and report links are listed above.</p></noscript>"""
        else:
            table = (
                '<div class="notice" role="status">'
                "No audit reports were found. The dashboard will populate "
                "once audits are committed under "
                "<code>latest_audit_reports/&lt;host&gt;/audit.json</code>."
                "</div>"
            )
        problems = ""
        if errors:
            items = "".join(
                f"<li><strong>{html.escape(item['host'])}</strong>: "
                f"{html.escape(item['message'])}</li>"
                for item in errors
            )
            problems = (
                '<div class="notice" role="alert"><strong>Skipped reports '
                f"({len(errors)}):</strong><ul>{items}</ul></div>"
            )
        counts = "".join(
            f"<li>{html.escape(self._level_name(number))}: "
            f"<strong>{summary['by_level'].get(number, 0)}</strong></li>"
            for number in range(6)
        )
        return f"""\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Government website audits &middot; Sri Lanka</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml" />
<link rel="stylesheet" href="style.css" />
</head>
<body>
<a class="skip" href="#sites">Skip to site table</a>
<header class="site">
<div class="eyebrow">glwa &middot; Government website audits</div>
<h1>Government website audits</h1>
<p class="lede">Evidence-based grading of Sri Lankan government websites. Every figure below comes from the committed audit data with no live requests. Open a site for its level progression, check results, evidence and downloadable reports.</p>
</header>
<main>
<section aria-label="Overview">
<div class="cards">
<div class="card"><strong>{summary['total']}</strong><span>Audited sites</span></div>
<div class="card"><strong>{summary['average_score']:.1f}/{summary['max_score']}</strong><span>Average score</span></div>
<div class="card"><strong>{html.escape(self._short(summary['last_audit']))}</strong><span>Last audit</span></div>
</div>
<ul class="level-counts">{counts}</ul>
</section>
<section aria-label="Sites" id="sites">
<h2>Sites</h2>
<form class="filters" role="search" onsubmit="return false">
<div class="search-field">
<svg class="search-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
<input id="q" type="search" placeholder="Filter by institution, host or URL" autocomplete="off" />
</div>
<label>Level<select id="f-level"><option value="">All levels</option>
<option value="0">Level 0</option><option value="1">Level 1</option><option value="2">Level 2</option>
<option value="3">Level 3</option><option value="4">Level 4</option><option value="5">Level 5</option></select></label>
<label>Status<select id="f-status"><option value="">Any status</option>
<option value="attention">Has failures</option><option value="inconclusive">Inconclusive only</option><option value="clean">Clean</option></select></label>
</form>
{table}
{problems}
</section>
</main>
<footer class="site"><p>Built from <code>latest_audit_reports/*/audit.json</code>. Scores match the repository README method. See <a href="https://github.com/nuuuwan/gov_lk_web_auditor">gov_lk_web_auditor</a> for Markdown reports and method docs.</p></footer>
<script src="app.js" defer></script>
</body>
</html>
"""

    def _group_by_ministry(self, sites: list) -> list[tuple[str, list]]:
        groups: dict[str, list] = {}
        for site in sites:
            groups.setdefault(site.get("ministry", ""), []).append(site)
        ordered = []
        for ministry, group_sites in groups.items():
            ordered.append((ministry, group_sites))
        ordered.sort(key=lambda item: (item[0] == "", item[0]))
        return ordered

    def _grouped_rows(self, ministry: str, sites: list) -> str:
        heading = ""
        if ministry:
            count = len(sites)
            heading = (
                f'          <tr><td colspan="5" class="group-heading">'
                f"{html.escape(ministry)} ({count} site{'s' if count != 1 else ''})"
                f"</td></tr>\n"
            )
        rows = "\n".join(self._row(site) for site in sites)
        return heading + rows

    def _row(self, site: dict) -> str:
        search = html.escape(
            f"{site['institution']} {site['host']} {site['normalized_url']} "
            f"{site.get('ministry', '')}".lower()
        )
        status = self._status_text(site)
        href = f"sites/{html.escape(site['host'])}/"
        return (
            f'          <tr data-search="{search}" data-level="{site["level"]}" '
            f'data-status="{site["status_group"]}" data-site="{search}" '
            f'data-score="{site["score"]}">'
            f"<td><a href=\"{href}\">"
            f"{html.escape(site['institution'])}</a><br />"
            f"<small>{html.escape(site['normalized_url'])}</small></td>"
            f"<td><span class=\"dot lv{site['level']}\" aria-hidden=\"true\"></span>"
            f"{html.escape(site['level_label'])}</td>"
            f"<td>{site['score']:.1f}/{site['max_score']}</td>"
            f"<td>{status}</td>"
            f"<td>{html.escape(self._short(site['completed_at']))}</td></tr>"
        )

    def _detail(self, site: dict, summary: dict) -> str:
        levels = "\n".join(self._level_row(item) for item in site["levels"])
        check_sections = "\n".join(
            self._check_section(item)
            for item in site["levels"]
            if item.get("checks")
        )
        evidence_count = len(site["evidence"])
        evidence = "\n".join(self._evidence_row(item) for item in site["evidence"])
        files = " ".join(
            f"<li><a href=\"{html.escape(name)}\">{html.escape(name)}</a></li>"
            for name in site["files"]
        ) or "<li>No downloadable files were copied for this site.</li>"
        evidence_block = ""
        if evidence:
            evidence_block = (
                f'<h2 class="collapsible" role="button" aria-expanded="false">'
                f"Evidence ({evidence_count})</h2>\n"
                f'<div class="collapsible-content">\n'
                f'<div class="table-wrap" role="region" aria-label="Evidence" tabindex="0">\n'
                f'<table><thead><tr><th>Check</th><th>Status</th>'
                f"<th>Detail</th><th>Source</th></tr></thead>\n"
                f"<tbody>\n{evidence}\n</tbody></table>\n</div>\n</div>"
            )
        else:
            evidence_block = (
                '<h2>Evidence (0)</h2>\n<p>No evidence items recorded.</p>'
            )
        return f"""\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(site['normalized_url'])} &middot; Website audit</title>
<link rel="icon" href="../../favicon.svg" type="image/svg+xml" />
<link rel="stylesheet" href="../../style.css" />
</head>
<body>
<a class="skip" href="#levels">Skip to level progression</a>
<header class="site">
<div class="eyebrow"><a href="../../">All sites</a> &middot; glwa website audit</div>
<h1>{html.escape(site['institution'])}</h1>
<p class="lede"><a href="{html.escape(site['normalized_url'])}">{html.escape(site['normalized_url'])}</a></p>
</header>
<main>
<section aria-label="Result">
<div class="meta">
<div><span>Achieved</span><strong><span class="dot lv{site['level']}" aria-hidden="true"></span>{html.escape(site['level_label'])}</strong></div>
<div><span>Score</span><strong>{site['score']:.1f}/{site['max_score']}</strong></div>
<div><span>Audited</span><strong>{html.escape(self._full_date(site['completed_at']))}</strong></div>
<div><span>Checks</span><strong>{site['failed_checks']} failed &middot; {site['inconclusive_checks']} inconclusive</strong></div>
</div>
</section>
<section aria-label="Level progression" id="levels">
<h2>Level progression</h2>
<div class="table-wrap" role="region" aria-label="Level progression" tabindex="0">
<table><thead><tr><th>Level</th><th>Status</th><th>Reason</th></tr></thead>
<tbody>
{levels}
</tbody></table>
</div>
</section>
<section aria-label="Check results">
<h2>Check results</h2>
{check_sections or '<p>No individual check results recorded.</p>'}
</section>
<section aria-label="Evidence">
{evidence_block}
</section>
<section aria-label="Downloads">
<h2>Reports and downloads</h2>
<ul>{files}</ul>
</section>
</main>
<footer class="site"><p><a href="../../">Back to all {summary['total']} sites</a> &middot; Counts, levels, scores and timestamps match the committed audit data.</p></footer>
<script src="../../app.js" defer></script>
</body>
</html>
"""

    def _level_row(self, item: dict) -> str:
        return (
            f"<tr><td>Level {int(item.get('level', 0))}</td>"
            f"<td>{self._badge(str(item.get('status', 'inconclusive')))}</td>"
            f"<td>{html.escape(str(item.get('reason', '')))}</td></tr>"
        )

    def _check_section(self, item: dict) -> str:
        rows = "\n".join(
            f"<tr><td>{html.escape(str(check.get('name', '')))}</td>"
            f"<td>{self._badge(str(check.get('status', 'inconclusive')))}</td>"
            f"<td>{html.escape(str(check.get('reason', '')))}</td></tr>"
            for check in item["checks"]
        )
        return (
            f"<h3>Level {int(item.get('level', 0))} checks</h3>"
            '<div class="table-wrap" role="region" tabindex="0">'
            "<table><thead><tr><th>Check</th><th>Status</th><th>Reason</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )

    def _evidence_row(self, item: dict) -> str:
        if not isinstance(item, dict):
            return ""
        source = str(item.get("source", ""))
        if source.startswith("http"):
            cell = f"<a href=\"{html.escape(source)}\">{html.escape(source)}</a>"
        else:
            cell = html.escape(source)
        return (
            f"<tr><td>{html.escape(str(item.get('check', '')))}</td>"
            f"<td>{self._badge(str(item.get('status', 'inconclusive')))}</td>"
            f"<td>{html.escape(str(item.get('detail', '')))}</td>"
            f"<td>{cell}</td></tr>"
        )

    def _badge(self, status: str) -> str:
        icon = STATUS_ICON.get(status, "?")
        label = html.escape(status.capitalize())
        return (
            f"<span class=\"badge st-{html.escape(status)}\">"
            f"<span aria-hidden=\"true\">{icon}</span> {label}</span>"
        )

    def _status_text(self, site: dict) -> str:
        if site["failed_checks"]:
            return self._badge("fail") + f" {site['failed_checks']} failed"
        if site["inconclusive_checks"]:
            return (
                self._badge("inconclusive")
                + f" {site['inconclusive_checks']} inconclusive"
            )
        return self._badge("pass") + " clean"

    def _level_name(self, number: int) -> str:
        return LevelEvaluator.LEVELS[number].label

    def _short(self, value: str) -> str:
        if not value:
            return "\u2014"
        try:
            return SriLankaTime.parse(value).strftime("%Y-%m-%d %H:%M SLST")
        except ValueError:
            return value

    def _full_date(self, value: str) -> str:
        if not value:
            return "\u2014"
        try:
            return SriLankaTime.parse(value).strftime(
                "%Y-%m-%d %H:%M:%S SLST"
            )
        except ValueError:
            return value

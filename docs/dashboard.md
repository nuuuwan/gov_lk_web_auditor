# Audit dashboard

The public dashboard is a fully static GitHub Pages site generated from the
committed `latest_audit_reports/*/audit.json` files. The build makes no live
requests to government websites.

Public URL (after enabling Pages with the **GitHub Actions** source):

`https://nuuuwan.github.io/gov_lk_web_auditor/`

## Preview locally

```bash
PYTHONPATH=src python3 -m glwa.dashboard --reports latest_audit_reports --output site
python3 -m http.server --directory site 8000
```

Open `http://localhost:8000/`. Detail pages live at `sites/<host>/`, for
example `http://localhost:8000/sites/daph.gov.lk/`.

## How it works

- `src/glwa/dashboard/DashboardLoader.py` reads every
  `latest_audit_reports/*/audit.json`. A missing or malformed report is
  listed on the overview page and never breaks the build. Institution and
  ministry names are resolved from `static_data/websites.json` and grouped
  in the overview table.
- `src/glwa/dashboard/DashboardSummary.py` computes the total sites, counts
  by achieved level, average score and last audit time. Level and score reuse
  the same `WebsiteScore` and max-passed-level logic as the README.
- `src/glwa/dashboard/DashboardBuilder.py` writes `index.html`, one
  `sites/<host>/` detail page per site, `data.json`, `style.css`, `app.js`,
  `.nojekyll` and `favicon.svg`, and copies each site's `audit.json`,
  `audit.md`, `evidence.csv`, `levels.csv` and `report.html` next to its
  detail page so links never leave the static site.
- The overview table is server-rendered, so core content and report links
  work with JavaScript disabled. JavaScript adds search (with magnifying-glass
  icon), level/status filters, column sorting, pagination, clickable rows,
  and collapsible evidence tables.
- Status is shown with text, icons (`pass`/`fail`/`inconclusive`) and colour,
  and the layout honours `prefers-color-scheme`, `prefers-reduced-motion`
  and print stylesheets.
- `data.json` includes `schema_version` and `build_time` for staleness
  debugging.
- Pages are paginated (25 per page, configurable 10/25/50/100) so the
  dashboard scales to hundreds of sites without overwhelming the browser.

## Deployment

`.github/workflows/dashboard-pages.yml` rebuilds on every `main` push that
touches the dashboard source, `latest_audit_reports/**`,
`static_data/websites.json`, `audit.output/**`, tests or the workflow itself.
It uses only `contents: read`, `pages: write` and `id-token: write`,
deploys through the `github-pages` environment, and serialises runs with
`concurrency: group: pages`.

## Features

| Feature | Description |
| --- | --- |
| Ministry grouping | Sites grouped under their parent ministry from `websites.json` |
| Search | Case-insensitive filter across institution, host and URL |
| Level filter | Filter by achieved level (0-5) |
| Status filter | Filter by check status (clean, inconclusive, attention) |
| Pagination | 25 rows per page, configurable |
| Sortable columns | Click column headers to sort |
| Clickable rows | Click any row to open the detail page |
| Evidence toggle | Evidence tables collapsed by default, click to expand |
| Print stylesheet | Clean print layout with hidden filters and navigation |
| Dark mode | Automatic via `prefers-color-scheme` |
| Reduced motion | Animations disabled when `prefers-reduced-motion` is set |
| Favicon | SVG globe icon with `G` monogram |
| `.nojekyll` | Prevents Jekyll processing on GitHub Pages |
| Fallback URLs | Core links work without JavaScript |

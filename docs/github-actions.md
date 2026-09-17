# GitHub Actions

## Audit workflow

The audit workflow runs on GitHub-hosted `ubuntu-latest` runners on a daily
schedule. It does not run on pull requests, so code from an untrusted fork is
never sent to a trusted runner.

Dispatch a limited run from the Actions page with `max_urls=1` first. The
workflow installs the locked `uv` environment and Chromium, logs the run's
vantage point, runs `PYTHONPATH=. uv run python workflows/pipeline.py`, and
uploads `audit.output`, `latest_audit_reports`, and `README.md` even when the
audit fails.

After a successful run the refreshed `README.md` and `latest_audit_reports`
are committed to `main` directly, matching the uptime workflow. This keeps the
published dashboard's `last_audit` date current without a manually merged
generated report PR. Disable the direct push by dispatching the workflow with
`push_reports=false` (for example when ran as a local smoke test).

The workflow grants `contents: write` (required for the direct push) and has a
concurrency lock and a 120-minute timeout. A failed run does not push any
report changes to `main`.

## Local workflow execution

`nektos/act` runs GitHub Actions jobs locally in Docker. Install Docker and
`act` using the instructions for your operating system, then inspect the
workflow with:

```bash
scripts/actions-validation.sh validate
scripts/actions-validation.sh list
```

The `validate` command uses `actionlint` for GitHub expression and runner-label
checks, then uses `wrkflw` for a second workflow parser. `wrkflw` is useful for
quick local validation and emulation, but it does not reproduce GitHub
permissions or concurrency behavior, so it is not an execution substitute for
the real GitHub-hosted runner.

Run the workflow locally against one URL with PR creation disabled:

```bash
MAX_URLS=1 scripts/actions-validation.sh run
```

The script also skips the first-time Chromium download and artifact
upload; this is a workflow smoke test, not a browser audit. It dispatches with
`push_reports=false` so a local run never pushes to `main`. The
artifact action's local server is not compatible with this `act` setup. Use
the direct fallback below to exercise the real browser-based audit locally:

```bash
MAX_URLS=1
uv sync --locked
uv run playwright install chromium
PYTHONPATH=. uv run python workflows/pipeline.py --max-urls "$MAX_URLS"
```

Omit `--max-urls` for a full audit.

The local command mirrors the workflow's GitHub-hosted runner with a local
Docker image (`node:20-bookworm-slim` by default) and starts a local artifact
server. The audit and uptime pipelines run from the runner's vantage point;
the GitHub-hosted runner is not a Sri Lankan vantage point, and neither is
a local Docker image unless it is itself running on a Sri Lankan machine.

The script deliberately runs `act` without `gh` on its `PATH`. This avoids
an `act` authentication bug where a GitHub Enterprise or stale `gh` token is
sent while cloning public Actions. Override `ACT_PATH` when a different local
tool layout is required.

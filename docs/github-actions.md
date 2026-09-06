# GitHub Actions

## Sri Lankan audit runner

The audit workflow runs only on a self-hosted runner with all three labels:

```text
self-hosted, linux, sri-lanka
```

The workflow is manually dispatched for now. It does not run on pull requests,
so code from an untrusted fork is never sent to the Sri Lankan runner. A weekly
schedule should be enabled only after a limited manual run has proved reliable.

Create the runner from the repository's **Settings > Actions > Runners** page.
Register it with the `sri-lanka` custom label and use a dedicated machine or
account with no unrelated credentials. GitHub warns that self-hosted runners
should be treated as trusted infrastructure, especially for public repositories.

The runner account needs read/write access to its checkout and permission to
run Docker-free Python and Playwright Chromium. The standard Linux service
commands are:

```bash
./svc.sh install
./svc.sh start
./svc.sh status
```

Runner diagnostics are stored in the runner directory under `_diag`. Service
logs can be inspected with `journalctl` using the service name printed by
`./svc.sh status`. Keep the runner application current by downloading the
release offered by the repository's runner settings page and restarting the
service after the upgrade.

Dispatch a limited run from the Actions page with `max_urls=1` first. The
workflow installs the locked `uv` environment and Chromium, runs
`PYTHONPATH=. uv run python workflows/pipeline.py`, uploads `audit.output`, `latest_audit_reports`, and
`README.md` even when the audit fails, and opens a report pull request only
after a successful run.

The workflow grants only `contents: write` and `pull-requests: write`, which
are required for the report pull request. It has a concurrency lock and a
120-minute timeout. A failed run does not create a pull request or push report
changes directly to `main`.

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
permissions or concurrency behavior, so it is not the execution substitute for
the real self-hosted runner.

Run the workflow locally against one URL with PR creation disabled:

```bash
MAX_URLS=1 scripts/actions-validation.sh run
```

The script also skips the first-time Chromium download, artifact upload,
and PR creation; this is a workflow smoke test, not a browser audit. The
artifact action's local server is not compatible with this `act` setup. Use
the direct fallback below to exercise the real browser-based audit locally:

```bash
MAX_URLS=1
uv sync --locked
uv run playwright install chromium
PYTHONPATH=. uv run python workflows/pipeline.py --max-urls "$MAX_URLS"
```

Omit `--max-urls` for a full audit.

The local command maps the workflow's `self-hosted` runner label to
`node:20-bookworm-slim` by default and starts a local artifact server. Docker uses the host's network path, so this
checks workflow wiring and local dependencies; it is only a Sri Lankan vantage
point when Docker is running on the Sri Lankan machine. It does not reproduce
GitHub's hosted-runner geography.

The script deliberately runs `act` without `gh` on its `PATH`. This avoids
an `act` authentication bug where a GitHub Enterprise or stale `gh` token is
sent while cloning public Actions. Override `ACT_PATH` when a different local
tool layout is required.

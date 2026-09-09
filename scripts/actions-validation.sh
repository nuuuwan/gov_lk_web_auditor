#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW="$ROOT_DIR/.github/workflows/audit.yml"
ACT="${ACT:-$(command -v act || true)}"
ACT_IMAGE="${ACT_IMAGE:-node:20-bookworm-slim}"
ACT_PATH="${ACT_PATH:-/usr/local/bin:/usr/bin:/bin}"
ACT_ARTIFACTS="${ACT_ARTIFACTS:-$ROOT_DIR/.act/artifacts}"

usage() {
    printf 'Usage: %s <validate|list|run>\n' "$0"
}

validate() {
    actionlint "$ROOT_DIR/.github/workflows/"*.yml
    wrkflw validate "$ROOT_DIR/.github/workflows/"*.yml
}

list_workflows() {
    [[ -n "$ACT" ]] || { printf 'act is required\n' >&2; exit 1; }
    "$ACT" -l -W "$WORKFLOW"
}

run_smoke_test() {
    [[ -n "$ACT" ]] || { printf 'act is required\n' >&2; exit 1; }
    mkdir -p "$ACT_ARTIFACTS"
    PATH="$ACT_PATH" GIT_CONFIG_GLOBAL=/dev/null "$ACT" workflow_dispatch \
        -W "$WORKFLOW" \
        -P "self-hosted=$ACT_IMAGE" \
        --input "max_urls=${MAX_URLS:-0}" \
        --input create_pr=false \
        --input skip_browser=true \
        --input skip_artifacts=true \
        --artifact-server-path "$ACT_ARTIFACTS"
}

[[ $# -eq 1 ]] || { usage >&2; exit 2; }

case "$1" in
    validate)
        validate
        ;;
    list)
        list_workflows
        ;;
    run)
        run_smoke_test
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac

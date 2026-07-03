#!/usr/bin/env bash
# check_changed.sh — Run tests relevant to changed files
#
# Usage:
#   ./scripts/check_changed.sh          # Check changes against main
#   ./scripts/check_changed.sh --all     # Run ALL tests
#   ./scripts/check_changed.sh --staged  # Check staged changes only
#
# Exit codes:
#   0 — All checks passed
#   1 — One or more checks failed

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

FAILED=0

# ── Helpers ──────────────────────────────────────────────────────────

run_check() {
    local name="$1"
    shift
    echo "━━━ [CHECK] $name ━━━"
    if "$@" 2>&1; then
        echo "  ✅ $name passed"
    else
        echo "  ❌ $name FAILED (exit code $?)"
        FAILED=1
    fi
    echo ""
}

get_changed_files() {
    if [ "${CHECK_ALL:-}" = "1" ]; then
        # Return everything (used with --all)
        echo "backend/app/core/ backend/app/stores/ backend/app/runners/ backend/app/installer/ backend/app/api/ backend/app/schemas/ src/ src-tauri/"
        return
    fi

    local base="${1:-main}"
    local files
    if [ "${CHECK_STAGED:-}" = "1" ]; then
        files=$(git diff --cached --name-only --diff-filter=ACMR)
    else
        files=$(git diff "$base" --name-only --diff-filter=ACMR 2>/dev/null || git diff HEAD --name-only --diff-filter=ACMR 2>/dev/null || echo "")
    fi
    echo "$files"
}

# ── Feature-to-Test Mappings ─────────────────────────────────────────

# Each function checks if any changed file matches its path prefix.
# If so, it runs the relevant tests.

check_core_domain() {
    local files="$1"
    if echo "$files" | grep -qE "^backend/app/core/|^backend/tests/(domain|core|repositories|use_cases)/"; then
        run_check "Core/Domain tests" uv run pytest tests/domain/ tests/core/ tests/repositories/ tests/use_cases/ -v --tb=short
    fi
}

check_stores() {
    local files="$1"
    if echo "$files" | grep -qE "^backend/app/stores/|^backend/tests/stores/"; then
        run_check "Store integration tests" uv run pytest tests/stores/ -v --tb=short
    fi
}

check_runners() {
    local files="$1"
    if echo "$files" | grep -qE "^backend/app/runners/|^backend/tests/runners/"; then
        run_check "Runner tests" uv run pytest tests/runners/ -v --tb=short
    fi
}

check_installer() {
    local files="$1"
    if echo "$files" | grep -qE "^backend/app/installer/|^backend/tests/installer/"; then
        run_check "Installer tests" uv run pytest tests/installer/ -v --tb=short
    fi
}

check_api() {
    local files="$1"
    if echo "$files" | grep -qE "^backend/app/api/|^backend/tests/api/|^backend/app/schemas/"; then
        run_check "API integration tests" uv run pytest tests/api/ -v --tb=short
    fi
}

check_backend_lint() {
    local files="$1"
    if echo "$files" | grep -qE "^backend/"; then
        run_check "Backend lint (ruff)" uv run ruff check .
        run_check "Backend types (mypy)" uv run mypy .
    fi
}

check_frontend() {
    local files="$1"
    if echo "$files" | grep -qE "^src/|^src-tauri/"; then
        run_check "Frontend typecheck" npx tsc --noEmit
        run_check "Frontend lint" npx eslint src/
        run_check "Frontend test" npx vitest run
        run_check "Frontend build" npx vite build
    fi
}

check_tauri() {
    local files="$1"
    if echo "$files" | grep -qE "^src-tauri/"; then
        run_check "Tauri cargo check" cargo check --manifest-path src-tauri/Cargo.toml
    fi
}

# If only tauri changed, skip backend
check_all_backend() {
    local files="$1"
    if echo "$files" | grep -qE "^backend/"; then
        run_check "All backend tests" uv run pytest -v --tb=short
    fi
}

# ── Main ─────────────────────────────────────────────────────────────

# Parse args
CHECK_ALL=0
CHECK_STAGED=0
while [ $# -gt 0 ]; do
    case "$1" in
        --all) CHECK_ALL=1 ;;
        --staged) CHECK_STAGED=1 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

echo "═══════════════════════════════════════════════════════════════"
echo "  New Heroic — Feature Check"
echo "═══════════════════════════════════════════════════════════════"

if [ "$CHECK_ALL" = "1" ]; then
    echo "  Mode: ALL tests"
    FILES="backend/app/core/ backend/app/stores/ backend/app/runners/ backend/app/installer/ backend/app/api/ backend/app/schemas/ src/ src-tauri/"
elif [ "$CHECK_STAGED" = "1" ]; then
    echo "  Mode: Staged changes only"
    FILES=$(get_changed_files)
else
    echo "  Mode: Changed files (vs main)"
    FILES=$(get_changed_files)
fi

if [ -z "$FILES" ]; then
    echo "  No changes detected. Nothing to check."
    exit 0
fi

echo ""
echo "  Changed areas:"
echo "$FILES" | tr ' ' '\n' | sed 's/^/    /'

echo ""
echo "───────────────────────────────────────────────────────────────"
echo "  Running relevant checks..."
echo "───────────────────────────────────────────────────────────────"
echo ""

cd backend

# Run specific feature tests first
check_core_domain "$FILES"
check_stores "$FILES"
check_runners "$FILES"
check_installer "$FILES"
check_api "$FILES"
check_backend_lint "$FILES"

cd "$ROOT_DIR"

# Frontend checks
check_frontend "$FILES"
check_tauri "$FILES"

echo "═══════════════════════════════════════════════════════════════"
if [ "$FAILED" -eq 0 ]; then
    echo "  ✅ ALL CHECKS PASSED"
else
    echo "  ❌ SOME CHECKS FAILED — fix before proceeding"
fi
echo "═══════════════════════════════════════════════════════════════"

exit "$FAILED"

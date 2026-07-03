.PHONY: help setup dev backend frontend lint typecheck test check check-feature check-all build clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies
	cd backend && uv sync
	npm install
	cargo install tauri-cli --version "^2" --locked

dev: ## Run both backend and frontend in dev mode
	@echo "Starting backend and frontend..."
	@$(MAKE) -j2 backend frontend

backend: ## Start the FastAPI backend dev server
	cd backend && PATH=".venv/bin:$$PATH" uv run uvicorn app.main:app --reload --host 127.0.0.1 --port $(or $(BACKEND_PORT),1430)

frontend: ## Start the Tauri dev server (WEBKIT_DISABLE_COMPOSITING_MODE=1 fixes Wayland GBM blank window)
	WEBKIT_DISABLE_COMPOSITING_MODE=1 cargo tauri dev

lint: ## Run all linters
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .
	npm run lint

typecheck: ## Run type checking
	cd backend && uv run mypy .
	npm run typecheck

test: ## Run all tests
	cd backend && uv run pytest
	npm run test

check: ## Run full verification suite (lint + types + tests + build)
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "  New Heroic — Full Verification Suite"
	@echo "═══════════════════════════════════════════════════════════════"
	@echo ""
	@echo "━━━ Phase 1: Backend lint ━━━"
	cd backend && uv run ruff check . || exit 1
	@echo ""
	@echo "━━━ Phase 2: Backend types ━━━"
	cd backend && uv run mypy . || exit 1
	@echo ""
	@echo "━━━ Phase 3: Backend tests ━━━"
	cd backend && uv run pytest -v --tb=short || exit 1
	@echo ""
	@echo "━━━ Phase 4: Frontend typecheck ━━━"
	npm run typecheck || exit 1
	@echo ""
	@echo "━━━ Phase 5: Frontend lint ━━━"
	npm run lint || exit 1
	@echo ""
	@echo "━━━ Phase 6: Frontend test ━━━"
	npm run test || exit 1
	@echo ""
	@echo "━━━ Phase 7: Frontend build ━━━"
	npm run build || exit 1
	@echo ""
	@echo "━━━ Phase 8: Tauri cargo check ━━━"
	cargo check --manifest-path src-tauri/Cargo.toml || exit 1
	@echo ""
	@echo "═══════════════════════════════════════════════════════════════"
	@echo "  ✅ ALL CHECKS PASSED"
	@echo "═══════════════════════════════════════════════════════════════"

check-feature: ## Run checks for changed files only (vs main)
	@bash scripts/check_changed.sh

check-all: ## Run all feature-specific checks
	@bash scripts/check_changed.sh --all

build: ## Build for production
	cd backend && pyinstaller --onefile --name backend-server app/main.py
	mv dist/backend-server src-tauri/binaries/backend-server-$(shell rustc --print host-tuple)
	cargo tauri build

clean: ## Clean all build artifacts
	rm -rf dist/
	rm -rf src-tauri/target/
	rm -rf backend/__pycache__
	rm -rf .pytest_cache/
	rm -rf node_modules/

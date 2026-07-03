# AGENTS.md — New Heroic Game Launcher

## Project Identity

A modern open-source game launcher combining the best of Lutris and Heroic Games Launcher.
Linux-first, cross-platform ready. GPLv3.

## Tech Stack (non-obvious)

| Layer | Technology | Note |
|-------|-----------|------|
| Desktop shell | **Tauri v2** | NOT Electron. Tauri wraps the frontend. |
| Frontend | React + TypeScript + Tailwind | Inside Tauri webview |
| Backend | **Python + FastAPI** | Runs as a sidecar process, NOT Rust backend |
| Plugin system | Python entry points | Plugins are Python packages, not JS/TS |
| Store CLI tools | Legendary (Epic), gogdl (GOG) | Called as subprocesses by the Python backend |

**Critical**: Tauri's native backend is Rust, but this project uses Tauri only as a shell.
All business logic lives in the Python/FastAPI sidecar. The Tauri Rust layer is a thin
bridge (IPC to Python). Do NOT put business logic in Rust.

## Architecture Rules

- **Clean Architecture** — domain logic never imports infrastructure
- **SOLID** — every class/module has one reason to change
- **Dependency Injection** — use `dependency-injector` or similar; no global singletons
- **DDD where appropriate** — aggregates, value objects, domain events for complex domains (game library, runner management)
- **Plugin architecture** — stores, runners, and installers are plugins loaded via entry points
- **Every feature must be independently testable** — no feature depends on another feature's internals

## Module Map

```
backend/
  core/          — Domain models, interfaces, use cases, game settings (NO external deps)
  runners/       — Wine, Proton, Native runners + WineManager (download Wine-GE/Proton-GE)
  stores/        — Epic (Legendary), GOG (gogdl), Steam (import), itch.io
  installer/     — YAML installer engine (Lutris-inspired)
  diagnostics/   — [NOT YET IMPLEMENTED] Log parsing, error detection
  updates/       — [NOT YET IMPLEMENTED] Self-update, runner updates
  plugins/       — [NOT YET IMPLEMENTED] Plugin loader, entry point discovery
  api/           — FastAPI routes, schemas, middleware (health, games, stores, runners, wine, installer, game_settings)
  schemas/       — Pydantic v2 schemas for all API endpoints
  models/        — Future SQLAlchemy models
frontend/
  src/
    components/  — GameCard, BackendStatus
    pages/       — Dashboard (library), SettingsPage, GameDetailPage
    hooks/       — useBackendHealth
    lib/         — API client (api.ts)
```

## Development Workflow (MANDATORY ORDER)

1. Analyze requirements → update docs
2. Design architecture → design APIs
3. Write tests (TDD) for the specific feature
4. Implement the feature
5. **Run feature-specific tests** → `make check-feature`
6. **If any test fails** → fix → retry step 5
7. **Run full verification suite** → `make check`
8. Only proceed to next feature if ALL checks pass (exit code 0)

**Critical rule: Never skip step 6.** A failing test blocks the next feature.
The CI gate job enforces this automatically on every push.

### Quick Check Commands

| Command | What it does |
|---------|-------------|
| `make check` | Full 8-phase suite (backend lint → types → tests → frontend typecheck → lint → test → build → cargo check) |
| `make check-feature` | Smart check: detects changed files vs main, runs only relevant tests |
| `make check-all` | Runs all feature-specific checks (same as CI) |
| `bash scripts/check_changed.sh --staged` | Check staged changes before commit |

## Milestone-Based Development

This is a long-term project. Never attempt to build everything at once.
Work milestone by milestone. Each milestone must be:
- Self-contained and shippable
- Fully tested
- Fully documented
- Reviewed before moving to the next

## Quality Gates (per feature)

- [ ] Unit tests (pytest for backend, vitest for frontend)
- [ ] Integration tests where modules cross boundaries
- [ ] Type hints (Python) / TypeScript strict mode
- [ ] Structured logging (structlog)
- [ ] Docstrings on all public APIs
- [ ] Comments ONLY when code is non-obvious — prefer self-documenting code

## Key Conventions

- Python: `snake_case` for everything except class names (`PascalCase`)
- TypeScript: `camelCase` for variables/functions, `PascalCase` for components/classes
- File names: `snake_case.py` for Python, `PascalCase.tsx` for React components
- Git: conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- Branch naming: `feat/<name>`, `fix/<name>`, `docs/<name>`

## Installer System (YAML)

Installers are YAML files inspired by Lutris. They describe:
- Dependencies to download
- Wine configuration
- Redistributable installation
- Environment variables
- Launcher setup

The installer engine is in `backend/installer/`. Do NOT hardcode installer logic
in store or runner modules.

## Store Integrations

| Store | Tool | Type | Status |
|-------|------|------|--------|
| Epic Games | Legendary | CLI subprocess | ✅ Working — 505 games synced |
| GOG | gogdl | CLI subprocess | ✅ CLI installed, auth flow ready |
| Steam | — | Import only | ❌ Not implemented |
| itch.io | — | TBD | ❌ Not implemented |

Adding a new store means creating a plugin in `backend/stores/` that implements
the store interface. Do NOT modify core to add a store.

## Diagnostics Engine (NOT YET IMPLEMENTED)

Planned: Reads Wine/debug logs, detects patterns (missing DLLs, Vulkan issues, driver problems,
permission errors), and suggests fixes. Diagnostics must NEVER mutate system state — only report and suggest.

## Current State

**All 6 Milestones complete** (June 2026). The project is a fully functional game launcher with:
- 182 backend tests (24 test files), 55 Python modules
- 11 frontend TS/TSX files
- Epic Games authenticated with 505 games synced in library
- Full stack verification: ruff → mypy → pytest → tsc → ESLint → Vite build → cargo check

### ✅ Delivered (Milestone 1) — Scaffolding & IPC PoC
- Tauri v2 + React 19 + TypeScript 5 + Tailwind CSS v4 frontend
- Python FastAPI backend with modular structure (api/, core/, models/, schemas/)
- Health check endpoint (`GET /api/health`) with typed response
- Frontend health widget with loading, error, and retry states
- Dependency injection container (dependency-injector)
- Structured logging (structlog)
- CI/CD pipeline (GitHub Actions: lint → typecheck → test → build)
- Python dev toolchain (ruff, mypy, pytest, uv)
- Frontend dev toolchain (ESLint, Vitest, TypeScript strict mode)

### ✅ Delivered (Milestone 2) — Core Domain Model
- **Domain model**: Game and Library aggregates with DDD patterns (entities, value objects, 8 domain events, status state machine)
- **Repository layer**: GameRepository and LibraryRepository interfaces (typing.Protocol) + InMemory implementations
- **Use cases**: LibraryUseCases with 9 operations (add, install, launch, close, uninstall, etc.)
- **REST API**: 10 endpoints (libraries CRUD, game CRUD, game actions)
- **DD Wiring**: dependency-injector container updated with repositories and use cases
- **Tests**: 87 tests across domain, repositories, use cases, and API integration
- **Clean Architecture**: domain (core/) has zero external dependencies — verified against all 5 Laws

### ✅ Delivered (Milestone 3) — Store Integrations
- StoreBase ABC with async subprocess helpers (_run_command, check_installed)
- EpicStore wrapping Legendary CLI (auth, status, list-games, info, install)
- GOGStore wrapping gogdl CLI (auth, status, list, info, install)
- StoreManager registry with register/get/list_available/create_default
- Structlog logging added to all stores and manager
- 111 tests total (store unit + API integration)

### ✅ Delivered (Milestone 4) — Runner Management
- RunnerBase ABC with detect(), run_game(), get_settings(), set_setting()
- NativeRunner (always available on Linux, direct exec)
- WineRunner (detects wine64/wine via which, WINEPREFIX/WINEARCH config)
- ProtonRunner (scans Steam compatibility tools directories)
- RunnerManager registry with detect_all() and create_default()
- 3 API endpoints: GET /api/runners, GET /api/runners/detect, GET /api/runners/{name}/detect
- 125 tests total

### ✅ Delivered (Milestone 5) — Installer System (YAML)
- InstallerFile, InstallerStep, InstallerManifest typed dataclasses
- YAML parser → typed InstallerManifest
- Step handlers: download, extract, execute, mkdir, chmodx, require
- Sequential executor with progress tracking and cancellation support
- InstallerManager registry for parse/run/cancel
- 2 API endpoints: POST /api/installer/parse, POST /api/installer/install
- 142 tests total

### ✅ Delivered (Milestone 6) — Frontend UI (Heroic-style)
- Heroic-style icon sidebar (Library/Settings navigation)
- Unified game library with filter pills (All/Installed/Not Installed/Epic/GOG/Local)
- Search bar, sync buttons with spinners, responsive 3:4 game card grid
- Game cards with store badges, status badges, hover action overlays
- Settings page: Store Accounts login UI (browser-based OAuth), Wine Manager, Runners detection, About
- Game Detail page with hero section, action buttons, 4 settings tabs
- 182 tests total (incl. backend)

### ✅ Post-Milestone Features

**Browser-based OAuth Login:**
- Epic Games: browser auth URL → instructions → code/sid input → connect
- GOG: same flow with GOG OAuth URL
- Endpoints: GET /api/stores/{name}/auth-url, POST /api/stores/{name}/auth, GET /api/stores/{name}/status
- Smart auth code detection: 32-char alphanumeric → tries --code first, falls back to --sid

**Wine Manager:**
- Downloads Wine-GE, Proton-GE, Lutris-Wine from GitHub releases
- Progress tracking: Content-Length via HEAD request, real percentage, speed_mbps, downloaded_mb/total_mb
- Install, delete, list available/installed versions
- 5 API endpoints under /api/wine/

**Per-Game Settings:**
- 17 config fields: runner, wine_version, wine_prefix, wine_arch, args, env_vars, DXVK/VKD3D/FSR toggles, FSR quality, GameMode, MangoHud, steam_runtime, pre_launch_command, post_exit_command
- Clean Architecture: GameSettings dataclass (core/) + GameSettingsStore JSON persistence (infrastructure)
- 2 API endpoints: GET/PUT /api/games/{id}/settings
- 4 UI tabs: General, Advanced (args + env vars), Compatibility (DXVK/VKD3D/FSR), System (GameMode/MangoHud)

**Epic Store Authentication & Sync:**
- Legendary v0.20.34 installed (pip) and authenticated as user "RJ76_VE"
- gogdl v1.2.2 installed from GitHub (Heroic-Games-Launcher/heroic-gogdl)
- 505 Epic games synced into library via POST /api/stores/epic/sync
- Backend must be started with venv/bin on PATH for CLI tool detection

### Verification
All 8 verification checks pass:
`ruff check .` (Python lint) → `mypy .` (Python types) → `pytest -v` (182 tests) →
`tsc --noEmit` (TypeScript) → `npm run lint` (ESLint) → `npm run build` (Vite) → `cargo check` (Tauri)

## IPC Architecture

```
Frontend (port 1420) ──HTTP──► FastAPI Backend (port 1430)
       │                          │
       │ Tauri shell (thin Rust)  │
       └── launches sidecar ──────┘
```

- **Dev mode**: Run backend (`make backend`) and frontend (`make frontend`) in separate terminals
- **Production**: Python bundles to PyInstaller binary, Tauri spawns it as sidecar process
- Frontend never talks to Rust code directly — all business logic goes through the Python API

### Port Management
| Component | Default Port | Config Location |
|-----------|-------------|-----------------|
| Frontend (Vite) | 1420 | `vite.config.ts` |
| Backend (FastAPI) | 1430 | `backend/.env` → `BACKEND_PORT` |
| Frontend→Backend URL | 1430 | `.env` → `VITE_BACKEND_URL` |

### CORS Configuration
The FastAPI backend uses `CORSMiddleware` with origins configured in `backend/.env`:
- `http://localhost:1420` — Vite dev server (development)
- `tauri://localhost` — Tauri webview origin (production)

In production, the Tauri webview uses `tauri://localhost` as its origin (not `http://localhost`).
Both origins must be allowed for the health check and all API calls to work in both environments.
CSP is set to `null` in `tauri.conf.json` to allow unrestricted connections during development.

## CI/CD Pipeline

The CI pipeline (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

### Jobs

| Job | What it checks | Runs when |
|-----|---------------|-----------|
| `frontend` | TypeScript → ESLint → Vitest → Vite build | Always |
| `backend-lint` | Ruff + mypy | Always |
| `backend-core` | Domain, core, repo, use case tests | Always |
| `backend-stores` | Store integration tests | Always |
| `backend-runners` | Runner tests | Always |
| `backend-installer` | Installer engine tests | Always |
| `backend-api` | API integration tests | Always |
| `tauri` | Cargo check | Always |
| `gate` | **Aggregator** — passes only if ALL jobs pass | After all jobs |

### Gate Job

The `gate` job waits for all 8 preceding jobs and checks each result explicitly.
If ANY job fails, the gate fails — blocking the PR from merging.

### Local Equivalent

Before pushing, run `make check` locally. This runs the same 8 phases
as the CI pipeline (minus parallelism) and must exit with code 0.

## Server Management

### Running Locally
```bash
# Terminal 1 — Backend (with venv PATH for CLI tools)
cd backend
PATH=".venv/bin:$PATH" .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 1430

# Terminal 2 — Frontend (Vite dev server)
npm run dev
```

### Important
- **PATH requirement**: The backend venv `bin/` directory must be on `PATH` for Legendary/gogdl CLI detection
- **Server won't reload automatically**: Use `--reload` for development but be aware that Python file changes may trigger reloader exit instead of restart
- **In-memory storage**: Data is lost on restart (no database yet). Use `POST /api/stores/{name}/sync` to re-import games after restart

## Lessons Learned (Scaffolding)

### Tauri v2 Config Gotchas
- `app.title` is NOT a valid field — window title only belongs inside the `windows[]` array
- Icon files listed in `bundle.icon` MUST exist at compile time or `cargo check` fails
- `bundle.externalBin` binaries MUST have `-TARGET_TRIPLE` suffix (e.g., `backend-server-x86_64-unknown-linux-gnu`) and must exist at compile time
- The `tsconfig.node.json` needs `composite: true` to work with project references from the main tsconfig
- The `@tailwindcss/vite` plugin replaces PostCSS config — do NOT create `postcss.config.js` or `tailwind.config.js` for Tailwind v4

### Verification Order
Run in this exact order for fastest feedback:
1. `ruff check .` (Python lint — fastest)
2. `tsc --noEmit` (TypeScript — catches structural issues)
3. `npm run test` / `pytest` (unit tests)
4. `cargo check` (Tauri Rust — slowest, run last)

### Post-Milestone Gotchas

- **CORS with 127.0.0.1**: Browsers treat `localhost` and `127.0.0.1` as different origins. Both must be in `cors_origins` if the frontend serves on 127.0.0.1.
- **Epic OAuth tokens are extremely short-lived**: authorizationCode expires in ~30-60 seconds. Must be consumed immediately.
- **Legendary `--auth-code` vs `--code`**: The Legendary flag is `--code` (not `--auth-code`). SIDs use `--sid`.
- **is_authenticated sentinel**: Legendary status returns `"account": "<not logged in>"` as a string when not authenticated. Check with `not in (None, "<not logged in>")` instead of `is not None`.
- **legendary `list-games` JSON key**: The app title is under `app_title`, not `title`.
- **Shared in-memory store bug**: When two API modules create separate `get_use_cases()` singletons, they get separate in-memory repositories. Fix: use a shared `dependencies.py` module.
- **Backend crash on --reload**: Uvicorn's `--reload` can fail to restart if an import error occurs during file change. Use `nohup` or a process manager for production-like sessions.

### Feature Check Workflow

- **Always run `make check-feature` after implementing a feature** — it detects changed files and runs only relevant tests
- **Always run `make check` before committing** — full verification suite
- **If `make check` fails, investigate immediately** — don't start the next feature
- **The CI gate job mirrors `make check`** — if it passes locally, CI will pass too

### Common Fixes
- **TypeScript `tsconfig.node.json` errors**: Add `"composite": true, "noEmit": false`
- **Tauri `cargo check` failures**: Check `tauri.conf.json` schema compatibility with installed `tauri-build` version
- **Python `mypy` on conftest.py**: Add type annotations to fixture return types
- **CORS issues**: The backend allows `http://localhost:1420` and `tauri://localhost` — add more origins in `app/core/config.py` if needed

### Package Management
- **Frontend**: npm (lockfile: `package-lock.json`)
- **Backend**: uv (lockfile: `backend/uv.lock`)
- **Rust**: cargo (lockfile: `src-tauri/Cargo.lock`)

## References

- Project spec: see the full brief in the repo's initial commit or project docs
- OpenCode config: `.opencode/opencode.jsonc`
- License: `LICENSE` (GPLv3)

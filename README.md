# New Heroic

A modern open-source game launcher combining the best features of Lutris and Heroic Games Launcher.

Linux-first, cross-platform ready.

## Tech Stack

- **Desktop Shell**: Tauri v2
- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Python + FastAPI (sidecar process)
- **License**: GPLv3

## Development

### Prerequisites

- Rust (via rustup)
- Node.js 20+
- Python 3.11+ with [uv](https://docs.astral.sh/uv/)
- System deps: `libwebkit2gtk-4.1-dev` (Ubuntu/Debian)

### Quick Start

```bash
# Install all dependencies
make setup

# Run development servers (backend + frontend)
make dev
```

### Commands

| Command | Description |
|---------|-------------|
| `make setup` | Install all dependencies |
| `make dev` | Run backend + frontend in dev mode |
| `make backend` | Start backend only |
| `make frontend` | Start frontend only |
| `make lint` | Run all linters |
| `make typecheck` | Run type checking |
| `make test` | Run all tests |
| `make build` | Build for production |
| `make clean` | Clean build artifacts |

### Architecture

The Tauri shell wraps a React + TypeScript frontend. A Python FastAPI backend runs as a Tauri sidecar process, communicating via HTTP on `localhost:1430`.

```
┌──────────────────────────────────────────┐
│               Tauri Shell                 │
│  ┌──────────┐    HTTP    ┌──────────────┐│
│  │  React    │ ◄────────► │  FastAPI     ││
│  │  Frontend │            │  Backend     ││
│  └──────────┘            └──────────────┘│
└──────────────────────────────────────────┘
```

## License

GNU General Public License v3.0

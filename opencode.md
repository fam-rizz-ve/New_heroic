# New Heroic — OpenCode Workflow Instructions

## Dopo Ogni Feature Completata

1. **Esegui verifica locale completa:**
   ```bash
   cd /home/andrea/Progetti/New_heroic
   make check
   ```
   `make check` esegue tutte 8 fasi: ruff → mypy → pytest → tsc → ESLint → vitest → vite build → cargo check.
   Se una fase fallisce, fermati e fixa prima di procedere.

2. **Fai git push per triggerare GitHub Actions:**
   ```bash
   git push origin main
   ```
   Il push attiva automaticamente la CI pipeline su GitHub Actions con 9 job:
   - frontend (typecheck + lint + test + build)
   - backend-lint (ruff + mypy)
   - backend-core (domain/repo/use case tests)
   - backend-stores (store integration tests)
   - backend-runners (runner tests)
   - backend-installer (installer tests)
   - backend-api (API integration tests)
   - tauri (cargo check)
   - gate (aggregator — passa solo se TUTTI i job precedenti passano)

3. **Leggi i risultati di GitHub Actions:**
   - Vai su https://github.com/AndreaDeLucia/New_heroic/actions
   - Controlla che il workflow più recente sia passato (✅ verde)
   - Se il `gate` job è verde, tutto ok

4. **Se il gate fallisce:**
   - Identifica quale job specifico è fallito (frontend, backend-lint, backend-core, etc.)
   - Leggi i log dell'errore su GitHub Actions
   - Riproduci il problema localmente con il comando specifico (es. `cd backend && ruff check .`)
   - Fixa il problema
   - Torna al passo 1 (verifica locale con `make check`)
   - Torna al passo 2 (git push)

5. **Se tutti i test passano:**
   - La feature è completa e verificata
   - Procedi alla prossima feature

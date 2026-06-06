# Tasks: Proyecto Setup — Scaffold TiendaVirtual

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 450–500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Dev env → Backend core → Frontend core |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Base | Lines | Notes |
|------|------|-----------|------|-------|-------|
| 1 | Dev environment scaffold | PR #1 | main | ~105 | `docker-compose.yml`, `.gitignore`, `README.md` |
| 2 | Backend core scaffold | PR #2 | main | ~177 | pyproject.toml, app package, DB engine, Alembic |
| 3 | Frontend core scaffold | PR #3 | main | ~200 | Angular 22, Material, Tailwind v3, i18n, layout |

## Phase 1: Dev Environment

- [ ] 1.1 Create `docker-compose.yml` with postgres:16 (named volume pgdata), backend (build ./backend, volume mount `./backend:/app`, port 8000), frontend (node:24-slim, volume mount `./frontend:/app`, port 4200)
- [ ] 1.2 Create `.gitignore` excluding `.env`, `uploads/`, `__pycache__/`, `node_modules/`, `.venv/`, `.angular/`, `dist/`
- [ ] 1.3 Create `README.md` with "La Tiendita", stack table, prerequisites (Docker, Node 24+, Python 3.14+), `docker compose up` instructions

## Phase 2: Backend Core

- [ ] 2.1 Create `backend/pyproject.toml` (PEP 621 deps: litestar, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, uvicorn)
- [ ] 2.2 Create `backend/app/__init__.py` (empty) + `backend/app/main.py` (Litestar app, CORS `localhost:4200`, OpenAPI `/schema`, `GET /health`)
- [ ] 2.3 Create `backend/app/config.py` with `Settings(BaseSettings)` fields: DATABASE_URL, DEBUG, SECRET_KEY, CORS_ORIGINS
- [ ] 2.4 Create `backend/app/db/` package with `__init__.py` (empty), `engine.py` (create_async_engine + async_sessionmaker), `base.py` (DeclarativeBase)
- [ ] 2.5 Run `alembic init migrations --async`; edit `alembic.ini` + `migrations/env.py` to read URL from Settings

## Phase 3: Frontend Core

- [ ] 3.1 Scaffold: `ng new frontend --routing --style=scss` with `@angular/build` builder; add `pnpm-workspace.yaml` if needed
- [ ] 3.2 Install deps: `@angular/material@22` (indigo-pink theme), `tailwindcss@3`, `@ngx-translate/core@17` + http-loader, PostCSS
- [ ] 3.3 Create `tailwind.config.js` with `./src/**/*.{html,ts}` content paths; add `@tailwind` directives to `styles.scss`
- [ ] 3.4 Create `shared/shared.module.ts` re-exporting MatButtonModule, MatToolbarModule, MatIconModule, MatSidenavModule, MatListModule
- [ ] 3.5 Create `layout/header/` (app title + ngx-translate language selector) and `layout/footer/` (copyright year text)
- [ ] 3.6 Create `features/home/` placeholder; wire AppComponent shell: header → router-outlet → footer
- [ ] 3.7 Create `assets/i18n/{es,en,sv}.json` with `header.title`, `footer.copyright`; register TranslateModule + provideHttpClient + provideAnimations
- [ ] 3.8 Wire routes: lazy home route, wildcard `**` redirect to `/`; update `app.config.ts`

## Phase 4: Verification

- [ ] 4.1 Verify `pip install -e .` succeeds in backend/; imports: litestar, sqlalchemy, alembic
- [ ] 4.2 Verify `ng serve` compiles and renders at :4200 with Material + Tailwind styles
- [ ] 4.3 Verify `docker compose up` starts postgres:16 (5432), backend (:8000 /health → `{"status":"ok"}`), frontend (:4200)
- [ ] 4.4 Verify `alembic revision --autogenerate -m "init"` creates a migration under `migrations/versions/`
- [ ] 4.5 Verify `.env` is excluded from `git status`; verify `__pycache__/` and `node_modules/` are excluded

## Implement Order

PR #1 (dev-env) first — no dependencies. PR #2 (backend) needs the project root conventions from PR #1. PR #3 (frontend) is independent of backend but needs the root scaffold from PR #1. Each PR is under budget and merges directly to `main`.

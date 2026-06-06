# Proposal: Proyecto Setup — Scaffold TiendaVirtual

## Intent

Initialize the TiendaVirtual codebase from an empty directory. Scaffold Docker Compose dev environment, Litestar backend shell, and Angular frontend shell. Every downstream change depends on this foundation.

## Scope

### In Scope (~15 files)
- Docker Compose (PostgreSQL 16, Litestar dev, Angular dev)
- Backend: `pyproject.toml`, `app/main.py`, `app/config.py`, `app/db/engine.py`, `app/db/base.py`
- Backend: `alembic.ini` + migrations folder
- Frontend: Angular 22 CLI project, Angular Material, Tailwind v3 (pinned), ngx-translate
- Frontend: header/footer layout components + basic routing
- Git init: `.gitignore`, `README.md`

### Out of Scope
- Auth, models, schemas, controllers (Change 2+)
- Testing infrastructure (no code to test yet; add when Change 2 introduces models)
- CI/CD pipelines, production Dockerfiles
- Tailwind v4 migration (explicitly deferred)

## Capabilities

### New Capabilities
- `dev-environment`: Docker Compose stack (PostgreSQL 16, backend, frontend), git init, README
- `backend-core`: Litestar app shell, pydantic-settings config, async SQLAlchemy engine, Alembic migrations scaffold
- `frontend-core`: Angular 22 app shell, Angular Material, Tailwind v3, ngx-translate, header/footer layout, basic routing

### Modified Capabilities
None — first change in the project.

## Approach

**Version decisions** (resolved from exploration discrepancies):
- **Angular 22** — actual available version (PLAN.md says 18; update PLAN.md note). Uses new `@angular/build` application builder.
- **Tailwind v3 pinned** (`tailwindcss@3`) — PLAN.md explicitly assumes `tailwind.config.js`. v4 is CSS-first and incompatible with PLAN approach. Migration deferred.
- **Python 3.14** — verify `python-jose` and `httpx-oauth` install cleanly with `pip install --dry-run` before committing.
- **pnpm** — project package manager (per tooling rules).

**Docker Compose**: PostgreSQL 16 official image, Litestar with volume-mounted source for hot reload, Angular dev server via `ng serve`.

**Backend**: `python3 -m venv .venv` for isolation. Litestar with CORS (localhost:4200) + OpenAPI docs. `pydantic-settings` reads from `.env`. Async engine via `create_async_engine` + `async_sessionmaker`. Alembic initialized with `alembic init migrations --async`.

**Frontend**: `npx @angular/cli new frontend --routing --style=scss`. Add Material, ngx-translate, Tailwind v3. Create `HeaderComponent`, `FooterComponent`, `HomeComponent`. Module-based architecture with lazy-loaded routes.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `docker-compose.yml` | New | Dev stack definition (PostgreSQL, backend, frontend) |
| `backend/` | New | Full backend scaffold (~7 files) |
| `frontend/` | New | Angular 22 scaffold + layout components (~5 files) |
| `.gitignore` | New | Exclude `.env`, `uploads/`, `__pycache__`, `node_modules`, `.venv` |
| `README.md` | New | Project overview, stack, setup instructions |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| python-jose/httpx-oauth wheels fail on Python 3.14 | Medium | `pip install --dry-run` first; fallback to Python 3.12 in Docker container |
| Angular 22 application builder breaks Material/Tailwind integration | Low | Both officially compatible with v22; manual PostCSS config as fallback |
| Docker Compose v5 breaking changes | Low | v5 is backwards-compatible with v3 format compose files |

## Rollback Plan

Delete all created files. No data exists — no migrations applied, no database initialized. `rm -rf .git` reverses git init. No external services to tear down.

## Dependencies
- Docker + Docker Compose (verified: 29.5.2 / 5.1.4)
- Node.js 24+ + pnpm 10+ (verified: 26.2.0 / 11.1.1)
- Python 3.14+ with venv (verified: 3.14.5)
- npx @angular/cli (verified: 22.0.0, not globally installed)

## Success Criteria
- [ ] `docker compose up` starts PostgreSQL 16, Litestar dev server, Angular dev server
- [ ] Angular app loads at `localhost:4200` with header, footer, and working routing
- [ ] Litestar OpenAPI docs accessible at `localhost:8000/schema`
- [ ] Backend connects to PostgreSQL; `alembic revision --autogenerate` creates initial migration
- [ ] `.gitignore` excludes `.env`, `uploads/`, `__pycache__`, `node_modules`, `.venv`

# La Tiendita — AGENTS.md

Second-hand clothing e-commerce: async Python **Litestar** API + **Angular 22** SPA (standalone components, signals, PrimeNG, Tailwind v3, ngx-translate) + PostgreSQL 16 + Redis 7 (cache + ARQ queue). Dev and prod run via Docker Compose; prod adds nginx (port 80).

## Commands

Backend (workdir `backend/`):
- Install: `pip install -e ".[dev]"`
- Run API: `uvicorn app.main:app --reload --port 8000` — requires Postgres + Redis running (or `docker compose up` for them)
- Tests: `python -m pytest` — `test_*_integration.py` hit a real DB (default `DATABASE_URL` set in `tests/conftest.py`, `tiendita_dev`); ~28 tests auto-skip when services are absent
- Seed catalog: `python scripts/seed_real.py` (300 real products, 3-language translations)

Frontend (workdir `frontend/`):
- Install: `pnpm install` (pnpm 11 — never npm)
- Run: `pnpm start` (`ng serve`; proxies `/api`, `/auth`, `/uploads` → `localhost:8000` via `proxy.conf.json`)
- Unit: `pnpm test` — vitest-based `@angular/build:unit-test` runner (no browser); CI form: `pnpm test -- --watch=false`
- Build: `pnpm run build` (prod build works; no typecheck/lint step in CI)
- E2E: `pnpm test:e2e` — Playwright (`frontend/tests/`, desktop/tablet/mobile projects, baseURL `localhost:4200`). Does NOT auto-start servers: backend + frontend dev must already be up.

CI parity (`.github/workflows/ci.yml`): backend pytest against `postgres:16-alpine` (env `DATABASE_URL`, `SECRET_KEY`); frontend production build + unit tests. Keep local verification to the same shape.

Graphify (knowledge graph, workdir repo root):
- Regenerate full graph (AST + LLM semantic): `graphify extract . --backend glm-coding` (uses GLM Coding Plan via `ZAI_API_KEY`; ~75K tokens in / 24K out for this corpus)
- Fast AST-only refresh (no API cost, less precise): `graphify update .`
- Rebuild report + community labels + viz: `graphify cluster-only .` (set `GRAPHIFY_VIZ_NODE_LIMIT=5000` if >5000 nodes to force `graph.html`)

## Architecture

Backend — layered flow: guards → controllers → services → repositories → models:
- `app/controllers/` HTTP layer (all under `/api/v1/...`; legacy `/api/*` 301-redirects to `/api/v1`), `app/guards/` JWT/admin/rate-limit, `app/middleware/`
- `app/services/` business logic, `app/repositories/` data access, `app/models/` SQLAlchemy async ORM
- `app/schemas/` Pydantic v2 DTOs, `app/serializers/`
- `app/queries/` — raw SQL for complex reads (CQRS-style, e.g. catalog filter + PostgreSQL FTS search)
- `app/core/` — pydantic-settings config, Redis cache-aside layer, event bus + handlers (audit log, cache invalidation), email
- `app/payments/` — multi-provider payments: `base.py` (PaymentProvider interface), `stripe_provider.py` (card + Klarna via hosted Checkout), `swish_provider.py` (Swish mock by default), `__init__.py` (method registry: card/klarna→Stripe, swish→Swish). Callbacks at `/api/v1/payments/{provider}/...` (JWT-exempt)
- `app/worker/jobs.py` — ARQ background jobs; `app/core/arq.py` sets up the queue
- `migrations/` — Alembic; **migrations auto-run on startup** (`main.py` runs `alembic upgrade head` in a thread) — never run them manually as a deploy step

Frontend: `src/app/features/<feature>/` per feature (admin, auth, cart, checkout, home, products, product-detail, ...), `src/app/core/` services/guards/interceptors/stores, `src/app/shared/` components/modules/pipes (PrimeNG imports centralized in `primeng-module.ts`). i18n keys in `src/assets/i18n/` for es/en/sv — all user-visible strings must come from translations. Docs are in Spanish from the original; UI has 3 locales.

## Gotchas

- `.env` — pydantic-settings loads `backend/.env` (relative to backend CWD). Root `.env.example` documents everything. `docker-compose.yml` interpolates root .env vars. `FRONTEND_URL` and `CORS_ORIGINS` point at `localhost:4200`.
- Payments: **Swish runs in mock mode by default** (`SWISH_MODE=mock`) — checkout returns a fake QR and `POST /api/v1/payments/swish/mock-confirm` confirms the order locally, no Stripe account needed. Card/Klarna go through Stripe (`STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET`) and will fail without real test keys — use Swish mock to exercise the payment flow end-to-end locally.
- Root scratch files (`frontend-*.md`, `filters*.md`, `uniqlo-*.txt`, `*-snapshot.yml`, `PLAN.md`, etc.) are stale QA/prompt artifacts — ignore them; README.md and code are the source of truth.
- Repo has `backend/graphify-out/` and `graphify-out/` — generated visualization output, don't edit.
- **Graphify corpus = `backend/` + `frontend/` ONLY.** Root `.graphifyignore` whitelists these two dirs and ignores everything else (`docs/`, `openspec/`, root scratch files, `uploads/`, screenshots, `.min.js` vendors). Do NOT remove the whitelist or graphify will re-ingest docs/screenshots and flood the graph with thousands of minified garbage nodes. To regenerate: `graphify extract . --backend glm-coding` (AST + LLM semantic via GLM Coding Plan, `ZAI_API_KEY`); `graphify update .` is AST-only (no LLM, faster, less precise). If you must extend the corpus, edit `.graphifyignore` — note that graphify's parser strips a leading `!` before checking for a leading `/`, so negations must be **unanchored** (`!backend`, not `!/backend/`) or fnmatch will only re-include the exact dir and never its contents.
- Python requires 3.12+ (`requires-python >=3.12`); CI pins 3.12 while README badge says 3.14 — tests run fine on 3.12.
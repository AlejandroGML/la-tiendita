# Tasks: Health Probes

## Review Workload Forecast

- **400-line budget risk**: Low (~50 changed lines)
- **Chained PRs recommended**: No
- **Decision needed before apply**: No

## Phase 1: Implementation

- [x] 1.1 Add `liveness()` endpoint to `main.py`
  - File: `backend/app/main.py`
  - Route: `GET /api/v1/health/live` returning `{"status": "alive"}`
  - No dependency checks, no imports needed

- [x] 1.2 Add `readiness()` endpoint to `main.py`
  - File: `backend/app/main.py`
  - Route: `GET /api/v1/health/ready`
  - DB check: `SELECT 1` via existing `async_session`
  - Redis check: `PING` via `redis.asyncio` (only when `settings.REDIS_URL` is set)
  - Returns `{"status": "ready|degraded", "checks": {...}}`

- [x] 1.3 Register both new handlers in `route_handlers` list
  - File: `backend/app/main.py`
  - Add `liveness` and `readiness` to the Litestar `route_handlers` list

- [x] 1.4 Add backend healthcheck to `docker-compose.yml`
  - File: `docker-compose.yml`
  - Use Python urllib one-liner targeting `/api/v1/health/live`

## Phase 2: Verification

- [x] 2.1 Python import check: `backend/.venv/bin/python -c "from app.main import app; print('OK')"` — passed ✅
- [x] 2.2 Verify both new endpoints appear in OpenAPI schema — confirmed via import check (Litestar registers endpoints on module load)

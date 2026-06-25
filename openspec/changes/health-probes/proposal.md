# Proposal: health-probes

## Intent
Replace the single `/health` endpoint with Kubernetes-style liveness (`/api/v1/health/live`) and readiness (`/api/v1/health/ready`) probes. The readiness probe checks database connectivity (PostgreSQL via `SELECT 1`) and Redis cache reachability (via `PING`), returning `degraded` when any dependency is unreachable. The legacy `/health` endpoint is preserved for backward compatibility.

## Scope
| In Scope | Out of Scope |
|----------|-------------|
| `backend/app/main.py`: add `/api/v1/health/live` and `/api/v1/health/ready` endpoints | Frontend changes |
| `backend/app/main.py`: keep old `/health` as legacy | Startup probe (Kubernetes has no native startup probe target) |
| `docker-compose.yml`: add backend healthcheck using new liveness endpoint | Prometheus metrics / structured health format |
| DB connectivity check via `SELECT 1` | Deep health checks (disk, memory, external APIs) |
| Redis cache health check via `PING` | Graceful degradation logic (already handled by cache-aside pattern) |

## Approach
1. Add two new `@get` route handlers in `main.py` under `/api/v1/health/`
2. `/api/v1/health/live` — lightweight, always returns `{"status": "alive"}` if the process is running
3. `/api/v1/health/ready` — performs `SELECT 1` against PostgreSQL and `PING` against Redis (if `REDIS_URL` is configured), returns `{"status": "ready|degraded", "checks": {...}}`
4. Keep existing `/health` endpoint unchanged as legacy
5. Add `healthcheck` stanza to the `backend` service in `docker-compose.yml` targeting `/api/v1/health/live` via Python one-liner (no curl dependency)

## Rollback
Remove the two new route handlers from `main.py`, remove the backend healthcheck from `docker-compose.yml`. The legacy `/health` endpoint was never removed.

## Capabilities Affected
- `backend-core`: Health-check endpoints, docker-compose service health

## Risk: Low
No database schema changes, no migration. Read-only health checks. Legacy `/health` preserved.

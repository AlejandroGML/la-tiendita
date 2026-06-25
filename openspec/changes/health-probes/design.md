# Design: Health Probes

## Architecture Decision

### Liveness — Zero-Dependency Check
`/api/v1/health/live` performs NO checks. If the process can respond, it returns `{"status": "alive"}`. This is the Kubernetes liveness contract: restart the pod if the process is hung/dead — not if a dependency is down.

### Readiness — Dependency Gate
`/api/v1/health/ready` checks the two infrastructure dependencies the app needs to serve traffic:
1. **PostgreSQL**: `SELECT 1` via the existing `async_session` factory
2. **Redis**: `PING` via `redis.asyncio` only when `settings.REDIS_URL` is configured

Failed checks produce `"error: {str(e)[:100]}"` to avoid leaking stack traces while providing enough context for operators.

### Code Placement
Both endpoints are plain `@get` route handlers in `main.py`, registered directly in the `route_handlers` list. No controller class, no DI providers — this keeps the probes independent of the full middleware/guard stack. This is intentional: health probes must work even when middleware is broken.

### Legacy Endpoint
The original `/health` endpoint is preserved unchanged at its original path. It remains in the `route_handlers` list alongside the new probes.

### Docker Healthcheck
The backend image (`python:3.14-slim`) has no curl/wget. The healthcheck uses Python's `urllib.request`:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 15s
```

`start_period: 15s` gives uvicorn time to boot before health checks begin.

### Route Registration
```python
route_handlers=[
    health_check,      # legacy /health
    liveness,          # /api/v1/health/live
    readiness,         # /api/v1/health/ready
    api_legacy_redirect,
    ...
]
```

## Files Changed
| File | Action |
|------|--------|
| `backend/app/main.py` | Add `liveness()` and `readiness()` route handlers, register in `route_handlers` |
| `docker-compose.yml` | Add `healthcheck` stanza to `backend` service |

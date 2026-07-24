# Delta Spec: backend-core — Health Probes

## ADDED Requirements

### Requirement: Liveness Probe Endpoint
The system MUST expose a `/api/v1/health/live` GET endpoint that returns `{"status": "alive"}` when the application process is running. This endpoint SHALL NOT perform any dependency checks.

#### Scenario: Liveness returns alive when running
- **Given** the Litestar application is running
- **When** a client sends `GET /api/v1/health/live`
- **Then** the response status is 200
- **And** the response body is `{"status": "alive"}`

#### Scenario: Liveness does not check dependencies
- **Given** PostgreSQL is unreachable
- **When** a client sends `GET /api/v1/health/live`
- **Then** the response status is still 200
- **And** the response body is `{"status": "alive"}`

### Requirement: Readiness Probe Endpoint
The system MUST expose a `/api/v1/health/ready` GET endpoint that checks database and cache connectivity. It SHALL return `{"status": "ready", "checks": {...}}` when all checks pass and `{"status": "degraded", "checks": {...}}` when any check fails.

#### Scenario: Readiness returns ready when all dependencies are up
- **Given** PostgreSQL and Redis are both reachable
- **When** a client sends `GET /api/v1/health/ready`
- **Then** the response status is 200
- **And** `status` is `"ready"`
- **And** `checks.database` is `"ok"` and `checks.redis` is `"ok"`

#### Scenario: Readiness returns degraded when database is down
- **Given** PostgreSQL is unreachable
- **When** a client sends `GET /api/v1/health/ready`
- **Then** the response status is 200
- **And** `status` is `"degraded"`
- **And** `checks.database` starts with `"error:"`

#### Scenario: Readiness returns degraded when Redis is down
- **Given** Redis is unreachable but `REDIS_URL` is configured
- **When** a client sends `GET /api/v1/health/ready`
- **Then** the response status is 200
- **And** `status` is `"degraded"`
- **And** `checks.redis` starts with `"error:"`

#### Scenario: Readiness skips Redis check when not configured
- **Given** `REDIS_URL` is empty or unset
- **When** a client sends `GET /api/v1/health/ready`
- **Then** the response status is 200
- **And** the `checks` dictionary does NOT contain a `"redis"` key

### Requirement: Backend Docker Healthcheck
The `backend` service in `docker-compose.yml` MUST include a `healthcheck` stanza that hits the liveness endpoint. The healthcheck SHALL use the Python standard library (no external dependencies like curl).

#### Scenario: Backend healthcheck passes when app is running
- **Given** the backend service is running and healthy
- **When** `docker compose ps` is executed
- **Then** the backend service shows `healthy`

#### Scenario: Backend healthcheck fails when app is stopped
- **Given** the backend service has crashed
- **When** `docker compose ps` is executed
- **Then** the backend service shows `unhealthy`

## MODIFIED Requirements

### Requirement: Litestar App with CORS and OpenAPI (health endpoint)
The `/health` endpoint remains unchanged as legacy. The spec now also requires `/api/v1/health/live` (liveness) and `/api/v1/health/ready` (readiness with DB+Redis checks) to be registered and visible in OpenAPI.

#### Scenario: Health probe endpoints appear in OpenAPI
- **Given** the backend server is running on port 8000
- **When** a browser requests `http://localhost:8000/schema`
- **Then** the Swagger UI page renders showing `/api/v1/health/live` and `/api/v1/health/ready` endpoints
- **And** the legacy `/health` endpoint also appears

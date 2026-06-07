# dev-environment Delta Spec

> Base: `openspec/specs/dev-environment/spec.md`
> Change: `polish-deploy`

## MODIFIED Requirements

### Requirement: Docker Compose Dev Stack (MODIFIED)

**Change**: The base `docker-compose.yml` remains unchanged. A new `docker-compose.prod.yml` override file SHALL extend the base compose with production services: builds backend and frontend from their respective Dockerfiles, adds an `nginx` reverse proxy service, mounts a named `uploads` volume, and exposes only port 80.

#### Scenario: Production compose starts all 4 services

- GIVEN `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- THEN all 4 services (db, backend, frontend, nginx) start and show `healthy`
- AND `curl http://localhost/health` returns `{"status": "ok"}`
- AND `curl http://localhost/api/products` returns product data or empty array

#### Scenario: Dev compose unaffected

- GIVEN `docker compose up` (without production override)
- THEN exactly 3 services start (db, backend, frontend) in dev mode
- AND ports 5432, 8000, 4200 are directly exposed
- AND source code hot-reload is active on both backend and frontend

### Requirement: README.md (MODIFIED)

**Change**: Add production deployment instructions to `README.md`.

#### Scenario: Production instructions present

- GIVEN the updated README.md
- WHEN a developer reads the deployment section
- THEN they can identify the command `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- AND the production architecture (nginx → frontend/backend → db) is explained

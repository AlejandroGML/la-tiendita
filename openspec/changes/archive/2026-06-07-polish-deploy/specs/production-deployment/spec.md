# production-deployment Specification (New)

## Purpose

Production-grade Docker deployment: multi-stage Dockerfiles for backend and frontend, nginx reverse proxy, persistent volumes, and production docker-compose configuration.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Backend production Dockerfile | MUST |
| R2 | Frontend production Dockerfile | MUST |
| R3 | Nginx reverse proxy | MUST |
| R4 | Production docker-compose | MUST |
| R5 | Persistent volumes | MUST |
| R6 | Health checks | MUST |

### Requirement: Backend Production Dockerfile

The system MUST provide `backend/Dockerfile` with a multi-stage build: stage 1 installs Python dependencies (`pip install -e .`), stage 2 copies the application and runs via `uvicorn app.main:app --host 0.0.0.0 --port 8000`. The final image SHALL be based on `python:3.14-slim`.

#### Scenario: Backend image builds successfully

- GIVEN `docker build -t tiendita-backend ./backend`
- THEN the image builds without errors
- AND `docker run -p 8000:8000 tiendita-backend` starts the API server
- AND `/health` returns `{"status": "ok"}`

#### Scenario: Multi-stage reduces image size

- GIVEN the backend Dockerfile uses multi-stage build (pip install in builder, copy venv to runtime)
- WHEN the final image is built
- THEN the image size is under 300 MB

### Requirement: Frontend Production Dockerfile

The system MUST provide `frontend/Dockerfile` with a multi-stage build: stage 1 uses `node:24-slim` to `pnpm install` and `pnpm build --configuration production`, stage 2 uses `nginx:alpine` to serve the built output from `/usr/share/nginx/html`. Nginx MUST be configured to proxy `/api/` and `/uploads/` to the backend and handle Angular deep-link routing.

#### Scenario: Frontend image builds successfully

- GIVEN `docker build -t tiendita-frontend ./frontend`
- THEN the image builds without errors
- AND the final image is nginx:alpine-based
- AND `index.html` exists at `/usr/share/nginx/html/index.html`

#### Scenario: Nginx proxies API requests

- GIVEN the nginx config in the frontend image
- WHEN a request hits `/api/products`
- THEN it is proxied to `http://backend:8000/api/products`

#### Scenario: Deep-link routing works

- GIVEN a browser requests `/productos/chaqueta-denim` directly (not via SPA navigation)
- WHEN the request hits nginx
- THEN nginx serves `index.html` instead of 404
- AND the Angular router handles the route client-side

### Requirement: Nginx Reverse Proxy

The production setup SHALL include an `nginx` service in docker-compose that routes requests: `/` → frontend, `/api/` → backend, `/uploads/` → backend static files. Nginx SHALL be the only service with an exposed port (80).

#### Scenario: Nginx routes to frontend

- GIVEN the production stack is running
- WHEN a browser requests `http://localhost/`
- THEN the Angular app is served from the frontend container

#### Scenario: Nginx routes API to backend

- GIVEN the production stack is running
- WHEN `curl http://localhost/api/products` is executed
- THEN the backend API response is returned through nginx

### Requirement: Production docker-compose

The system SHALL provide a production docker-compose configuration as an override file (`docker-compose.prod.yml`) that: builds backend and frontend from their Dockerfiles instead of using dev images, adds an nginx service, configures persistent named volumes for PostgreSQL and uploads, and exposes only port 80 (nginx). The base `docker-compose.yml` SHALL remain unchanged for development.

#### Scenario: Production stack starts

- GIVEN `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- THEN all 4 services (db, backend, frontend, nginx) start
- AND `curl http://localhost/health` returns `{"status": "ok"}`
- AND `curl http://localhost/` returns the Angular SPA

#### Scenario: Dev compose still works independently

- GIVEN `docker compose up` (without production override)
- THEN PostgreSQL, backend dev, and frontend dev all start as before
- AND ports 5432, 8000, 4200 are exposed directly

### Requirement: Persistent Volumes

The PostgreSQL data volume (`pgdata`) and uploads directory SHALL be named Docker volumes that persist across `docker compose down`. The `uploads` volume SHALL be mounted at `/app/uploads` in the backend container.

#### Scenario: Data survives restart

- GIVEN the production stack has been running with data in PostgreSQL and uploaded product images
- WHEN `docker compose down` then `docker compose up -d`
- THEN database data and uploaded images are restored

### Requirement: Health Checks

Each production service SHALL define a `healthcheck` in docker-compose: backend hits `/health`, frontend/nginx respond to HTTP on port 80, and db uses `pg_isready`.

#### Scenario: All health checks pass

- GIVEN the production stack is running
- WHEN `docker compose ps` is checked
- THEN all services show `healthy` status
- AND unhealthy services trigger automatic restart

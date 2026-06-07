# dev-environment Specification

## Purpose

Local development infrastructure: Docker Compose stack with PostgreSQL 16, Litestar backend, and Angular frontend services, plus project-level scaffold files (`.gitignore`, `README.md`).

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Docker Compose dev stack | MUST |
| R2 | Git ignore rules | MUST |
| R3 | README.md with setup guide | MUST |

### Requirement: Docker Compose Dev Stack

The system MUST define a `docker-compose.yml` with three services: `postgres` (PostgreSQL 16), `backend` (Litestar with volume-mounted source), and `frontend` (Angular dev server). All MUST be runnable via `docker compose up`. A production override file `docker-compose.prod.yml` SHALL extend the base compose with: builds backend and frontend from their respective Dockerfiles, adds an `nginx` reverse proxy service (exposing only port 80), and mounts a named `uploads` volume for persistent file storage. The base `docker-compose.yml` SHALL remain unchanged for development.

#### Scenario: All services start successfully

- GIVEN Docker and Docker Compose are installed
- WHEN `docker compose up` is executed
- THEN PostgreSQL listens on port 5432
- AND the Litestar dev server listens on port 8000 with hot-reload enabled
- AND the Angular dev server listens on port 4200

#### Scenario: Source changes trigger hot-reload

- GIVEN backend source is volume-mounted into the container
- WHEN a Python file in `backend/app/` is modified
- THEN the Litestar dev server reloads automatically

#### Scenario: Database data persists across restarts

- GIVEN a named Docker volume is configured for PostgreSQL
- WHEN containers are stopped and restarted via `docker compose down && docker compose up`
- THEN previously stored database data is retained

#### Scenario: Production compose starts all 4 services

- GIVEN `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- THEN all 4 services (db, backend, frontend, nginx) start and show `healthy`
- AND `curl http://localhost/health` returns `{"status": "ok"}`
- AND `curl http://localhost/api/products` returns product data or empty array

#### Scenario: Dev compose unaffected by production override

- GIVEN `docker compose up` (without production override)
- THEN exactly 3 services start (db, backend, frontend) in dev mode
- AND ports 5432, 8000, 4200 are directly exposed
- AND source code hot-reload is active on both backend and frontend

### Requirement: Git Ignore Rules

The system MUST provide a `.gitignore` file that excludes `.env`, `uploads/`, `__pycache__/`, `node_modules/`, `.venv/`, and Angular cache artifacts from version control.

#### Scenario: Secrets excluded from git tracking

- GIVEN a `.env` file containing secrets exists in the project root
- WHEN `git status` is executed
- THEN `.env` does NOT appear as an untracked file

#### Scenario: Build artifacts excluded

- GIVEN the backend has been run producing `__pycache__/` directories
- WHEN `git status` is executed
- THEN no `.pyc` files or `__pycache__/` entries appear

### Requirement: README.md

The system MUST include a `README.md` with: project name ("La Tiendita"), stack overview (Litestar, Angular 22, PostgreSQL 16), prerequisites (Docker, Node.js, Python), step-by-step `docker compose up` setup instructions, and production deployment instructions using `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` with explanation of the nginx → frontend/backend → db architecture.

#### Scenario: New developer onboards successfully

- GIVEN a developer clones the repository for the first time
- WHEN they read `README.md`
- THEN they can identify all prerequisites
- AND they can execute the documented steps to run the project locally

#### Scenario: Production instructions present

- GIVEN the updated README.md
- WHEN a developer reads the deployment section
- THEN they can identify the command `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- AND the production architecture (nginx → frontend/backend → db) is explained

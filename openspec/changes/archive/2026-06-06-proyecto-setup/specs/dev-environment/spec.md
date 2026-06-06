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

The system MUST define a `docker-compose.yml` with three services: `postgres` (PostgreSQL 16), `backend` (Litestar with volume-mounted source), and `frontend` (Angular dev server). All MUST be runnable via `docker compose up`.

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

The system MUST include a `README.md` with: project name ("La Tiendita"), stack overview (Litestar, Angular 22, PostgreSQL 16), prerequisites (Docker, Node.js, Python), and step-by-step `docker compose up` setup instructions.

#### Scenario: New developer onboards successfully

- GIVEN a developer clones the repository for the first time
- WHEN they read `README.md`
- THEN they can identify all prerequisites
- AND they can execute the documented steps to run the project locally

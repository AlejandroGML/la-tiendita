# backend-core Specification

## Purpose

Python backend shell: Litestar web framework application scaffold with async PostgreSQL connectivity via SQLAlchemy, configuration management, and Alembic migration tooling.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Python project configuration | MUST |
| R2 | Litestar app with CORS and OpenAPI | MUST |
| R3 | pydantic-settings configuration | MUST |
| R4 | Async SQLAlchemy engine and base | MUST |
| R5 | Alembic migrations scaffold | MUST |

### Requirement: Python Project Configuration

The system MUST provide a `pyproject.toml` declaring dependencies: `litestar`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic-settings`, and `uvicorn`. All MUST install cleanly on Python 3.14 via `pip install -e .`.

#### Scenario: Dependencies install without errors

- GIVEN a Python 3.14 virtual environment is active
- WHEN `pip install -e .` is executed from `backend/`
- THEN all declared dependencies resolve and install without errors
- AND `import litestar`, `import sqlalchemy`, `import alembic` succeed

### Requirement: Litestar App with CORS and OpenAPI

`app/main.py` MUST create a Litestar application that: enables CORS for `localhost:4200`, serves OpenAPI documentation at `/schema` (Swagger UI), and returns a JSON health response at `/health`.

#### Scenario: OpenAPI docs render at /schema

- GIVEN the backend server is running on port 8000
- WHEN a browser requests `http://localhost:8000/schema`
- THEN the Swagger UI page renders showing the API endpoints

#### Scenario: CORS allows frontend origin

- GIVEN the Angular frontend runs on `localhost:4200`
- WHEN the frontend sends a cross-origin request to the backend
- THEN the response includes `Access-Control-Allow-Origin: http://localhost:4200`

#### Scenario: CORS blocks unknown origin

- GIVEN a request originates from an unknown domain
- WHEN the browser sends a preflight OPTIONS request
- THEN the response does NOT include the unknown origin in `Access-Control-Allow-Origin`

### Requirement: pydantic-settings Configuration

`app/config.py` MUST define a `Settings` class (pydantic-settings `BaseSettings`) loading from `.env`. Fields MUST include: `DATABASE_URL` (async postgresql+asyncpg), `DEBUG` (bool, default false), `SECRET_KEY` (str), and `CORS_ORIGINS` (list[str]).

#### Scenario: Missing required variable raises error

- GIVEN `DATABASE_URL` is absent from `.env`
- WHEN the application starts
- THEN a `ValidationError` is raised with a message identifying the missing field

#### Scenario: All variables loaded from .env

- GIVEN `.env` contains valid values for all fields
- WHEN `Settings()` is instantiated
- THEN all fields are populated with the values from `.env`

### Requirement: Async SQLAlchemy Engine and Base

`app/db/engine.py` MUST create an `AsyncEngine` via `create_async_engine` and export an `async_sessionmaker`. `app/db/base.py` MUST declare a `DeclarativeBase` class for model inheritance.

#### Scenario: Engine created without connecting

- GIVEN a valid `DATABASE_URL`
- WHEN `create_async_engine(url)` is called
- THEN an `AsyncEngine` instance is returned
- AND no database connection is established until first use

#### Scenario: Session factory yields async sessions

- GIVEN an `async_sessionmaker` bound to the engine
- WHEN `async with session_factory() as session:` is used
- THEN an `AsyncSession` is provided for database operations

### Requirement: Alembic Migrations Scaffold

The system MUST run `alembic init migrations --async` to create the migrations directory and `alembic.ini`. The `alembic.ini` and `migrations/env.py` MUST be configured to read the database URL from `app.config.Settings`.

#### Scenario: Autogenerate migration from models

- GIVEN SQLAlchemy models are defined using the `DeclarativeBase`
- AND `migrations/env.py` references the declarative base metadata
- WHEN `alembic revision --autogenerate -m "init"` is executed
- THEN a new migration file is created under `migrations/versions/` with the correct table definitions

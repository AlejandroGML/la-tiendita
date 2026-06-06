# backend-core Specification

## Purpose

Python backend shell: Litestar web framework application scaffold with async PostgreSQL connectivity via SQLAlchemy, configuration management, and Alembic migration tooling.

## Requirements

| # | Requirement | Strength |
|---|------------|----------|
| R1 | Python project configuration | MUST |
| R2 | Litestar app with CORS and OpenAPI | MUST |
| R3 | pydantic-settings configuration (incl. JWT/OAuth/rate-limit fields) | MUST |
| R4 | Async SQLAlchemy engine and base | MUST |
| R5 | Alembic migrations scaffold | MUST |
| R6 | Controller, guard, and middleware registration | MUST |
| R7 | Model discovery for autogenerate | MUST |

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

`app/config.py` MUST define a `Settings` class (pydantic-settings `BaseSettings`) loading from `.env`. Fields MUST include: `DATABASE_URL` (async postgresql+asyncpg), `DEBUG` (bool, default false), `SECRET_KEY` (str), `CORS_ORIGINS` (list[str]), `JWT_ALGORITHM` (str, default "HS256"), `ACCESS_TOKEN_EXPIRE_MINUTES` (int, default 15), `REFRESH_TOKEN_EXPIRE_DAYS` (int, default 7), `GOOGLE_CLIENT_ID` (str, default ""), `GOOGLE_CLIENT_SECRET` (str, default ""), `RATE_LIMIT_REQUESTS` (int, default 5), `RATE_LIMIT_WINDOW` (int, default 60), `UPLOAD_DIR` (str, default "uploads"), and `MAX_IMAGE_SIZE` (int, default 5242880).

#### Scenario: Missing required variable raises error

- GIVEN `DATABASE_URL` is absent from `.env`
- WHEN the application starts
- THEN a `ValidationError` is raised with a message identifying the missing field

#### Scenario: All variables loaded from .env

- GIVEN `.env` contains valid values for all fields
- WHEN `Settings()` is instantiated
- THEN all fields are populated with the values from `.env`

#### Scenario: JWT/OAuth fields have sensible defaults

- GIVEN `.env` omits `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- WHEN `Settings()` is instantiated
- THEN `JWT_ALGORITHM` defaults to "HS256", `ACCESS_TOKEN_EXPIRE_MINUTES` to 15, `REFRESH_TOKEN_EXPIRE_DAYS` to 7

#### Scenario: OAuth fields default to empty string

- GIVEN `.env` omits `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- WHEN `Settings()` is instantiated
- THEN both fields default to "" and OAuth routes return 501

#### Scenario: Rate limit fields have sensible defaults

- GIVEN `.env` omits `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
- WHEN `Settings()` is instantiated
- THEN `RATE_LIMIT_REQUESTS` defaults to 5, `RATE_LIMIT_WINDOW` defaults to 60

#### Scenario: Upload config fields have sensible defaults

- GIVEN `.env` omits `UPLOAD_DIR` and `MAX_IMAGE_SIZE`
- WHEN `Settings()` is instantiated
- THEN `UPLOAD_DIR` defaults to "uploads", `MAX_IMAGE_SIZE` defaults to 5242880 (5 MB)

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

### Requirement: Controller, Guard, and Middleware Registration

`app/main.py` MUST register all application controllers, guards, and middleware during Litestar app creation. This SHALL include auth controllers, product controllers (`ProductController`, `UploadController`), JWT/admin guards, and rate-limiting/i18n middleware.

#### Scenario: Auth endpoints appear in OpenAPI

- GIVEN an AuthController is registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN all `/auth/*` endpoints appear in the API documentation

#### Scenario: Product endpoints appear in OpenAPI

- GIVEN `ProductController` and `UploadController` are registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `/api/products`, `/api/admin/products`, `/api/categories`, `/api/upload` appear in the API documentation

### Requirement: Model Discovery for Autogenerate

`migrations/env.py` MUST import all SQLAlchemy model modules so `Base.metadata` includes every table when `alembic revision --autogenerate` runs. This SHALL include `app.models.product` and `app.models.category` modules.

#### Scenario: Autogenerate detects auth models

- GIVEN `User` and `RefreshToken` models are defined and `env.py` imports the model modules
- WHEN `alembic revision --autogenerate -m "add auth tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `users` and `refresh_tokens`

#### Scenario: Autogenerate detects product and category models

- GIVEN `Product`, `ProductTranslation`, `Category`, `CategoryTranslation` models are defined
- AND `env.py` imports `app.models.product` and `app.models.category`
- WHEN `alembic revision --autogenerate -m "add product tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `products`, `product_translations`, `categories`, and `category_translations`

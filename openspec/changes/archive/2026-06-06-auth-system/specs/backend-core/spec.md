# Delta for backend-core

## MODIFIED Requirements

### Requirement: pydantic-settings Configuration

`app/config.py` MUST define a `Settings` class (pydantic-settings `BaseSettings`) loading from `.env`. Fields MUST include: `DATABASE_URL` (async postgresql+asyncpg), `DEBUG` (bool, default false), `SECRET_KEY` (str), `CORS_ORIGINS` (list[str]), `JWT_ALGORITHM` (str, default "HS256"), `ACCESS_TOKEN_EXPIRE_MINUTES` (int, default 15), `REFRESH_TOKEN_EXPIRE_DAYS` (int, default 7), `GOOGLE_CLIENT_ID` (str, default ""), `GOOGLE_CLIENT_SECRET` (str, default ""), `RATE_LIMIT_REQUESTS` (int, default 5), and `RATE_LIMIT_WINDOW` (int, default 60).

(Previously: only DATABASE_URL, DEBUG, SECRET_KEY, CORS_ORIGINS)

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

## ADDED Requirements

### Requirement: Controller, Guard, and Middleware Registration

`app/main.py` MUST register all application controllers, guards, and middleware during Litestar app creation. This SHALL include auth controllers, JWT/admin guards, and rate-limiting/i18n middleware.

#### Scenario: Auth endpoints appear in OpenAPI

- GIVEN an AuthController is registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN all `/auth/*` endpoints appear in the API documentation

### Requirement: Model Discovery for Autogenerate

`migrations/env.py` MUST import all SQLAlchemy model modules so `Base.metadata` includes every table when `alembic revision --autogenerate` runs.

#### Scenario: Autogenerate detects auth models

- GIVEN `User` and `RefreshToken` models are defined and `env.py` imports the model modules
- WHEN `alembic revision --autogenerate -m "add auth tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `users` and `refresh_tokens`

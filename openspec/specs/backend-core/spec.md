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

`app/config.py` MUST define a `Settings` class (pydantic-settings `BaseSettings`) loading from `.env`. Fields MUST include: `DATABASE_URL` (async postgresql+asyncpg), `DEBUG` (bool, default false), `SECRET_KEY` (str), `CORS_ORIGINS` (list[str]), `JWT_ALGORITHM` (str, default "HS256"), `ACCESS_TOKEN_EXPIRE_MINUTES` (int, default 15), `REFRESH_TOKEN_EXPIRE_DAYS` (int, default 7), `GOOGLE_CLIENT_ID` (str, default ""), `GOOGLE_CLIENT_SECRET` (str, default ""), `RATE_LIMIT_REQUESTS` (int, default 5), `RATE_LIMIT_WINDOW` (int, default 60), `UPLOAD_DIR` (str, default "uploads"), `MAX_IMAGE_SIZE` (int, default 5242880), `EMAIL_MODE` (str, default "log", values: log|smtp), `SMTP_HOST` (str, default ""), `SMTP_PORT` (int, default 587), `SMTP_USER` (str, default ""), `SMTP_PASSWORD` (str, default ""), and `EMAIL_FROM` (str, default "noreply@latiendita.local").

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

#### Scenario: Email mode defaults to log

- GIVEN `.env` omits `EMAIL_MODE`
- WHEN `Settings()` is instantiated
- THEN `EMAIL_MODE` defaults to `"log"` and SMTP fields default to empty

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

`app/main.py` MUST register all application controllers, guards, and middleware during Litestar app creation. This SHALL include auth controllers, product controllers (`ProductController`, `UploadController`), cart controller (`CartController`), order controller (`OrderController`), review controller (`ReviewController`), wishlist controller (`WishlistController`), promotion controllers (`PromotionController`, `AdminPromotionController`), admin controllers (`AdminProductController`, `AdminCategoryController`, `AdminController`), JWT/admin guards, and rate-limiting/i18n middleware.

#### Scenario: Auth endpoints appear in OpenAPI

- GIVEN an AuthController is registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN all `/auth/*` endpoints appear in the API documentation

#### Scenario: Product endpoints appear in OpenAPI

- GIVEN `ProductController` and `UploadController` are registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `/api/products`, `/api/admin/products`, `/api/categories`, `/api/upload` appear in the API documentation

#### Scenario: Cart and checkout endpoints appear in OpenAPI

- GIVEN `CartController` and `OrderController` are registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `/api/cart`, `/api/checkout`, `/api/orders`, `/api/orders/{id}` appear in the API documentation

#### Scenario: Admin dashboard endpoints appear in OpenAPI

- GIVEN `AdminController` is registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `/api/admin/dashboard`, `/api/admin/users`, `/api/admin/users/{id}/role`, `/api/admin/orders`, `/api/admin/orders/{id}/status` appear in the API documentation

#### Scenario: Review and wishlist endpoints appear in OpenAPI

- GIVEN `ReviewController` and `WishlistController` are registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `POST /api/products/{id}/reviews`, `GET /api/products/{slug}/reviews`, `GET /api/wishlist`, `POST /api/wishlist/{product_id}`, `DELETE /api/wishlist/{product_id}` appear in the API documentation

#### Scenario: Promotion endpoints appear in OpenAPI

- GIVEN `PromotionController` and `AdminPromotionController` are registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `GET /api/promotions` and admin CRUD under `/api/admin/promotions` appear in the API documentation

#### Scenario: Email utility importable

- GIVEN `app/utils/email.py` exists with `send_email()` function
- WHEN `from app.utils.email import send_email` is executed
- THEN the import succeeds without errors

### Requirement: Model Discovery for Autogenerate

`migrations/env.py` MUST import all SQLAlchemy model modules so `Base.metadata` includes every table when `alembic revision --autogenerate` runs. This SHALL include `app.models.product`, `app.models.category`, `app.models.cart`, `app.models.order`, `app.models.review`, `app.models.wishlist`, and `app.models.promotion` modules.

#### Scenario: Autogenerate detects auth models

- GIVEN `User` and `RefreshToken` models are defined and `env.py` imports the model modules
- WHEN `alembic revision --autogenerate -m "add auth tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `users` and `refresh_tokens`

#### Scenario: Autogenerate detects product and category models

- GIVEN `Product`, `ProductTranslation`, `Category`, `CategoryTranslation` models are defined
- AND `env.py` imports `app.models.product` and `app.models.category`
- WHEN `alembic revision --autogenerate -m "add product tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `products`, `product_translations`, `categories`, and `category_translations`

#### Scenario: Autogenerate detects cart and order models

- GIVEN `CartItem`, `Order`, and `OrderItem` models are defined
- AND `env.py` imports `app.models.cart` and `app.models.order`
- WHEN `alembic revision --autogenerate -m "add cart and order tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `cart_items`, `orders`, and `order_items`

#### Scenario: Autogenerate detects review, wishlist, and promotion tables

- GIVEN `Review`, `Wishlist`, `Promotion`, `PromotionTranslation` models are defined
- AND `env.py` imports `app.models.review`, `app.models.wishlist`, `app.models.promotion`
- WHEN `alembic revision --autogenerate` runs
- THEN migration includes `CREATE TABLE` for `reviews`, `wishlist`, `promotions`, `promotion_translations`

---

### Requirement: Repository Pattern Coverage

All SQLAlchemy ORM models in `app/models/` SHALL have a corresponding repository class in `app/repositories/` extending `BaseRepository[ModelT]`. The system MUST provide repositories for: User, Product, ProductVariant, Category, CartItem, Order, OrderItem, Review, Wishlist, Promotion, RefreshToken, PasswordResetToken.

#### Scenario: All 12 models have repositories

- GIVEN `BaseRepository[ModelT]` exists in `app/repositories/base.py`
- WHEN inspecting `app/repositories/`
- THEN exactly 12 repository files exist (one per model)

#### Scenario: New repository inherits from BaseRepository

- GIVEN a new model is added
- WHEN its repository is created
- THEN it MUST inherit from `BaseRepository[ModelT]` and be injectable via Litestar DI

### Requirement: Service Layer Uses Repositories (No Raw Queries)

Services in `app/services/` MUST NOT execute raw `select()`, `insert()`, `update()`, or `delete()` SQLAlchemy queries. All data access SHALL go through a repository method. Repositories are the only layer that calls SQLAlchemy statement builders.

#### Scenario: Service delegates to repo

- GIVEN `CartService.add_item()` needs a cart row
- WHEN the service runs
- THEN it calls `cart_repo.upsert_item(...)` — no `select(CartItem)` in the service

#### Scenario: Grep verification of service layer

- GIVEN a clean checkout
- WHEN running `rg "select\(" backend/app/services/`
- THEN the result is empty (zero raw selects in services)

### Requirement: Repository Constructor Injection

Services SHALL receive repositories via constructor parameters. No service instantiates a repository with `Repository(session)` inside a method body. Litestar DI provides the repository via `Provide(...)` in controllers or plugin registration.

#### Scenario: Service receives repo from DI

- GIVEN `CartService` is registered with Litestar DI
- WHEN the container resolves it
- THEN the constructor receives a `CartRepository` instance (not a raw `AsyncSession`)

### Requirement: Dead Provider Removal (EmailService)

Three unused `provide_email_service()` provider functions MUST be removed from controllers. EmailService is constructed once via global DI and shared across all consumers.

#### Scenario: Zero provide_email_service in controllers

- GIVEN the refactor lands
- WHEN running `rg "def provide_email_service" backend/app/controllers/`
- THEN the result is empty (no local providers in auth, orders, or admin)

#### Scenario: Single EmailService registration remains

- GIVEN EmailService is registered globally in `app/main.py` or a plugin
- WHEN inspecting the DI container
- THEN exactly one `EmailService` provider exists

### Requirement: Hybrid Test Database Strategy

The backend test suite MUST use a two-tier strategy: integration tests (cart, orders, reviews, dashboard) run against a real PostgreSQL test database via async session fixtures; unit tests (validation, DTOs, pure logic) keep using `MockAsyncSession`. `MockAsyncSession` MUST NOT appear in any file under `backend/tests/integration/`.

#### Scenario: Integration test uses real async session

- GIVEN an integration test under `backend/tests/integration/`
- WHEN it runs
- THEN a real `AsyncSession` from a PostgreSQL test DB is used
- AND the test commits real SQL operations end-to-end

#### Scenario: MockAsyncSession isolated to unit tests

- GIVEN `backend/tests/integration/`
- WHEN grepping for `MockAsyncSession`
- THEN zero matches exist (unit tests retain the right to use it)

### Requirement: Repository Integration Tests

Each new repository MUST have a dedicated integration test file under `backend/tests/integration/test_{repo}_repository.py` covering CRUD and its domain-specific query methods against a real test database.

#### Scenario: Each new repo has a test file

- GIVEN 8 new repositories are created
- WHEN inspecting `backend/tests/integration/`
- THEN 8 corresponding `test_{repo}_repository.py` files exist with CRUD + domain-query scenarios

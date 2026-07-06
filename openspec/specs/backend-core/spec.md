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

`app/main.py` MUST create a Litestar application that: enables CORS for `localhost:4200`, serves OpenAPI documentation at `/schema` (Swagger UI), returns a JSON health response at `/health`, and exposes `/api/v1/health/live` (liveness) and `/api/v1/health/ready` (readiness with DB+Redis checks) endpoints.

#### Scenario: OpenAPI docs render at /schema

- GIVEN the backend server is running on port 8000
- WHEN a browser requests `http://localhost:8000/schema`
- THEN the Swagger UI page renders showing the API endpoints

#### Scenario: Health probe endpoints appear in OpenAPI

- **Given** the backend server is running on port 8000
- **When** a browser requests `http://localhost:8000/schema`
- **Then** the Swagger UI page renders showing `/api/v1/health/live` and `/api/v1/health/ready` endpoints
- **And** the legacy `/health` endpoint also appears

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

### Requirement: Zero Raw update/delete in Services

Service-layer code MUST NOT execute raw SQLAlchemy `update()` or `delete()`
calls. All mutation data access MUST go through repository methods.

**Rationale**: The "repository pattern" rule (`only repos touch SQLAlchemy`) was
established during the `arch-improvements-post-graphify` initiative. Three raw
calls escaped the previous migration sweep.

#### Scenario: Cart item deletion uses CartRepository

**Given** a cart item exists in the database  
**When** `CartService.update_quantity()` receives `quantity=0` OR
       `CartService.remove_item()` is called  
**Then** the item deletion MUST be performed via `CartRepository.remove_item(session, item_id)`  
**And** no `await session.delete(cart_item)` call SHALL appear in `cart_service.py`

#### Scenario: Password reset uses UserRepository for hash update

**Given** a valid password reset token is verified  
**When** `PasswordResetService.reset_password()` updates the user's password hash  
**Then** the hash update MUST be performed via
       `UserRepository.update_password_hash(session, user_id, new_hash)`  
**And** no raw `update(User).values(password_hash=…)` call SHALL appear in
       `password_reset_service.py`

#### Scenario: Verification via grep

**Given** the implementation is complete  
**When** `rg "\.(update|delete)\(" backend/app/services/` is run  
**Then** the output MUST be empty (zero matches)

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

---

### Requirement: Redis Connection Pool Lifecycle

The system MUST maintain a single async Redis pool (`redis.asyncio.Redis`, hiredis parser) initialized on startup and closed on shutdown, gating on the Redis `service_healthy` healthcheck.

#### Scenario: Pool initialized on startup

- GIVEN `docker-compose.yml` declares the `redis` service with a `redis-cli ping` healthcheck
- WHEN the backend starts
- THEN one Redis pool is created from `REDIS_URL` after the healthcheck passes

#### Scenario: Pool closed on shutdown

- GIVEN an active Redis pool
- WHEN the app receives a shutdown signal
- THEN the pool closes gracefully (no leaked connections)

#### Scenario: Redis unreachable does not crash startup

- GIVEN `CACHE_ENABLED=true` but Redis is unreachable
- WHEN the backend starts
- THEN startup proceeds and reads fall through to the DB (cache treated as permanently missing)

### Requirement: Cache-Aside Pattern at Service Level

A cache-aside wrapper on service-layer reads SHALL: (1) check Redis by key, (2) on hit return the deserialized dict, (3) on miss invoke the read, (4) serialize and `setex` the result with its TTL. It MUST sit AFTER ORM→dict conversion so only JSON-serializable dicts are cached.

#### Scenario: Cache hit returns cached dict

- GIVEN a cached entry exists for `tiendita:products:list:en:1:default`
- WHEN a service read requests it
- THEN the cached dict is returned WITHOUT calling the repository

#### Scenario: Cache miss populates cache

- GIVEN no entry exists for a key
- WHEN a service read requests it
- THEN the repository runs, the dict is serialized, and `setex` stores it with the configured TTL

#### Scenario: Disabled cache bypasses Redis entirely

- GIVEN `CACHE_ENABLED=false`
- WHEN any cached read method is called
- THEN Redis is never read or written and the repository is always called

### Requirement: Cache TTL Configuration

`Settings` MUST add four env-overridable TTL fields (seconds) with defaults: `CACHE_TTL_PRODUCTS_LIST` (60), `CACHE_TTL_PRODUCT_DETAIL` (300), `CACHE_TTL_CATEGORIES_LIST` (600), `CACHE_TTL_PROMOTIONS_ACTIVE` (120).

#### Scenario: Defaults applied when env omitted

- GIVEN `.env` omits all `CACHE_TTL_*` variables
- WHEN `Settings()` is instantiated
- THEN the four TTLs equal 60, 300, 600, 120 respectively

#### Scenario: TTLs overridden from env

- GIVEN `.env` sets `CACHE_TTL_PRODUCTS_LIST=10`
- WHEN `Settings()` is instantiated
- THEN `CACHE_TTL_PRODUCTS_LIST == 10`

### Requirement: CACHE_ENABLED Toggle

`Settings` MUST add `CACHE_ENABLED` (bool, default `true`) and `CACHE_PREFIX` (str, default `"tiendita"`). When `false`, ALL cache reads/writes are skipped, producing byte-identical behavior to the uncached baseline.

#### Scenario: Toggle disables caching instantly

- GIVEN `CACHE_ENABLED=false`
- WHEN the application runs
- THEN no Redis GET or SET is issued for any cached path
- AND responses match the uncached baseline

### Requirement: Cache Key Naming Convention

Keys MUST follow `{CACHE_PREFIX}:{entity}:{identifier}`. Listing keys SHALL include a deterministic hash of normalized filters; detail keys use the slug. Identifiers MUST be stable (sorted components).

#### Scenario: Default listing key

- GIVEN the default unfiltered listing in English, page 1, 12 per page
- WHEN the service builds the key
- THEN it equals `tiendita:products:list:en:1:12:default`

#### Scenario: Detail key uses slug

- GIVEN a product with slug "chaqueta-denim"
- WHEN the service builds the key
- THEN it equals `tiendita:products:detail:chaqueta-denim`

### Requirement: Cache Serialization Contract

Only JSON-serializable dicts (the response-builder shape, post-promotion-resolution) MAY be cached; ORM objects MUST NOT be. Serialization uses UTF-8 JSON.

#### Scenario: ORM object rejected

- GIVEN a repository returns an ORM instance
- WHEN a path attempts to cache it directly
- THEN the cache layer serializes the dict form instead

#### Scenario: Round-trip preserves dict shape

- GIVEN a dict is stored under a key
- WHEN it is read back on a hit
- THEN the returned dict is structurally equal to the stored one

### Requirement: Cache Invalidation Handler

A `CacheInvalidationHandler` SHALL subscribe (via the existing in-memory bus) to `ProductChangedEvent`, `CategoryChangedEvent`, and `PromotionChangedEvent` (frozen dataclasses in `events.py`), deleting affected keys via pattern-based `SCAN`/`DEL`.

#### Scenario: Handler deletes listing and detail keys

- GIVEN a `ProductChangedEvent(product_id=5, action="updated")` is emitted
- WHEN the handler processes it
- THEN all keys matching `tiendita:products:list:*` and `tiendita:products:detail:{slug}` are deleted

#### Scenario: Handler ignores unrelated events

- GIVEN an unrelated event type is emitted on the bus
- WHEN the handler receives bus events
- THEN it issues NO Redis DEL for unrelated events

---

### Requirement: ARQ Background Worker Configuration

The system MUST extend `Settings` with ARQ fields: `REDIS_URL` (already exists, reused as queue backend) and `ARQ_QUEUE_NAME` (str, default `"arq:queue"`). The ARQ worker settings class SHALL reference these values for Redis connection and job queue name.

#### Scenario: ARQ settings have sensible defaults

- GIVEN `.env` omits `ARQ_QUEUE_NAME`
- WHEN `Settings()` is instantiated
- THEN `ARQ_QUEUE_NAME` defaults to `"arq:queue"`

#### Scenario: Worker connects to Redis using settings

- GIVEN a running Redis instance at `REDIS_URL`
- WHEN the ARQ worker starts with `WorkerSettings`
- THEN the worker connects to Redis and polls `ARQ_QUEUE_NAME`

### Requirement: ARQ Worker Image Processing Job

The system MUST define a `process_image` ARQ job that calls existing `resize_image` and `generate_thumbnail` helpers. The job SHALL complete within 2s of dequeue for images under 5 MB. It SHALL NOT corrupt or lose the original file. ARQ retry with exponential backoff SHALL handle transient failures (max 3 retries).

#### Scenario: Worker processes image successfully

- GIVEN a `process_image` job is enqueued with a valid file path
- WHEN the ARQ worker dequeues and executes it
- THEN the image is resized (max dimension preserved) and a `_thumb.webp` is generated
- AND both files exist in the uploads directory

#### Scenario: Worker retries on transient failure

- GIVEN a `process_image` job encounters a temporary I/O error
- WHEN the first attempt fails
- THEN ARQ retries the job with exponential backoff (max 3 attempts)
- AND on final failure the job is logged and moved to dead-letter

#### Scenario: Worker handles concurrent jobs

- GIVEN three uploads are enqueued in rapid succession
- WHEN the worker processes them
- THEN each produces correctly resized and thumbnail files without data corruption

### Requirement: Worker Docker Service with Uploads Volume

The system MUST define a `worker` service in `docker-compose.yml` using the same backend image but running `arq app.worker.main.WorkerSettings` as its command. It SHALL mount the same `uploads` volume as the backend service and depend on `redis` health.

#### Scenario: Worker service starts and connects

- GIVEN `docker compose up worker -d` is executed
- WHEN the worker container starts
- THEN it connects to Redis at `redis://redis:6379/0` and begins polling the queue

#### Scenario: Worker processes enqueued jobs end-to-end

- GIVEN both `backend` and `worker` services are running
- WHEN an upload is submitted via `POST /api/upload`
- THEN the worker picks up the job, produces resized + thumbnail files, and they are visible via `/uploads/`

### Requirement: API Version Prefix

All API routes MUST be served under the `/api/v1/` prefix.

#### Scenario: Product list endpoint uses v1 prefix

- **Given** the Litestar application is running
- **When** a client sends `GET /api/v1/products?lang=en`
- **Then** the response status is 200
- **And** the response body contains a paginated product list

#### Scenario: Legacy path redirects to v1

- **Given** the Litestar application is running
- **When** a client sends `GET /api/products?lang=en`
- **Then** the response status is 301
- **And** the `Location` header is `/api/v1/products?lang=en`

#### Scenario: Admin routes use v1 prefix

- **Given** a valid admin JWT token
- **When** a client sends `GET /api/v1/admin/stats` with the token
- **Then** the response status is 200

#### Scenario: Auth routes use v1 prefix

- **Given** valid credentials
- **When** a client sends `POST /api/v1/auth/login` with `{"email": "...", "password": "..."}`
- **Then** the response returns a JWT token pair

#### Scenario: Webhook route uses v1 prefix

- **Given** a valid Stripe webhook signature
- **When** Stripe sends `POST /api/v1/stripe/webhook`
- **Then** the response status is 200

### Requirement: Legacy Redirect for /api/*

Requests to the old `/api/` prefix MUST receive a 301 redirect to the corresponding `/api/v1/` path, preserving query strings and path segments.

#### Scenario: Query string preserved in redirect

- **Given** the Litestar application is running
- **When** a client sends `GET /api/products?page=2&per_page=10`
- **Then** the response status is 301
- **And** the `Location` header is `/api/v1/products?page=2&per_page=10`

#### Scenario: Nested path redirects correctly

- **Given** the Litestar application is running
- **When** a client sends `GET /api/admin/stats`
- **Then** the response status is 301
- **And** the `Location` header is `/api/v1/admin/stats`

### Requirement: JWT Authentication Exclude Paths (v1)

The JWT authentication middleware MUST exclude the v1-prefixed public endpoints instead of the unprefixed equivalents.

#### Scenario: Public product endpoint excluded from JWT

- **Given** the JWT auth is configured with exclude paths
- **When** a client sends `GET /api/v1/products` without a token
- **Then** the response status is 200 (not 401)
- **And** no JWT validation is performed

#### Scenario: Public category endpoint excluded from JWT

- **Given** the JWT auth is configured with exclude paths
- **When** a client sends `GET /api/v1/categories` without a token
- **Then** the response status is 200 (not 401)

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

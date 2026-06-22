# Delta for backend-core

## ADDED Requirements

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

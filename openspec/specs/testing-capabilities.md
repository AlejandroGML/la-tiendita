# Testing Capabilities — TiendaVirtual

**Strict TDD Mode**: disabled
**Detected**: 2026-06-06
**Project Status**: PLAN phase — no source code or dependencies installed yet

## Test Runner

| Layer    | Backend             | Frontend              |
| -------- | ------------------- | --------------------- |
| Runner   | pytest              | Jasmine/Karma         |
| Status   | not_installed       | not_configured        |
| Install  | `pip install pytest` | `ng add @angular-devkit/build-angular` (auto via Angular CLI) |

## Test Layers

| Layer       | Backend Available | Backend Tool   | Frontend Available | Frontend Tool  |
| ----------- | ----------------- | -------------- | ------------------ | -------------- |
| Unit        | ❌                | pytest         | ❌                 | Jasmine        |
| Integration | ❌                | httpx (Litestar test client) | ❌       | Angular TestBed |
| E2E         | ❌                | —              | ✅                 | Playwright |

## Coverage

| Layer    | Available | Command                       |
| -------- | --------- | ----------------------------- |
| Backend  | ❌        | `pytest --cov=app --cov-report=term-missing` |
| Frontend | ❌        | `ng test --no-watch --code-coverage`         |
| E2E      | ✅        | `pnpm test:e2e` (Playwright)                |

## Quality Tools

| Tool         | Backend Available | Backend Command         | Frontend Available | Frontend Command       |
| ------------ | ----------------- | ----------------------- | ------------------ | ---------------------- |
| Linter       | ❌                | `ruff check .`          | ❌                 | `ng lint` (ESLint)     |
| Type checker | ❌                | `mypy .` (planned)      | ✅ (inherent)      | `tsc --noEmit`         |
| Formatter    | ❌                | `ruff format .`         | ❌                 | `prettier --write .`   |

## Notes

- No dependencies installed yet. This project is in PLAN phase.
- pytest + httpx AsyncClient is the recommended backend test stack for Litestar.
- Angular ships with Jasmine/Karma by default; Karma can be replaced with Jest for better DX.
- Once `pyproject.toml` and `package.json` are created, install dependencies and re-scan.
- TypeScript compilation (`tsc`) will be available as soon as Angular config exists.
- Playwright E2E journey tests added (2026-06-25) covering 7 critical user paths: homepage, catalog, product detail, auth, cart, checkout, admin.
- Run with `pnpm test:e2e` from `frontend/` — requires Angular dev server on `:4200` and backend on `:8000`.
- 23 new tests across 7 spec files under `frontend/tests/journeys/`.

---

### Requirement: Real DB Test Fixtures for Cart Service

`backend/tests/integration/test_cart_service.py` MUST run against a real PostgreSQL test database via async session fixtures. The existing `MockAsyncSession`-based unit test for cart MUST be split: pure validation stays as a unit test; anything exercising `CartService` (add, update, remove, clear, get_cart with subtotals, dual-scope) moves to the integration suite.

#### Scenario: Cart integration test uses real DB

- GIVEN `backend/tests/integration/test_cart_service.py` exists
- WHEN the test suite runs
- THEN the file uses an `async_session` fixture bound to a real test PostgreSQL DB
- AND commits real cart operations end-to-end (insert cart item, query, delete)

#### Scenario: Cart unit tests retain MockAsyncSession

- GIVEN pure validation/DTO tests for cart live in `backend/tests/unit/`
- WHEN the test suite runs
- THEN those unit tests MAY use `MockAsyncSession` (legitimate unit-test pattern)

### Requirement: Real DB Test Fixtures for Order Service

`backend/tests/integration/test_order_service.py` MUST run against a real PostgreSQL test database. Order lifecycle tests (create from cart, status transitions, payment) MUST exercise real SQL — not mocks.

#### Scenario: Order integration test uses real DB

- GIVEN `backend/tests/integration/test_order_service.py` exists
- WHEN the test suite runs
- THEN the file uses a real async session fixture
- AND validates order creation, status state machine, and stock decrement end-to-end

#### Scenario: Repository-based order tests

- GIVEN `OrderRepository` already exists
- WHEN the integration tests run
- THEN they verify `OrderService` correctly delegates to `OrderRepository` (no raw `select(Order)` in service)

### Requirement: Real DB Test Fixtures for Review Service

`backend/tests/integration/test_review_service.py` MUST run against a real PostgreSQL test database. Verified-buyer checks, duplicate review rejection, and avg_rating aggregation MUST be tested against real SQL.

#### Scenario: Review integration test uses real DB

- GIVEN `backend/tests/integration/test_review_service.py` exists
- WHEN the test suite runs
- THEN the file uses a real async session fixture
- AND validates create-review (with verified-buyer check), list-with-aggregate, and duplicate-rejection scenarios

### Requirement: conftest.py Real-DB Session Fixtures

`backend/tests/conftest.py` MUST provide async session fixtures backed by a real test PostgreSQL database, following the pattern from `backend/tests/test_seed_integrity.py`. The fixture MUST handle per-test transaction rollback or per-test schema isolation to prevent test pollution.

#### Scenario: async_session fixture is real-DB backed

- GIVEN `backend/tests/conftest.py`
- WHEN inspecting the `async_session` fixture
- THEN it is bound to `TEST_DATABASE_URL` (real PostgreSQL, not SQLite or in-memory)
- AND it yields a working `AsyncSession` whose operations commit to the test DB

#### Scenario: Test isolation between cases

- GIVEN two integration tests run in sequence
- WHEN the first test inserts a cart item
- THEN the second test starts with a clean DB state (no leakage from test 1)

### Requirement: MockAsyncSession Restricted to Unit Tests

`MockAsyncSession` MUST NOT be imported or used in any file under `backend/tests/integration/`. Unit tests under `backend/tests/unit/` (or top-level test files that are explicitly unit tests) MAY continue using it.

#### Scenario: Zero MockAsyncSession in integration tests

- GIVEN `backend/tests/integration/` directory
- WHEN grepping for `MockAsyncSession`
- THEN zero matches exist

#### Scenario: Unit tests retain MockAsyncSession

- GIVEN `backend/tests/unit/test_*_service_validation.py` style files
- WHEN inspecting imports
- THEN `MockAsyncSession` MAY be imported and used (legitimate unit-test pattern preserved)

### Requirement: Reduced MockAsyncSession Edge Count

A future `graphify` run SHALL show `MockAsyncSession` with fewer than 30 edges in the resulting graph (down from 102). This is the architectural success criterion: integration tests replace the heavy mock usage, leaving mocks only for genuine unit-test concerns.

#### Scenario: Graphify post-refactor shows reduction

- GIVEN the refactor lands
- WHEN `graphify` is re-run on the codebase
- THEN `MockAsyncSession` node degree drops below 30
- AND `Select` (SQLAlchemy) betweenness centrality drops below 0.2

---

### Requirement: Homepage E2E Journey
The system MUST pass automated Playwright tests that verify homepage critical content loads without errors.

#### Scenario: Hero banner visible
- GIVEN an unauthenticated user navigates to `/`
- WHEN the page loads
- THEN the hero banner section MUST be visible
- AND the main heading or hero text MUST be present

#### Scenario: Categories carousel loads
- GIVEN the homepage renders
- WHEN the categories section appears
- THEN at least one category item or carousel track MUST be visible

#### Scenario: Featured products display
- GIVEN seed data exists with at least 3 products
- WHEN the homepage renders
- THEN featured product cards MUST be visible in the featured section

### Requirement: Catalog E2E Journey
The system MUST pass automated tests that verify catalog search, filter, sort, and pagination work end-to-end.

#### Scenario: Search returns results
- GIVEN seed data with matching products
- WHEN user types a search term and submits
- THEN product cards matching the query MUST appear
- OR a no-results message MUST display if no match

#### Scenario: Filters narrow results
- GIVEN the catalog page renders with products
- WHEN user selects a category filter or price range
- THEN visible product cards MUST reflect the active filter

#### Scenario: Sort reorders products
- GIVEN the catalog page renders with multiple products
- WHEN user changes sort order (e.g., price low-to-high)
- THEN product card order MUST change accordingly

#### Scenario: Pagination works
- GIVEN seed data exceeds one page of results
- WHEN user clicks next page or page number
- THEN the next set of products MUST load

### Requirement: Product Detail E2E Journey
The system MUST pass automated tests that verify product detail page content renders fully.

#### Scenario: Product images load
- GIVEN a product exists in the catalog
- WHEN user navigates to `/productos/{slug}`
- THEN the main product image MUST be visible

#### Scenario: Reviews section loads
- GIVEN a product has at least one review
- WHEN user navigates to the product detail page
- THEN the reviews section MUST be visible with review content

#### Scenario: Related products display
- GIVEN the catalog has related products for the current item
- WHEN user views the product detail page
- THEN a related-products section MUST render with at least one card

### Requirement: Auth E2E Journey
The system MUST pass automated tests that verify forgot-password and registration-success flows work end-to-end.

#### Scenario: Forgot-password flow submits
- GIVEN a registered user email
- WHEN user navigates to forgot-password page and submits the email
- THEN a success confirmation MUST appear or redirect to a confirmation page

#### Scenario: Registration success page renders
- GIVEN valid registration data
- WHEN user completes the registration form and submits
- THEN user MUST be redirected to a success page or logged-in state

#### Scenario: Auth guard redirects on protected route
- GIVEN an unauthenticated user
- WHEN user navigates to `/carrito`, `/admin`, or `/checkout`
- THEN user MUST be redirected to `/login`

### Requirement: Cart E2E Journey
The system MUST pass automated tests that verify cart item manipulation works end-to-end.

#### Scenario: Add item to cart
- GIVEN an authenticated user on a product detail page
- WHEN user clicks "Add to Cart"
- THEN a snackbar or toast MUST confirm the action

#### Scenario: Update item quantity
- GIVEN an item exists in the cart
- WHEN user changes the quantity via the quantity control
- THEN the cart total MUST update accordingly

#### Scenario: Remove item from cart
- GIVEN an item exists in the cart
- WHEN user clicks the remove/delete action on that item
- THEN the item MUST disappear from the cart table

#### Scenario: Empty cart state
- GIVEN an authenticated user with an empty cart
- WHEN user navigates to `/carrito`
- THEN the empty cart state MUST render with a "continue shopping" link

### Requirement: Checkout E2E Journey
The system MUST pass automated tests that verify the full checkout flow works end-to-end.

#### Scenario: Checkout form validates required fields
- GIVEN an authenticated user on the checkout page with items in cart
- WHEN the form is submitted with empty fields
- THEN validation errors MUST appear on required fields

#### Scenario: Successful order confirmation
- GIVEN an authenticated user with items in cart and valid shipping data
- WHEN user fills the checkout form and confirms the order
- THEN user MUST be redirected to an order confirmation page
- AND the confirmation page MUST display the order ID

### Requirement: Admin E2E Journey
The system MUST pass automated tests that verify admin product creation and order management lifecycle.

#### Scenario: Admin creates a product
- GIVEN an admin-authenticated session
- WHEN admin navigates to `/admin/productos/nuevo` and fills the form
- THEN the new product MUST appear in the admin products table

#### Scenario: Admin manages order status
- GIVEN at least one order exists in the system
- WHEN admin navigates to `/admin/ordenes` and changes an order status
- THEN the status MUST update and reflect in the orders list

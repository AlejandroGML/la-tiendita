# Delta for testing-capabilities

## ADDED Requirements

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

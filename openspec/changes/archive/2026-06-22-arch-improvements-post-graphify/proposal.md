# Proposal: Architectural Improvements Post-Graphify

## Intent

Graphify analysis revealed three structural problems: (1) `Select` (SQLAlchemy) is the #1 bridge node (0.430 betweenness) — raw queries scattered across ~10 services instead of centralized in repositories; (2) `MockAsyncSession` is the #2 god node (102 edges) — 8 test files use a no-op DB mock, inflating inferred edges; (3) `EmailService` has 94 edges partly from 3 dead `provide_email_service()` providers in controllers. Only 4 of ~12 models have repositories. This change consolidates data access behind the repository pattern, removes dead code, and improves test realism.

## Scope

### In Scope
- **P1**: Create 8 new repositories (`VariantRepository`, `CartRepository`, `ReviewRepository`, `PromotionRepository`, `WishlistRepository`, `RefreshTokenRepository`, `PasswordResetTokenRepository`, `DashboardRepository`) inheriting from `BaseRepository[ModelT]`
- **P1**: Migrate raw SQLAlchemy queries from ~10 services to use repository methods (`admin_order_service`, `admin_user_service`, `slug_service`, `stripe_service`, `cart_service`, `review_service`, `promotion_service`, `wishlist_service`, `variant_service`, `token_service`, `password_reset_service`, `dashboard_service`)
- **P2**: Remove 3 unused `provide_email_service()` providers from `controllers/auth.py`, `controllers/orders.py`, `controllers/admin.py`
- **P3**: Extend real-DB integration tests (pattern from `test_seed_integrity.py`) to cart, orders, reviews; restrict `MockAsyncSession` to unit tests only

### Out of Scope
- Frontend changes (Angular)
- New features or endpoints
- `ProductRepository`/`OrderRepository`/`UserRepository`/`CategoryRepository` refactor (already exist)
- Full `MockAsyncSession` elimination (kept for legitimate unit tests)

## Capabilities

### New Capabilities
None — this is an internal architectural refactor with no new user-facing behavior.

### Modified Capabilities
- `backend-core`: Repository pattern completion — 8 new repos + query migration from services; dead provider cleanup; hybrid test DB strategy
- `cart`: CartService queries move to CartRepository
- `reviews`: ReviewService queries move to ReviewRepository
- `wishlist`: WishlistService queries move to WishlistRepository
- `promotions`: PromotionService queries move to PromotionRepository
- `product-variants`: VariantService queries move to VariantRepository
- `admin-dashboard`: DashboardService queries move to DashboardRepository; dead email provider removed from admin controller
- `email-notifications`: Dead `provide_email_service()` providers removed from 3 controllers
- `testing-capabilities`: Hybrid test DB — integration tests for cart/orders/reviews using real DB

## Approach

1. **Repository creation**: Each new repo extends `BaseRepository[ModelT]`, adding domain-specific query methods. Services receive repos via constructor injection (Litestar DI).
2. **Query migration**: Replace `select(...)` calls in services with `repo.method()` calls. One service at a time, starting with leaf services (no downstream deps).
3. **Dead code removal**: Delete unused `provide_email_service()` functions and their imports.
4. **Test hybridization**: Add `conftest.py` fixtures for real async DB sessions (following `test_seed_integrity.py` pattern). Convert integration test files; keep `MockAsyncSession` for pure unit tests.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/repositories/` | New | 8 new repository files |
| `backend/app/services/` (~10 files) | Modified | Raw queries → repo method calls |
| `backend/app/controllers/auth.py` | Modified | Remove dead `provide_email_service()` |
| `backend/app/controllers/orders.py` | Modified | Remove dead `provide_email_service()` |
| `backend/app/controllers/admin.py` | Modified | Remove dead `provide_email_service()` |
| `backend/tests/` (~8 files) | Modified | Integration tests use real DB; unit tests keep mocks |
| `backend/tests/conftest.py` | Modified | Add real-DB session fixtures |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Query behavior change during migration | Medium | Keep existing tests green; add integration tests per repo before migrating its service |
| DI wiring errors for new repos | Low | Litestar dependency injection is type-checked; run existing test suite after each repo addition |
| Real-DB tests slower than mocks | Low | Scope integration tests to critical paths only; keep unit tests fast with mocks |

## Rollback Plan

Git revert. Each priority level (P1/P2/P3) is an independent commit group — revert individually if needed. No DB migrations involved.

## Dependencies

- Existing `BaseRepository[ModelT]` in `backend/app/repositories/base.py`
- Existing `test_seed_integrity.py` as reference pattern for real-DB tests
- Litestar DI system for repository injection

## Success Criteria

- [ ] All 12 models have corresponding repositories
- [ ] Zero raw `select()` calls in service layer (verified by grep)
- [ ] Zero unused `provide_email_service()` providers (verified by grep)
- [ ] `MockAsyncSession` edge count drops below 30 in next graphify run
- [ ] All existing tests pass; new integration tests cover cart, orders, reviews
- [ ] `Select` betweenness centrality drops below 0.2 in next graphify run

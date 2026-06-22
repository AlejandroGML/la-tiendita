# Design: Architectural Improvements Post-Graphify

## Technical Approach

Leaf-first migration: create 8 repositories extending `BaseRepository[ModelT]` (except Dashboard and Wishlist), then migrate raw `select()` calls from 12 services/controllers to repo methods. Delete 3 dead `provide_email_service()` providers. Add real-DB session fixtures to `conftest.py` for integration tests.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| WishlistRepository base | Standalone (not `BaseRepository`) | `Wishlist` inherits `_CompositeBase`, not `Base` — `ModelT` bound incompatible. Methods are domain-specific: `upsert`, `list_by_user`, `delete` by composite PK |
| DashboardRepository base | Standalone | Multi-model aggregate queries (Product, User, Order, Review, Promotion). No single model to bind |
| CartRepository upsert | Repo-owns upsert via partial-index aware logic | CartItem has 4 partial unique indexes. Upsert requires explicit `select`-then-`update`/`insert` — cannot use `ON CONFLICT` directly |
| TokenRepository naming | `RefreshTokenRepository` (model=RefreshToken), `PasswordResetTokenRepository` (model=PasswordResetToken) | Follows `{Model}Repository` convention from existing repos (ProductRepository, UserRepository, OrderRepository) |
| `session` fixture isolation | Per-test rollback (existing pattern from conftest.py L93-105) | Proven pattern; `async with _maker() as s: yield s; await s.rollback()` ensures zero cross-test pollution |
| categories.py L216 fix | Add `count_products` method to existing `CategoryRepository` | Controller already receives `CategoryRepository` via DI; minimal refactor to existing repo |

## Repository Skeletons (P1)

### 1. VariantRepository

```python
class VariantRepository(BaseRepository[ProductVariant]):
    def __init__(self) -> None:
        super().__init__(ProductVariant)

    async def get_by_product(self, session: AsyncSession, product_id: UUID) -> list[ProductVariant]:
        # select(Variant).where(product_id==, deleted_at.is_(None)).order_by(created_at)
    async def get_by_sku(self, session: AsyncSession, sku: str) -> ProductVariant | None:
        # find_one(ProductVariant.sku == sku)
    async def get_active_for_product(self, session: AsyncSession, product_id: UUID) -> list[ProductVariant]:
        # find_all(product_id==, deleted_at.is_(None), stock > 0)
    async def decrement_stock(self, session: AsyncSession, variant_id: UUID, qty: int) -> None:
        # update stock -= qty with FOR UPDATE
```

### 2. CartRepository

```python
class CartRepository(BaseRepository[CartItem]):
    def __init__(self) -> None:
        super().__init__(CartItem)

    async def get_items(self, session, *, user_id=None, session_id=None) -> list[CartItem]:
        # find_all with scope filter + selectinload(Product), selectinload(Variant)
    async def upsert_item(self, session, *, user_id, session_id, product_id, variant_id, qty, unit_price) -> CartItem:
        # SELECT existing via scope+product+variant; if found UPDATE qty+price, else INSERT
    async def update_qty(self, session, item_id, qty) -> None:
    async def remove_item(self, session, item_id) -> None:
    async def clear_scope(self, session, *, user_id=None, session_id=None) -> None:
```

### 3. ReviewRepository

```python
class ReviewRepository(BaseRepository[Review]):
    def __init__(self) -> None:
        super().__init__(Review)

    async def get_by_product(self, session, product_id, page, per_page) -> tuple[list[Review], int]:
    async def create_review(self, session, user_id, product_id, rating, comment) -> Review:
    async def get_aggregate(self, session, product_id) -> dict:  # avg_rating, total_reviews
    async def user_has_purchased(self, session, user_id, product_id) -> bool:
```

### 4. PromotionRepository

```python
class PromotionRepository(BaseRepository[Promotion]):
    def __init__(self) -> None:
        super().__init__(Promotion)

    async def get_active(self, session, lang: str) -> list[Promotion]:
        # filter is_active=True, date range, max_uses; eagerload translations
    async def get_by_code(self, session, code: str) -> Promotion | None:
    async def get_best_for_product(self, session, product_id) -> Promotion | None:
```

### 5. WishlistRepository

```python
class WishlistRepository:
    """Standalone — Wishlist uses composite PK, not Base."""
    
    async def get_by_user(self, session, user_id, lang: str) -> list[Wishlist]:
        # select(Wishlist).where(user_id==).options(joinedload(product).joinedload(translations))
    async def upsert(self, session, user_id, product_id) -> bool:
        # INSERT or return False if exists (idempotent)
    async def remove(self, session, user_id, product_id) -> None:
        # delete().where(user_id==, product_id==)
```

### 6. RefreshTokenRepository

```python
class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self) -> None:
        super().__init__(RefreshToken)

    async def save_token(self, session, token: RefreshToken) -> RefreshToken:
    async def find_by_user(self, session, user_id) -> list[RefreshToken]:
    async def delete_token(self, session, token: RefreshToken) -> None:
    async def delete_user_tokens(self, session, user_id) -> None:
    async def delete_expired(self, session) -> int:
```

### 7. PasswordResetTokenRepository

```python
class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    def __init__(self) -> None:
        super().__init__(PasswordResetToken)

    async def save_token(self, session, token: PasswordResetToken) -> PasswordResetToken:
    async def find_valid(self, session, user_id) -> PasswordResetToken | None:
        # where user_id==, used==False, expires_at > now()
    async def invalidate_token(self, session, token: PasswordResetToken) -> None:
        # token.used = True; flush
```

### 8. DashboardRepository

```python
class DashboardRepository:
    """Multi-model aggregate repository — no single model bound."""

    async def get_total_products(self, session) -> int:
    async def get_total_users(self, session) -> int:
    async def get_total_orders(self, session) -> int:
    async def get_recent_orders(self, session, limit=5) -> list[Order]:
    async def get_total_revenue(self, session) -> Decimal:
    async def compute_stats(self, session) -> dict:  # all 12 fields in one call
```

## Service Migration: Before/After Examples

| Service | Before | After |
|---------|--------|-------|
| `variant_service.py:47` | `select(ProductVariant).where(...)` | `variant_repo.get_by_product(session, product_id)` |
| `token_service.py:155` | `select(RefreshToken).where(user_id==).with_for_update()` | `token_repo.find_by_user(session, user_id)` |
| `token_service.py:242` | `select(RefreshToken).where(user_id==)` + manual delete loop | `token_repo.delete_user_tokens(session, user_id)` |
| `cart_service.py:281` | `select(CartItem).where(scope filter)` | `cart_repo.get_items(session, user_id=...)` |
| `wishlist_service.py:37` | `select(Wishlist).where(user_id==)` | `wishlist_repo.get_by_user(session, user_id, lang)` |
| `admin_order_service.py:54` | `select(Order).options(selectinload(Order.user))` | `order_repo.get_all_with_user(session, page, per_page)` (extend existing OrderRepository) |
| `slug_service.py:60` | `select(Product.id).where(slug==)` | `product_repo.get_by_slug(session, slug)` |
| `stripe_service.py:357` | `select(Order).where(id==)` | `order_repo.get_by_id(session, order_id)` |
| `email_service.py:214` | `select(User).where(id==)` | `user_repo.get_by_id(session, user_id)` |
| `password_reset_service.py:99` | `select(PasswordResetToken).where(...)` | `pwd_reset_repo.find_valid(session, user_id)` |
| `review_service.py:78` | `select(Review).where(product_id==)` | `review_repo.get_by_product(session, product_id, page, per_page)` |
| `promotion_service.py:50` | `select(Promotion).where(is_active==True)` | `promotion_repo.get_active(session, lang)` |
| `dashboard_service.py:67-120` | 13 raw aggregate `select(func.count())` calls | `dashboard_repo.compute_stats(session)` |
| `admin_user_service.py:37-53` | `select(User)` + `select(func.count(Order.id))` | `user_repo.get_paginated(...)`, `order_repo.count_by_user(session, user_id)` |
| `controllers/categories.py:216` | `select(func.count(Product.id)).where(category_id==)` | `category_repo.count_products(session, category_id)` |

## P2: Dead Code Cleanup

Delete 3 identical `provide_email_service()` blocks — EmailService is already registered globally:

| File | Lines | Delete |
|------|-------|--------|
| `controllers/auth.py` | 46-50 | `def provide_email_service()` + its body |
| `controllers/orders.py` | 53-57 | `def provide_email_service()` + its body |
| `controllers/admin.py` | 71-75 | `def provide_email_service()` + its body |

Also remove any remaining references in each controller's `dependencies` dict if present (auth.py currently does NOT reference it in its deps — verify the other two).

## P3: Hybrid Test Database

### conftest.py changes

The `session` fixture already exists (L92-105) with real `AsyncSession` + rollback. It is available across all tests via `pytest_asyncio`. Add a scoped variant for integration suites:

```python
# conftest.py — NEW fixture
@pytest_asyncio.fixture(scope="function")
async def real_db_session() -> AsyncSession:
    """Real PostgreSQL session for integration tests — same as `session` but
    explicitly named for integration test files to import."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from app.config import settings
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
        await s.rollback()
    await engine.dispose()
```

### Usage in integration tests

```python
# tests/integration/test_cart_repository.py
@pytest.mark.asyncio
async def test_upsert_and_list(real_db_session: AsyncSession):
    repo = CartRepository()
    await repo.upsert_item(real_db_session, user_id=uid, product_id=pid, ...)
    items = await repo.get_items(real_db_session, user_id=uid)
    assert len(items) == 1
```

`MockAsyncSession` stays in `tests/unit/` files and in files testing pure logic (validators, DTOs, auth guards). Integration test files under `tests/integration/` use only `real_db_session`.

## File Changes

### P1: New Files (8 repos + __init__ update)

| File | Action |
|------|--------|
| `backend/app/repositories/variant_repository.py` | Create |
| `backend/app/repositories/cart_repository.py` | Create |
| `backend/app/repositories/review_repository.py` | Create |
| `backend/app/repositories/promotion_repository.py` | Create |
| `backend/app/repositories/wishlist_repository.py` | Create |
| `backend/app/repositories/refresh_token_repository.py` | Create |
| `backend/app/repositories/password_reset_token_repository.py` | Create |
| `backend/app/repositories/dashboard_repository.py` | Create |
| `backend/app/repositories/__init__.py` | Modify (export new repos) |

### P1: Service Modifications

| File | Action | Scope |
|------|--------|-------|
| `services/variant_service.py` | Modify | Migrate 5 raw queries → VariantRepository |
| `services/cart_service.py` | Modify | Migrate raw queries → CartRepository; inject CartRepository in __init__ |
| `services/review_service.py` | Modify | Migrate raw queries → ReviewRepository |
| `services/promotion_service.py` | Modify | Migrate raw queries → PromotionRepository |
| `services/wishlist_service.py` | Modify | Migrate raw queries → WishlistRepository |
| `services/token_service.py` | Modify | Migrate RefreshToken queries → RefreshTokenRepository |
| `services/password_reset_service.py` | Modify | Migrate PasswordResetToken queries → PasswordResetTokenRepository |
| `services/dashboard_service.py` | Modify | Migrate 13 aggregate queries → DashboardRepository |
| `services/admin_order_service.py` | Modify | Use OrderRepository methods; add `get_all_with_user` to OrderRepository |
| `services/admin_user_service.py` | Modify | Use UserRepository + OrderRepository methods |
| `services/email_service.py` | Modify | Use UserRepository (already injects it?) |
| `services/slug_service.py` | Modify | Use ProductRepository.get_by_slug |
| `services/stripe_service.py` | Modify | Use OrderRepository.get_by_id |
| `services/order_service.py` | Modify | Use CartRepository for cart reads, VariantRepository for stock checks |

### P1: Existing Repository Extensions

| File | Action | Description |
|------|--------|-------------|
| `repositories/order_repository.py` | Modify | Add `get_all_with_user`, `count_by_user` |
| `repositories/category_repository.py` | Modify | Add `count_products` |

### P2: Dead Code

| File | Action | Lines |
|------|--------|-------|
| `controllers/auth.py` | Modify | Delete L46-50 |
| `controllers/orders.py` | Modify | Delete L53-57 |
| `controllers/admin.py` | Modify | Delete L71-75 |

### P3: Tests

| File | Action |
|------|--------|
| `tests/conftest.py` | Modify (add `real_db_session` fixture) |
| `tests/integration/test_variant_repository.py` | Create |
| `tests/integration/test_cart_repository.py` | Create |
| `tests/integration/test_review_repository.py` | Create |
| `tests/integration/test_promotion_repository.py` | Create |
| `tests/integration/test_wishlist_repository.py` | Create |
| `tests/integration/test_refresh_token_repository.py` | Create |
| `tests/integration/test_password_reset_token_repository.py` | Create |
| `tests/integration/test_dashboard_repository.py` | Create |
| `tests/integration/test_cart_service.py` | Create (migrate from mock-based) |
| `tests/integration/test_order_service.py` | Create |
| `tests/integration/test_review_service.py` | Create |

## Migration Order

Leaf repositories have no dependencies — create them first:

1. **P1a — Repos with zero deps**: Variant, Cart, Review, Promotion, RefreshToken, PasswordResetToken, Dashboard
2. **P1a — WishlistRepository**: after P1a (standalone, no BaseRepository dep)
3. **P1b — Extend existing repos**: OrderRepository.add methods, CategoryRepository.add methods
4. **P1c — Service migrations**: token_service, password_reset_service (leaf services) → cart_service → wishlist_service → review_service → promotion_service → variant_service → admin_user_service → admin_order_service → email_service → slug_service → stripe_service → dashboard_service → order_service (most deps)
5. **P1c — Controller fix**: categories.py L216 → CategoryRepository
6. **P2 — Dead code**: order-independent, can run anytime
7. **P3 — Tests**: after each repo or service migration

## Open Questions

- None — all technical decisions resolved from existing patterns in `base.py`, `product_repository.py`, `order_repository.py`, and `conftest.py`.

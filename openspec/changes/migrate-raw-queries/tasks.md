# Tasks: Migrate Remaining Raw SQLAlchemy Calls

## Review Workload Forecast

- **400-line budget risk**: Low (~20-40 changed lines)
- **Chained PRs recommended**: No
- **Decision needed before apply**: No

## Phase 1: Repository Methods

- [x] 1.1 Add `update_password_hash()` method to `UserRepository`
  - File: `backend/app/repositories/user_repository.py`
  - Fetch user via inherited `get_by_id()`, set `password_hash` attribute, flush

## Phase 2: Service Refactors

- [x] 2.1 Replace `session.delete()` in `cart_service.py` `update_quantity()`
  - Line 227: replace `await session.delete(cart_item); await session.flush()` with `await self._cart_repo.remove_item(session, item_id)`

- [x] 2.2 Replace `session.delete()` in `cart_service.py` `remove_item()`
  - Line 256: replace `await session.delete(cart_item); await session.flush()` with `await self._cart_repo.remove_item(session, item_id)`

- [x] 2.3 Replace raw `update(User).values(...)` in `password_reset_service.py`
  - Lines 113-117: replace with `await self._user_repo.update_password_hash(session, matched.user_id, new_hash)`

## Phase 3: Cleanup

- [x] 3.1 Remove unused SQLAlchemy imports from `cart_service.py`
  - Remove `delete`, `select`, `update` from the `from sqlalchemy import …` line
  - Also removed unused `selectinload` from `sqlalchemy.orm` and unused `User`/`select` from `password_reset_service.py`
  - Keep `ColumnElement` (still used by `_scope_filter`)

## Phase 4: Verification

- [x] 4.1 Run `rg "\.(update|delete)\(" backend/app/services/` — MUST be empty ✅
- [x] 4.2 Run Python import check: `python -c "from app.repositories.cart_repository import CartRepository; print('OK')"` ✅
- [x] 4.3 Run Python import check: `python -c "from app.repositories.user_repository import UserRepository; print('OK')"` ✅

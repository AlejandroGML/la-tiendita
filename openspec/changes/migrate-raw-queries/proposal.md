# Proposal: Migrate Remaining Raw SQLAlchemy Calls

## Intent

Finish the repository pattern migration. Three raw `update()` / `delete()` SQLAlchemy
calls remain in service-layer code, violating the architectural rule "only repositories
touch SQLAlchemy". This mechanical refactor moves them into their respective repositories.

## Scope

| In Scope | Out of Scope |
|----------|-------------|
| `cart_service.py`: replace `session.delete(cart_item)` ×2 with `CartRepository.remove_item()` | `session.add()` calls in services |
| `password_reset_service.py`: replace raw `update(User).values(...)` with `UserRepository.update_password_hash()` | Flushing strategy / transaction boundaries |
| Unused `delete`, `select`, `update` import cleanup in `cart_service.py` | New validation or error handling |

## Capabilities

### Modified Capabilities
- `cart`: CartService delegates item deletion to `CartRepository.remove_item()` (already exists).
- `password-reset`: PasswordResetService delegates password-hash update to `UserRepository.update_password_hash()` (new method).

## Approach

| Phase | Action |
|-------|--------|
| 1 | Add `update_password_hash()` to `UserRepository` — fetch user by ID, set `password_hash`, flush |
| 2 | Replace `session.delete(cart_item)` ×2 in `CartService` with `self._cart_repo.remove_item()` |
| 3 | Replace raw `update(User).values(password_hash=…)` in `PasswordResetService` with `self._user_repo.update_password_hash()` |
| 4 | Clean up unused SQLAlchemy imports from `cart_service.py` |

## Risk

**Low.** Mechanical refactor. `CartRepository.remove_item()` already exists and is
tested. `UserRepository.update_password_hash()` is a trivial get-and-set on
`BaseRepository.get_by_id()`. No API surface change. Scope validation is already
performed by `_get_own_item()` before the repo call in the cart service.

## Rollback

Revert the 3 call sites to their original raw SQLAlchemy calls. No database
schema changes, no migration needed.

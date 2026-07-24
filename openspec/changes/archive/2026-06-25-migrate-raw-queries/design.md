# Design: Migrate Remaining Raw SQLAlchemy Calls

## Architecture Decision

### Cart Deletion → CartRepository.remove_item()

`CartRepository` already provides a `remove_item(session, item_id)` method
(which delegates to `_delete_by_id`). The service performs scope validation
via `_get_own_item()` before the delete, so the repo does not need to
re-validate scope.

```
Before (line 227, update_quantity):
  cart_item = await self._get_own_item(session, user_id, session_id, item_id)
  if data.quantity == 0:
      await session.delete(cart_item)       ← raw
      await session.flush()

After:
  cart_item = await self._get_own_item(session, user_id, session_id, item_id)
  if data.quantity == 0:
      await self._cart_repo.remove_item(session, item_id)
```

```
Before (line 256, remove_item):
  cart_item = await self._get_own_item(session, user_id, session_id, item_id)
  await session.delete(cart_item)           ← raw
  await session.flush()

After:
  cart_item = await self._get_own_item(session, user_id, session_id, item_id)
  await self._cart_repo.remove_item(session, item_id)
```

**Tradeoff**: `CartRepository._delete_by_id()` re-fetches the item by ID
before deleting (one extra SELECT). The scope check already validated
ownership, so the re-fetch is a minor cost for architectural purity.

### Password Hash Update → UserRepository.update_password_hash()

`UserRepository` inherits `BaseRepository.get_by_id()`. The new method is
a thin wrapper:

```python
# backend/app/repositories/user_repository.py (new method)
async def update_password_hash(
    self, session: AsyncSession, user_id: UUID, password_hash: str
) -> None:
    user = await self.get_by_id(session, user_id)
    if user:
        user.password_hash = password_hash
        await session.flush()
```

```
Before (password_reset_service.py line 113-117):
  await session.execute(
      __import__("sqlalchemy").update(User)
      .where(User.id == matched.user_id)
      .values(password_hash=new_hash)
  )

After:
  await self._user_repo.update_password_hash(
      session, matched.user_id, new_hash
  )
```

### Import Cleanup in cart_service.py

After migration, `cart_service.py` no longer uses `delete`, `select`, or
`update` from `sqlalchemy`. Remove them from the import line:

```python
# Before:
from sqlalchemy import ColumnElement, delete, select, update

# After:
from sqlalchemy import ColumnElement
```

## Files Changed

| File | Action |
|------|--------|
| `backend/app/repositories/user_repository.py` | Add `update_password_hash()` method |
| `backend/app/services/cart_service.py` | Replace 2 `session.delete()` calls + clean imports |
| `backend/app/services/password_reset_service.py` | Replace raw `update(User).values()` call |

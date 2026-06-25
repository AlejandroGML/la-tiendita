# Delta Spec: Backend Core — Repository Purity

## ADDED Requirements

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

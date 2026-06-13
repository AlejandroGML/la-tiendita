# Delta for Wishlist

## MODIFIED Requirements

### Requirement: Wishlist Is User-Scoped
Backend: All operations remain scoped to JWT user. Unauthenticated requests SHALL return 401 (unchanged). Frontend: the public /wishlist route SHALL display a login prompt card instead of redirecting to /login. The authenticated /perfil/wishlist route SHALL remain under authGuard.
(Previously: unauthenticated access redirected to /login on frontend.)

#### Scenario: Unauthenticated backend access returns 401
- GIVEN no JWT token
- WHEN GET /api/wishlist
- THEN returns 401 (backend unchanged)

#### Scenario: Public wishlist route shows login prompt
- GIVEN unauthenticated user navigates to /wishlist
- WHEN Angular router loads the page
- THEN UI displays login prompt card; no redirect to /login

#### Scenario: Authenticated /perfil/wishlist unchanged
- GIVEN authenticated user navigates to /perfil/wishlist
- WHEN Angular router loads the page under authGuard
- THEN wishlist items display normally

# Delta Specs — arch-improvements-post-graphify

Quick reference for the 9 delta specs produced by `sdd-spec` for this change.

## Specs

| Domain | File | Priority | Type | Focus |
|--------|------|----------|------|-------|
| `backend-core` | [backend-core/spec.md](./backend-core/spec.md) | P1 + P2 + P3 | Cross-cutting | 8 new repos, no raw selects in services, dead provider removal, hybrid test DB |
| `cart` | [cart/spec.md](./cart/spec.md) | P1 | Service-repo | CartService → CartRepository |
| `product-variants` | [product-variants/spec.md](./product-variants/spec.md) | P1 | Service-repo | VariantService → VariantRepository |
| `reviews` | [reviews/spec.md](./reviews/spec.md) | P1 | Service-repo | ReviewService → ReviewRepository |
| `wishlist` | [wishlist/spec.md](./wishlist/spec.md) | P1 | Service-repo | WishlistService → WishlistRepository |
| `promotions` | [promotions/spec.md](./promotions/spec.md) | P1 | Service-repo | PromotionService → PromotionRepository |
| `admin-dashboard` | [admin-dashboard/spec.md](./admin-dashboard/spec.md) | P1 + P2 | Service-repo + dead code | DashboardService → DashboardRepository; admin controller provider removed |
| `email-notifications` | [email-notifications/spec.md](./email-notifications/spec.md) | P1 + P2 | Service-repo + dead code | EmailService → UserRepository; 3 dead providers removed |
| `testing-capabilities` | [testing-capabilities.md](./testing-capabilities.md) | P3 | Test strategy | Real-DB integration tests for cart/orders/reviews; MockAsyncSession → unit tests only |

## Summary of Changes per Spec

| Domain | Added | Modified | Removed |
|--------|------:|---------:|--------:|
| backend-core | 6 | 0 | 0 |
| cart | 1 | 0 | 0 |
| product-variants | 1 | 0 | 0 |
| reviews | 1 | 0 | 0 |
| wishlist | 1 | 0 | 0 |
| promotions | 1 | 0 | 0 |
| admin-dashboard | 2 | 0 | 0 |
| email-notifications | 4 | 0 | 0 |
| testing-capabilities | 6 | 0 | 0 |
| **Totals** | **23** | **0** | **0** |

## Why Only ADDED (No MODIFIED)

This change is a **purely internal architectural refactor**. No user-facing behavior changes. The existing functional requirements (add to cart, create review, etc.) remain valid and unchanged. The new requirements describe:
- New repository classes and their contract
- Service layer constraints (no raw queries, repo injection)
- Test strategy (real DB for integration, mocks for unit)
- Dead code removal (no `provide_email_service()` in 3 controllers)

When `sdd-archive` runs, every ADDED block is appended to its main spec — no existing requirements are modified or removed.

## Coverage Check

| Concern | Covered? | Notes |
|---------|:--------:|-------|
| Happy path (service uses repo) | Yes | Each domain spec includes a "service method uses repo" scenario |
| Edge case (grep verification) | Yes | `backend-core` includes `rg "select\("` zero-match scenario |
| Error states (DI wiring) | Implicit | Constructor-injection requirement; Litestar DI type-checked |
| Dead code removal | Yes | 3 separate grep-verification scenarios across auth/orders/admin |
| Real DB test isolation | Yes | `testing-capabilities` includes test pollution prevention scenario |

## Next Step

Ready for `sdd-design`. The design phase will produce:
- Repo class skeletons and their method signatures
- DI wiring patterns (Litestar `Provide` per repo)
- Test fixture design (conftest.py real-DB session)
- Migration order (leaf services first to avoid cascade breakage)

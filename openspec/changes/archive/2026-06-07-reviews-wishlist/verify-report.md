## Verification Report

**Change**: reviews-wishlist
**Version**: 1.0
**Mode**: Standard

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 27 |
| Tasks complete | 27 |
| Tasks incomplete | 0 |

### Build & Tests Execution
**Build**: ✅ Passed (Angular 22 compilation + Litestar import check)
```text
Backend: no explicit build step — controller/service/model imports validated by test runner.
Frontend: ng test compiles all TypeScript successfully (17/21 test files pass).
```

**Tests**:
- Backend: ✅ 163 passed / ❌ 0 failed
- Frontend: ✅ 237 passed / ❌ 6 failed (all 6 pre-existing in app.spec.ts, cart.spec.ts, order-detail.spec.ts, order-list.spec.ts)
- New frontend tests: ✅ 52 passed (star-rating 19, wishlist 16, admin-promotions 17)

```text
Backend (venv Python): 163 passed, 386 warnings in 6.47s
Frontend (ng test): 17 passed, 4 failed test files (243 tests: 237 passed, 6 failed, 2 errors)
  New test files: star-rating.spec.ts ✅, wishlist.spec.ts ✅, admin-promotions.spec.ts ✅
  Pre-existing failures: app.spec.ts (2), cart.spec.ts (1), order-detail.spec.ts (1), order-list.spec.ts (2)
```

**Coverage**: ➖ Not available (no coverage config for backend or frontend)

### Spec Compliance Matrix

#### Backend: reviews
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1: Create review (verified buyer) | Verified buyer creates review → 201 | (none found) | ❌ UNTESTED |
| R1: Create review (verified buyer) | Non-buyer rejected → 403 | (none found) | ❌ UNTESTED |
| R1: Create review (verified buyer) | Unauthenticated rejected → 401 | (none found) | ❌ UNTESTED |
| R2: Get product reviews + avg | Product with reviews returns array + avg_rating | (none found) | ❌ UNTESTED |
| R2: Get product reviews + avg | Product without reviews returns empty + avg=0 | (none found) | ❌ UNTESTED |
| R3: One review per user per product | Duplicate review rejected → 409 | (none found) | ❌ UNTESTED |
| R4: Rating validation | Invalid rating (0) → 422 | (none found) | ❌ UNTESTED |

#### Backend: wishlist
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1: List wishlist items | User with items → 200 with array | (none found) | ❌ UNTESTED |
| R1: List wishlist items | Empty wishlist → 200 empty array | (none found) | ❌ UNTESTED |
| R2: Add product | New product → 201 | (none found) | ❌ UNTESTED |
| R2: Add product | Duplicate add idempotent → 200 | (none found) | ❌ UNTESTED |
| R2: Add product | Non-existent product → 404 | (none found) | ❌ UNTESTED |
| R3: Remove product | Remove existing → 204 | (none found) | ❌ UNTESTED |
| R3: Remove product | Remove non-existent → 404 | (none found) | ❌ UNTESTED |
| R4: User-scoped | Unauthenticated → 401 | (none found) | ❌ UNTESTED |

#### Backend: promotions
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| R1: Admin CRUD | Create promotion → 201 | (none found) | ❌ UNTESTED |
| R1: Admin CRUD | List all promotions (admin) | (none found) | ❌ UNTESTED |
| R1: Admin CRUD | Update promotion → 200 | (none found) | ❌ UNTESTED |
| R1: Admin CRUD | Delete promotion → 204 | (none found) | ❌ UNTESTED |
| R1: Admin CRUD | Non-admin rejected → 403 | (none found) | ❌ UNTESTED |
| R2: List active (public) | Active within date range returned | (none found) | ❌ UNTESTED |
| R2: List active (public) | Max uses exhausted → hidden | (none found) | ❌ UNTESTED |
| R3: Validation | Invalid date range → 422 | (none found) | ❌ UNTESTED |
| R3: Validation | Duplicate code → 409 | (none found) | ❌ UNTESTED |
| R4: Translations | Multi-language titles via ?lang= | (none found) | ❌ UNTESTED |

#### Backend: backend-core delta
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| MOD: Controller registration | Review/wishlist endpoints in OpenAPI | (none found) | ❌ UNTESTED |
| MOD: Controller registration | Promotion endpoints in OpenAPI | (none found) | ❌ UNTESTED |
| MOD: Model discovery | Autogenerate detects new tables | (none found) | ❌ UNTESTED |

#### Frontend: frontend-core delta
| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| MOD: Wishlist route | `/perfil/wishlist` renders, requires auth | `wishlist.spec.ts` > loads module | ⚠️ PARTIAL |
| MOD: Admin promotions route | `/admin/promociones` requires admin guard | Angular compiler validates route config | ⚠️ PARTIAL |
| ADD: Star-rating component | Read-only star display (4 filled, 1 empty) | `star-rating.spec.ts` > starFill tests | ✅ COMPLIANT |
| ADD: Star-rating component | Editable star selection (click → emit 5) | `star-rating.spec.ts` > handleClick tests | ✅ COMPLIANT |
| ADD: Star-rating component | Zero rating renders all empty | `star-rating.spec.ts` > rating=0 test | ✅ COMPLIANT |
| ADD: Star-rating component | Keyboard support (Enter/Space) | `star-rating.spec.ts` > handleKeydown tests | ✅ COMPLIANT |

**Compliance summary**: 5/28 scenarios fully compliant, 2 PARTIAL, 21 UNTESTED

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|------------|--------|-------|
| Review model + UNIQUE(user,product) | ✅ Implemented | `backend/app/models/review.py` — composite unique constraint, FK to users+products, ck_review_rating_range |
| Wishlist composite PK | ✅ Implemented | `backend/app/models/wishlist.py` — PK (user_id, product_id) per design |
| Promotion + translations | ✅ Implemented | `backend/app/models/promotion.py` — Promotion + PromotionTranslation models |
| Pydantic schemas | ✅ Implemented | `review.py`, `wishlist.py`, `promotion.py` — all fields with validation |
| ReviewController (POST JWT, GET public) | ✅ Implemented | `backend/app/controllers/reviews.py` |
| WishlistController (JWT CRUD) | ✅ Implemented | `backend/app/controllers/wishlist.py` |
| Promotion/AdminPromotion controllers | ✅ Implemented | `backend/app/controllers/promotions.py` |
| Controller registration in main.py | ✅ Implemented | All 4 controllers registered at lines 55-66 |
| Migration (Alembic 0004) | ✅ Implemented | Creates reviews, wishlist, promotions, promotion_translations with indexes, FKs, check constraints |
| env.py model imports | ✅ Implemented | review, wishlist, promotion modules imported for autogenerate |
| TypeScript models | ✅ Implemented | review.model.ts, wishlist.model.ts, promotion.model.ts |
| StarRatingComponent | ✅ Implemented | With @Input rating/readonly/size, @Output ratingChange, aria+keyboard |
| Wishlist page | ✅ Implemented | Lazy-loaded WishlistModule, grid with remove, empty/error states |
| Admin promotions page | ✅ Implemented | Table CRUD + ReactiveForm with FormArray translations, status chips |
| Routes | ✅ Implemented | `/perfil/wishlist` (authGuard), `/admin/promociones` (authGuard+adminGuard) |
| i18n keys | ✅ Implemented | es.json, en.json, sv.json updated with reviews/wishlist/promotions keys |

### Coherence (Design)
| Decision | Followed? | Notes |
|----------|-----------|-------|
| Review validation via completed orders JOIN | ✅ Yes | `review_service.can_review()` queries orders+order_items with status IN (confirmed,shipped,delivered) |
| Wishlist composite PK (user_id, product_id) | ✅ Yes | Matches CartItem pattern |
| Promotion active filter in service layer | ✅ Yes | `list_active_promotions()` filters by date range + max_uses |
| Server-side SQL AVG for avg_rating | ✅ Yes | `func.avg(Review.rating)` in `list_reviews()` |
| Star-rating reusable shared component | ✅ Yes | Used `@Input`/`@Output` per design |
| Star-rating template: span vs mat-icon | ⚠️ Deviation | Used `<span class="material-icons">` instead of `<mat-icon>` to avoid host binding issues in test environment (noted in apply-progress) |
| Admin form 3 default translations (es/en/sv) | ⚠️ Deviation | Matches existing admin product form pattern — acceptable |
| SharedModule CommonModule | ⚠️ Deviation | Added to support ngClass/ngFor in templates — minor |

### Issues Found
**CRITICAL**: 
- **Zero backend tests for reviews, wishlist, or promotions features.** The design.md explicitly specified: unit tests for `can_review()` SQL query, integration tests for POST review 403 (non-buyer), wishlist CRUD flow, and admin promotion CRUD cycle. None of these 21 backend spec scenarios have covering tests. Pre-existing 163 tests all pass without regression, but no new backend tests were added.
- **Backend spec compliance cannot be verified.** 22 spec scenarios (reviews R1-R4, wishlist R1-R5, promotions R1-R4, backend-core) are UNTESTED against the backend implementation.

**WARNING**:
- Frontend tests are component-level only; no HTTP service-level integration tests verify actual API contracts for review, wishlist, or promotion services.
- 6 pre-existing frontend test failures in 4 files (app.spec.ts, cart.spec.ts, order-detail.spec.ts, order-list.spec.ts) — unrelated to this change.
- Route guard enforcement for wishlist and promotions pages has only partial test coverage (verified by Angular compiler, not explicit guard unit tests).

**SUGGESTION**:
- Add backend HTTP integration tests for the 22 UNTESTED spec scenarios to achieve full compliance.
- The backend implementation code follows the design faithfully and is structurally sound — the gap is purely in test coverage, not code quality.

### Verdict
**FAIL** — Implementation is complete (27/27 tasks, all files exist, code follows design, pre-existing tests pass), but backend spec compliance is unverifiable: 21 backend/API spec scenarios are UNTESTED with zero backend tests covering reviews, wishlist, or promotions functionality.

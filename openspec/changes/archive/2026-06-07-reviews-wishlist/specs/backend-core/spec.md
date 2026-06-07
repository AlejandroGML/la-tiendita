# Delta for backend-core

## MODIFIED Requirements

### Requirement: Controller, Guard, and Middleware Registration

`app/main.py` MUST register all application controllers, guards, and middleware during Litestar app creation. This SHALL include auth controllers, product controllers (`ProductController`, `UploadController`), cart controller (`CartController`), order controller (`OrderController`), review controller (`ReviewController`), wishlist controller (`WishlistController`), promotion controllers (`PromotionController`, `AdminPromotionController`), admin controllers (`AdminProductController`, `AdminCategoryController`, `AdminController`), JWT/admin guards, and rate-limiting/i18n middleware.
(Previously: Did not include ReviewController, WishlistController, PromotionController, AdminPromotionController)

#### Scenario: Review and wishlist endpoints appear in OpenAPI
- GIVEN ReviewController, WishlistController are registered in main.py
- WHEN the backend starts and /schema is accessed
- THEN POST /api/products/{id}/reviews, GET /api/products/{slug}/reviews, GET/POST/DELETE /api/wishlist appear in API docs

#### Scenario: Promotion endpoints appear in OpenAPI
- GIVEN PromotionController, AdminPromotionController are registered in main.py
- WHEN /schema is accessed
- THEN GET /api/promotions, admin CRUD /api/admin/promotions appear in API docs

### Requirement: Model Discovery for Autogenerate

`migrations/env.py` MUST import all SQLAlchemy model modules so `Base.metadata` includes every table when `alembic revision --autogenerate` runs. This SHALL include `app.models.product`, `app.models.category`, `app.models.cart`, `app.models.order`, `app.models.review`, `app.models.wishlist`, and `app.models.promotion` modules.
(Previously: Did not import review, wishlist, promotion model modules)

#### Scenario: Autogenerate detects review, wishlist, and promotion tables
- GIVEN Review, Wishlist, Promotion, PromotionTranslation models are defined
- AND env.py imports app.models.review, app.models.wishlist, app.models.promotion
- WHEN alembic revision --autogenerate runs
- THEN migration includes CREATE TABLE for reviews, wishlist, promotions, promotion_translations

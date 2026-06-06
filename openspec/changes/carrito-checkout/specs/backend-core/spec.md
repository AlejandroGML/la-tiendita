# Delta for backend-core

## MODIFIED Requirements

### Requirement: Controller, Guard, and Middleware Registration

`app/main.py` MUST register all application controllers, guards, and middleware during Litestar app creation. This SHALL include auth controllers, product controllers (`ProductController`, `UploadController`), cart controller (`CartController`), order controller (`OrderController`), JWT/admin guards, and rate-limiting/i18n middleware.
(Previously: registered only auth and product controllers; no cart/checkout controllers.)

#### Scenario: Auth endpoints appear in OpenAPI

- GIVEN an AuthController is registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN all `/auth/*` endpoints appear in the API documentation

#### Scenario: Product endpoints appear in OpenAPI

- GIVEN `ProductController` and `UploadController` are registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `/api/products`, `/api/admin/products`, `/api/categories`, `/api/upload` appear in the API documentation

#### Scenario: Cart and checkout endpoints appear in OpenAPI

- GIVEN `CartController` and `OrderController` are registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `/api/cart`, `/api/checkout`, `/api/orders`, `/api/orders/{id}` appear in the API documentation

### Requirement: Model Discovery for Autogenerate

`migrations/env.py` MUST import all SQLAlchemy model modules so `Base.metadata` includes every table when `alembic revision --autogenerate` runs. This SHALL include `app.models.product`, `app.models.category`, `app.models.cart`, and `app.models.order` modules.
(Previously: imported only product and category models; no cart/order model imports.)

#### Scenario: Autogenerate detects auth models

- GIVEN `User` and `RefreshToken` models are defined and `env.py` imports the model modules
- WHEN `alembic revision --autogenerate -m "add auth tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `users` and `refresh_tokens`

#### Scenario: Autogenerate detects product and category models

- GIVEN `Product`, `ProductTranslation`, `Category`, `CategoryTranslation` models are defined
- AND `env.py` imports `app.models.product` and `app.models.category`
- WHEN `alembic revision --autogenerate -m "add product tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `products`, `product_translations`, `categories`, and `category_translations`

#### Scenario: Autogenerate detects cart and order models

- GIVEN `CartItem`, `Order`, and `OrderItem` models are defined
- AND `env.py` imports `app.models.cart` and `app.models.order`
- WHEN `alembic revision --autogenerate -m "add cart and order tables"` is executed
- THEN the generated migration includes `CREATE TABLE` for `cart_items`, `orders`, and `order_items`

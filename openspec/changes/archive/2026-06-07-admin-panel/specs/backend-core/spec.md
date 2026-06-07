# Delta for backend-core

## MODIFIED Requirements

### Requirement: Controller, Guard, and Middleware Registration

`app/main.py` MUST register all application controllers, guards, and middleware during Litestar app creation. This SHALL include auth controllers, product controllers (`ProductController`, `UploadController`), cart controller (`CartController`), order controller (`OrderController`), admin controllers (`AdminProductController`, `AdminCategoryController`, `AdminController`), JWT/admin guards, and rate-limiting/i18n middleware.

(Previously: AdminController was not registered; cart/order/category controllers were present.)

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

#### Scenario: Admin dashboard endpoints appear in OpenAPI

- GIVEN `AdminController` is registered in `main.py`
- WHEN the backend starts and `/schema` is accessed
- THEN `/api/admin/dashboard`, `/api/admin/users`, `/api/admin/users/{id}/role`, `/api/admin/orders`, `/api/admin/orders/{id}/status` appear in the API documentation

# 🛍️ Plan: "La Tiendita" — Tienda Virtual de Ropa Segunda Mano

**Proyecto:** TiendaVirtual
**Nombre tienda:** La Tiendita (posible cambio)
**Idiomas:** Español 🇪🇸, Inglés 🇬🇧, Sueco 🇸🇪
**Stack API:** Litestar (Python 3.12+) + PostgreSQL 16
**Stack Frontend:** Angular 18+ + TypeScript + Angular Material + Tailwind

---

## Stack Completo

| Capa | Tecnología | Detalle |
|------|-----------|---------|
| **API** | Litestar + Pydantic v2 | ASGI, DI nativo, OpenAPI auto, guards, JWT |
| **DB** | PostgreSQL 16 + SQLAlchemy async | asyncpg driver, Alembic migrations |
| **Frontend** | Angular 18+ + TypeScript | SPA con routing, guards, interceptors |
| **UI** | Angular Material + Tailwind | Material components + utilidades CSS |
| **Auth** | JWT (access 15m + refresh 7d) + OAuth2 Google | Litestar JWTAuth + google-auth |
| **i18n** | ngx-translate (runtime) + JSON backend | 3 idiomas: ES, EN, SV |
| **Imágenes** | Local filesystem + Pillow | Upload con resize + thumbnail |
| **DevOps** | Docker Compose | PostgreSQL + API + Angular dev |
| **Validación** | Pydantic v2 | Schemas tipados, validación automática |

---

## Estructura del Proyecto

```
TiendaVirtual/
├── docker-compose.yml
├── .gitignore
├── README.md
├── PLAN.md                                 ← Este archivo
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                         # Litestar app entry
│   │   ├── config.py                       # pydantic-settings
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py                   # SQLAlchemy async engine + session
│   │   │   └── base.py                     # DeclarativeBase
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── category.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   ├── promotion.py
│   │   │   ├── review.py
│   │   │   └── wishlist.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── cart.py
│   │   │   ├── order.py
│   │   │   └── common.py                  # Pagination, filters, response wrapper
│   │   ├── controllers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                    # /auth/*
│   │   │   ├── products.py               # /api/products/*
│   │   │   ├── cart.py                    # /api/cart/*
│   │   │   ├── orders.py                  # /api/orders/*
│   │   │   ├── admin.py                   # /api/admin/*
│   │   │   └── upload.py                  # /api/upload/*
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── product_service.py
│   │   │   ├── cart_service.py
│   │   │   ├── order_service.py
│   │   │   └── image_service.py
│   │   ├── guards/
│   │   │   ├── __init__.py
│   │   │   ├── jwt_guard.py
│   │   │   ├── admin_guard.py
│   │   │   └── optional_auth.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── rate_limit.py
│   │   │   └── i18n.py                    # Detecta lang del request
│   │   ├── i18n/
│   │   │   ├── es.json
│   │   │   ├── en.json
│   │   │   └── sv.json
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pagination.py
│   │       ├── image.py                   # Pillow resize + thumbnail
│   │       └── email.py                   # Envío emails (password reset, confirmación)
│   ├── uploads/                           # Imágenes de productos (gitignored)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_products.py
│       ├── test_cart.py
│       └── test_orders.py
│
└── frontend/
    ├── angular.json
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── Dockerfile
    ├── src/
    │   ├── main.ts
    │   ├── index.html
    │   ├── styles.scss
    │   ├── app/
    │   │   ├── app.config.ts
    │   │   ├── app.routes.ts
    │   │   ├── app.component.ts
    │   │   │
    │   │   ├── core/
    │   │   │   ├── guards/
    │   │   │   │   ├── auth.guard.ts
    │   │   │   │   └── admin.guard.ts
    │   │   │   ├── interceptors/
    │   │   │   │   ├── auth.interceptor.ts
    │   │   │   │   ├── error.interceptor.ts
    │   │   │   │   └── language.interceptor.ts
    │   │   │   └── services/
    │   │   │       ├── auth.service.ts
    │   │   │       ├── product.service.ts
    │   │   │       ├── cart.service.ts
    │   │   │       ├── order.service.ts
    │   │   │       ├── admin.service.ts
    │   │   │       ├── wishlist.service.ts
    │   │   │       └── translation.service.ts
    │   │   │
    │   │   ├── shared/
    │   │   │   ├── components/
    │   │   │   │   ├── product-card/
    │   │   │   │   ├── cart-icon/
    │   │   │   │   ├── pagination/
    │   │   │   │   ├── star-rating/
    │   │   │   │   └── search-bar/
    │   │   │   ├── pipes/
    │   │   │   │   └── currency.pipe.ts
    │   │   │   └── models/
    │   │   │       ├── user.model.ts
    │   │   │       ├── product.model.ts
    │   │   │       ├── cart.model.ts
    │   │   │       └── order.model.ts
    │   │   │
    │   │   ├── layout/
    │   │   │   ├── header/
    │   │   │   │   ├── header.component.ts
    │   │   │   │   └── header.component.html
    │   │   │   └── footer/
    │   │   │       ├── footer.component.ts
    │   │   │       └── footer.component.html
    │   │   │
    │   │   └── features/
    │   │       ├── home/
    │   │       │   ├── home.component.ts
    │   │       │   └── home.component.html
    │   │       ├── products/
    │   │       │   ├── product-list.component.ts
    │   │       │   └── product-list.component.html
    │   │       ├── product-detail/
    │   │       │   ├── product-detail.component.ts
    │   │       │   └── product-detail.component.html
    │   │       ├── cart/
    │   │       │   ├── cart.component.ts
    │   │       │   └── cart.component.html
    │   │       ├── checkout/
    │   │       │   ├── checkout.component.ts
    │   │       │   └── checkout.component.html
    │   │       ├── auth/
    │   │       │   ├── login/
    │   │       │   │   ├── login.component.ts
    │   │       │   │   └── login.component.html
    │   │       │   └── register/
    │   │       │       ├── register.component.ts
    │   │       │       └── register.component.html
    │   │       ├── profile/
    │   │       │   ├── profile.component.ts
    │   │       │   ├── profile.component.html
    │   │       │   ├── order-list/
    │   │       │   │   ├── order-list.component.ts
    │   │       │   │   └── order-list.component.html
    │   │       │   ├── order-detail/
    │   │       │   │   ├── order-detail.component.ts
    │   │       │   │   └── order-detail.component.html
    │   │       │   └── wishlist/
    │   │       │       ├── wishlist.component.ts
    │   │       │       └── wishlist.component.html
    │   │       └── admin/
    │   │           ├── dashboard/
    │   │           │   ├── admin-dashboard.component.ts
    │   │           │   └── admin-dashboard.component.html
    │   │           ├── products/
    │   │           │   ├── admin-products.component.ts
    │   │           │   └── admin-products.component.html
    │   │           ├── product-form/
    │   │           │   ├── admin-product-form.component.ts
    │   │           │   └── admin-product-form.component.html
    │   │           ├── users/
    │   │           │   ├── admin-users.component.ts
    │   │           │   └── admin-users.component.html
    │   │           ├── orders/
    │   │           │   ├── admin-orders.component.ts
    │   │           │   └── admin-orders.component.html
    │   │           └── categories/
    │   │               ├── admin-categories.component.ts
    │   │               └── admin-categories.component.html
    │   │
    │   └── assets/i18n/
    │       ├── es.json
    │       ├── en.json
    │       └── sv.json
    │
    └── environments/
        ├── environment.ts
        └── environment.prod.ts
```

---

## Database Schema

### Tablas principales

```sql
-- usuarios
users (
  id UUID PK,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),            -- NULL si solo OAuth
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(50),
  avatar_url TEXT,
  role user_role NOT NULL DEFAULT 'customer',  -- 'customer' | 'admin'
  preferred_lang lang_code NOT NULL DEFAULT 'es',  -- 'es' | 'en' | 'sv'
  oauth_provider VARCHAR(50),            -- 'google' | NULL
  oauth_id VARCHAR(255),                 -- sub de Google | NULL
  is_verified BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)

-- refresh tokens
refresh_tokens (
  id UUID PK,
  user_id UUID FK NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)

-- categorías
categories (
  id SERIAL PK,
  slug VARCHAR(100) UNIQUE NOT NULL,
  image_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)

-- traducciones de categorías
category_translations (
  category_id INT FK NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  lang lang_code NOT NULL,
  name VARCHAR(255) NOT NULL,
  PRIMARY KEY (category_id, lang)
)

-- productos
products (
  id UUID PK,
  slug VARCHAR(255) UNIQUE NOT NULL,
  price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
  category_id INT FK REFERENCES categories(id),
  size VARCHAR(20),
  brand VARCHAR(255),
  condition product_condition NOT NULL DEFAULT 'good',  -- 'new'|'like_new'|'good'|'fair'
  image_urls JSONB NOT NULL DEFAULT '[]',
  stock INT NOT NULL DEFAULT 1 CHECK (stock >= 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)

-- traducciones de productos
product_translations (
  product_id UUID FK NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  lang lang_code NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  PRIMARY KEY (product_id, lang)
)

-- carrito
cart_items (
  id UUID PK,
  user_id UUID FK NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id UUID FK NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, product_id)
)

-- órdenes
orders (
  id UUID PK,
  user_id UUID FK NOT NULL REFERENCES users(id),
  status order_status NOT NULL DEFAULT 'pending',  -- 'pending'|'confirmed'|'shipped'|'delivered'|'cancelled'
  total DECIMAL(10,2) NOT NULL,
  shipping_address JSONB NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)

-- items de órdenes
order_items (
  id UUID PK,
  order_id UUID FK NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID FK NOT NULL REFERENCES products(id),
  product_snapshot JSONB NOT NULL,        -- copia del producto al momento de la compra
  quantity INT NOT NULL CHECK (quantity > 0),
  price DECIMAL(10,2) NOT NULL
)

-- promociones
promotions (
  id UUID PK,
  code VARCHAR(50) UNIQUE NOT NULL,
  discount_percent INT NOT NULL CHECK (discount_percent BETWEEN 1 AND 100),
  product_id UUID FK REFERENCES products(id),  -- NULL = global
  max_uses INT,
  current_uses INT NOT NULL DEFAULT 0,
  start_date TIMESTAMPTZ NOT NULL,
  end_date TIMESTAMPTZ NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)

-- traducciones de promociones
promotion_translations (
  promotion_id UUID FK NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
  lang lang_code NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  PRIMARY KEY (promotion_id, lang)
)

-- reviews
reviews (
  id UUID PK,
  user_id UUID FK NOT NULL REFERENCES users(id),
  product_id UUID FK NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, product_id)
)

-- wishlist / favoritos
wishlist (
  user_id UUID FK NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id UUID FK NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, product_id)
)
```

---

## API Endpoints

### Auth (`/auth/*`)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Registro con email + password |
| POST | `/auth/login` | No | Login → JWT access + refresh |
| POST | `/auth/refresh` | No | Refresh token → nuevo access |
| GET | `/auth/oauth/google` | No | Redirect a Google OAuth |
| GET | `/auth/oauth/google/callback` | No | Callback OAuth → JWT |
| POST | `/auth/logout` | JWT | Invalidar refresh token |
| POST | `/auth/forgot-password` | No | Enviar email con reset link |
| POST | `/auth/reset-password` | No | Reset password con token |

### Productos (`/api/products/*`)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/products` | Optional | Lista paginada con filtros `?category=&size=&min_price=&max_price=&condition=&q=&page=&lang=` |
| GET | `/api/products/{slug}` | No | Detalle producto + `redirect` a slug correcto |
| GET | `/api/products/{slug}/reviews` | No | Reviews del producto paginadas con avg rating |
| POST | `/api/products/{id}/reviews` | JWT | Crear review (solo si compró el producto) |

### Categorías / Promociones

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/categories` | No | Lista categorías con traducciones según `?lang=` |
| GET | `/api/promotions` | No | Promociones activas con traducciones según `?lang=` |

### Carrito

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/cart` | JWT | Ver carrito con subtotales |
| POST | `/api/cart` | JWT | Agregar producto `{product_id, quantity}` |
| PUT | `/api/cart/{item_id}` | JWT | Actualizar cantidad |
| DELETE | `/api/cart/{item_id}` | JWT | Eliminar ítem |
| DELETE | `/api/cart` | JWT | Vaciar carrito |

### Órdenes

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/api/checkout` | JWT | Crear orden desde carrito (reduce stock) |
| GET | `/api/orders` | JWT | Órdenes del usuario autenticado |
| GET | `/api/orders/{id}` | JWT | Detalle orden (solo propia o admin) |

### Perfil

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/profile` | JWT | Datos personales |
| PUT | `/api/profile` | JWT | Actualizar nombre, teléfono, idioma preferido |

### Wishlist

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/wishlist` | JWT | Lista favoritos |
| POST | `/api/wishlist/{product_id}` | JWT | Agregar a favoritos |
| DELETE | `/api/wishlist/{product_id}` | JWT | Quitar de favoritos |

### Upload

| Método | Ruta | Auth | Rol | Descripción |
|--------|------|------|-----|-------------|
| POST | `/api/upload` | JWT | admin | Subir imágenes, devuelve URLs |

### Admin

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/api/admin/stats` | Admin | Dashboard: total productos, usuarios, órdenes, revenue |
| GET | `/api/admin/products` | Admin | Todos los productos (con borradores) |
| POST | `/api/admin/products` | Admin | Crear producto con traducciones |
| PUT | `/api/admin/products/{id}` | Admin | Actualizar producto + traducciones |
| DELETE | `/api/admin/products/{id}` | Admin | Desactivar (soft delete) producto |
| GET | `/api/admin/categories` | Admin | Todas las categorías |
| POST | `/api/admin/categories` | Admin | Crear categoría con traducciones |
| PUT | `/api/admin/categories/{id}` | Admin | Editar categoría |
| DELETE | `/api/admin/categories/{id}` | Admin | Eliminar categoría |
| GET | `/api/admin/users` | Admin | Todos los usuarios |
| PUT | `/api/admin/users/{id}` | Admin | Editar usuario (rol, verificado) |
| DELETE | `/api/admin/users/{id}` | Admin | Desactivar usuario |
| GET | `/api/admin/orders` | Admin | Todas las órdenes con filtros |
| PUT | `/api/admin/orders/{id}/status` | Admin | Cambiar estado de orden |

---

## Angular Routes

| Ruta | Componente | Auth | Descripción |
|------|-----------|------|-------------|
| `/` | HomeComponent | No | Landing: hero, productos destacados, promos activas, categorías populares |
| `/productos` | ProductListComponent | No | Catálogo con filtros (sidebar), búsqueda, paginación, grid de cards |
| `/productos/:slug` | ProductDetailComponent | No | Galería imágenes, info, talla, condición, precio, stock, reviews, related |
| `/carrito` | CartComponent | JWT | Tabla items + cantidades + total + botón checkout |
| `/checkout` | CheckoutComponent | JWT | Form dirección envío, resumen orden, confirmar |
| `/login` | LoginComponent | No | Form email/password + botón "Google Sign In" |
| `/register` | RegisterComponent | No | Form registro email/password |
| `/recuperar` | ForgotPasswordComponent | No | Form email para reset link |
| `/reset-password` | ResetPasswordComponent | No | Nuevo password con token |
| `/perfil` | ProfileComponent | JWT | Datos personales, selector de idioma |
| `/perfil/ordenes` | OrderListComponent | JWT | Historial órdenes con estado |
| `/perfil/ordenes/:id` | OrderDetailComponent | JWT | Detalle orden, items, timeline estados |
| `/perfil/wishlist` | WishlistComponent | JWT | Grid productos favoritos |
| `/admin` | AdminDashboardComponent | Admin | Stats cards, charts (Chart.js) |
| `/admin/productos` | AdminProductsComponent | Admin | Tabla CRUD + botón nuevo |
| `/admin/productos/nuevo` | AdminProductFormComponent | Admin | Form producto + traducciones ES/EN/SV |
| `/admin/productos/:id` | AdminProductFormComponent | Admin | Editar producto |
| `/admin/usuarios` | AdminUsersComponent | Admin | Tabla usuarios, editar rol |
| `/admin/ordenes` | AdminOrdersComponent | Admin | Tabla órdenes, filtros, cambiar estado |
| `/admin/categorias` | AdminCategoriesComponent | Admin | CRUD categorías + traducciones |
| `/admin/promociones` | AdminPromotionsComponent | Admin | CRUD promociones |

---

## Auth Flow

```
┌─────────────────────────────────────────────────────┐
│                    REGISTER                          │
│  POST /auth/register                                │
│  { email, password, name, preferred_lang }          │
│  ↓                                                  │
│  hash password (bcrypt) → save user → JWT tokens    │
│  ↓                                                  │
│  { access_token, refresh_token, user }              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                     LOGIN                            │
│  POST /auth/login                                   │
│  { email, password }                                │
│  ↓                                                  │
│  verify password hash → save refresh token → JWT    │
│  ↓                                                  │
│  { access_token, refresh_token, user }              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                   OAUTH GOOGLE                       │
│  GET /auth/oauth/google                             │
│  ↓ redirect a Google consent                        │
│  GET /auth/oauth/google/callback?code=...           │
│  ↓                                                  │
│  exchange code → get profile → find/create user     │
│  ↓                                                  │
│  { access_token, refresh_token, user, is_new }      │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                    REFRESH                           │
│  POST /auth/refresh                                 │
│  { refresh_token }                                  │
│  ↓                                                  │
│  verify hash in DB → generate new access token      │
│  ↓                                                  │
│  { access_token }                                   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  GUARDS (backend)                    │
│                                                      │
│  jwt_guard →  valida JWT del header Authorization   │
│               inyecta request.user en DI             │
│                                                      │
│  admin_guard → verifica request.user.role == admin   │
│                                                      │
│  optional_auth → intenta JWT, no falla si no hay     │
│                  inyecta request.user o None          │
└─────────────────────────────────────────────────────┘
```

---

## i18n (Internacionalización)

### Backend (Litestar)
- **Middleware i18n**: Detecta idioma de `?lang=` query param o `Accept-Language` header
- **Archivos JSON**: `backend/app/i18n/{es,en,sv}.json` con mensajes de API
- **Database**: Tablas separadas `*_translations` por entidad traducible (productos, categorías, promociones)
- **Default**: `es` si no se especifica ni detecta

### Frontend (Angular)
- **Librería**: `@ngx-translate/core` + `@ngx-translate/http-loader`
- **Archivos**: `frontend/src/assets/i18n/{es,en,sv}.json`
- **Selector**: Dropdown en el header con banderas ES/EN/SV
- **Persistencia**: Idioma guardado en localStorage + `preferred_lang` en perfil de usuario
- **Cambio**: En caliente sin recargar página

---

## Features por Change

### Change 1 — `proyecto-setup`
**Archivos ~15**
- Docker Compose (PostgreSQL 16 + Litestar + Angular)
- `backend/pyproject.toml` (Litestar, SQLAlchemy async, asyncpg, Alembic, Pillow, Pydantic, python-jose, httpx-oauth)
- `backend/app/main.py` con configuración básica Litestar + CORS + OpenAPI
- `backend/app/config.py` con `pydantic-settings` (DB URL, JWT secret, Google OAuth keys, etc.)
- `backend/app/db/engine.py` + `base.py` — conexión async, `DeclarativeBase`
- `backend/alembic.ini` + migrations folder
- Git init `.gitignore` con `uploads/`, `.env`, `__pycache__`
- `frontend/` Angular CLI project con Angular Material + Tailwind + ngx-translate
- `frontend/src/app/layout/header/` + `footer/` con routing básico

### Change 2 — `auth-system`
**Archivos ~20**
- `backend/app/models/user.py` + `refresh_tokens.py`
- `backend/app/schemas/auth.py` + `user.py`
- `backend/app/services/auth_service.py` (register, login, verify, hash, tokens)
- `backend/app/controllers/auth.py` (endpoints auth)
- `backend/app/guards/` (jwt, admin, optional)
- `backend/app/middleware/rate_limit.py`
- Frontend: `auth/` (login, register), `core/guards/`, `core/interceptors/auth.interceptor.ts`, `core/services/auth.service.ts`
- Google OAuth: botón "Sign in with Google" en login

### Change 3 — `catalogo-productos`
**Archivos ~25**
- `backend/app/models/product.py`, `category.py`
- `backend/app/schemas/product.py`
- `backend/app/controllers/products.py` (CRUD público + filtros + paginación)
- `backend/app/controllers/upload.py` (subida de imágenes + thumbnail)
- `backend/app/services/product_service.py`
- `backend/app/utils/image.py` (Pillow resize)
- Frontend: `product-list`, `product-detail`, `shared/product-card`, `shared/search-bar`, `shared/pagination`
- Admin: `admin-products`, `admin-product-form`

### Change 4 — `carrito-checkout`
**Archivos ~15**
- `backend/app/models/cart.py`, `order.py`
- `backend/app/schemas/cart.py`, `order.py`
- `backend/app/services/cart_service.py`, `order_service.py`
- `backend/app/controllers/cart.py`, `orders.py`
- Frontend: `cart/`, `checkout/`, `profile/order-list`, `profile/order-detail`
- Lógica: checkout → reduce stock → vacía carrito → crea order_items con snapshot

### Change 5 — `admin-panel`
**Archivos ~15**
- `backend/app/controllers/admin.py` (dashboard, CRUD users, gestión órdenes)
- Endpoints de stats con queries agregadas (COUNT, SUM, GROUP BY)
- Frontend: `admin/dashboard` (ng2-charts), `admin/users`, `admin/orders`, `admin/categories`
- Layout admin con sidebar + guards

### Change 6 — `reviews-wishlist`
**Archivos ~10**
- `backend/app/models/review.py`, `wishlist.py`, `promotion.py`
- Endpoints reviews (solo usuarios que compraron), wishlist (CRUD), promociones (admin)
- Validación: solo 1 review por usuario-producto, solo si tiene orden completada
- Frontend: `shared/star-rating`, `profile/wishlist`, sección de related products

### Change 7 — `polish-deploy`
**Archivos ~10**
- `backend/app/utils/email.py` + templates Jinja2 (password reset, order confirmation)
- `backend/app/middleware/i18n.py` + locates JSON para mensajes de API
- Rate limiting middleware con redis (o dict simple para MVP)
- Frontend: modo oscuro (Angular Material theme), responsive final, SEO meta tags
- Dockerfile producción (multi-stage Litestar con uvicorn + Angular build)
- `docker-compose.yml` final con volumen persistente para PostgreSQL y uploads

---

## Cómo Arrancar

```bash
# 1. Ir al proyecto
cd ~/Proyectos/TiendaVirtual

# 2. Inicializar git
git init
git add -A && git commit -m "chore: init PLAN.md"

# 3. Abrir OpenCode en esta carpeta y ejecutar:
#    /sdd-init
#
# 4. Cuando el orchestrator pregunte:
#    - Artifact store → "Engram"
#    - Execution mode → "interactive" (para ver los ECC gates)
#    - Delivery strategy → "single-pr" (proyecto nuevo, no hay reviewers)
#
# 5. Luego ejecutar en orden:
#    /sdd-new proyecto-setup
#    /sdd-new auth-system
#    /sdd-new catalogo-productos
#    /sdd-new carrito-checkout
#    /sdd-new admin-panel
#    /sdd-new reviews-wishlist
#    /sdd-new polish-deploy
```

---

## Funcionalidades Adicionales (por si quieres agregar después)

- [ ] Pagos reales (Stripe o MercadoPago)
- [ ] Notificaciones push cuando cambia estado de orden
- [ ] Chat en vivo comprador-vendedor
- [ ] Códigos de descuento por referidos
- [ ] Subasta de productos (precio inicial + pujas)
- [ ] Verificación de identidad para vendedores
- [ ] Integración con Shopify u otras plataformas
- [ ] Aplicación móvil (Flutter/React Native)
- [ ] Analytics embebidos
- [ ] Exportación de datos (CSV/Excel)
- [ ] Sistema de tallas con guía de medición
- [ ] Notificaciones por email de wishlist (cuando baja de precio)
- [ ] Moderación de reviews
- [ ] Facturación automatizada
- [ ] Gestión de devoluciones

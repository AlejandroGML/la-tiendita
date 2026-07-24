# Design: api-versioning

## Architecture Decision

**Decision**: Use Litestar controller path prefix change + a catch-all 301 redirect handler rather than URL rewriting middleware.

**Rationale**:
- Litestar controllers declare their own `path` — changing that is the canonical way to set route prefixes
- A `@get("/api/{path:path}")` handler returning `Redirect(path, 301)` is simpler than middleware that rewrites `request.scope["path"]`
- 301 (Moved Permanently) is semantically correct: the old paths are permanently moved, and clients/browsers SHOULD update their bookmarks

**Alternatives considered**:
- **URL rewrite middleware**: Would silently serve content at both paths, creating duplicate URLs and SEO issues. Rejected — explicit redirect is cleaner.
- **308 (Permanent Redirect)**: Preserves HTTP method on redirect, but browsers handle 301 for GET/HEAD correctly and most API consumers follow redirects. 301 is sufficient and simpler.
- **API gateway prefix**: Not available in this setup (no reverse proxy in dev). Could be added later.

## Implementation Plan

### 1. Controller path changes (16 declarations, 12 files)

Each `path = "/api..."` → `path = "/api/v1..."`. The prefix is inserted after `/api`:

| File | Old | New |
|------|-----|-----|
| auth.py | `/api/auth` | `/api/v1/auth` |
| stripe.py | `/api/stripe` | `/api/v1/stripe` |
| admin.py L94 | `/api/admin` | `/api/v1/admin` |
| admin.py L259 | `/api/admin/products/{...}/variants` | `/api/v1/admin/products/{...}/variants` |
| profile.py | `/api/profile` | `/api/v1/profile` |
| orders.py | `/api` | `/api/v1` |
| upload.py | `/api` | `/api/v1` |
| products.py L64 | `/api/products` | `/api/v1/products` |
| products.py L176 | `/api/admin/products` | `/api/v1/admin/products` |
| categories.py L65 | `/api/categories` | `/api/v1/categories` |
| categories.py L108 | `/api/admin/categories` | `/api/v1/admin/categories` |
| reviews.py | `/api/products` | `/api/v1/products` |
| promotions.py L58 | `/api/promotions` | `/api/v1/promotions` |
| promotions.py L87 | `/api/admin/promotions` | `/api/v1/admin/promotions` |
| cart.py | `/api/cart` | `/api/v1/cart` |
| wishlist.py | `/api/wishlist` | `/api/v1/wishlist` |

### 2. Legacy redirect handler (main.py)

```python
from litestar.response import Redirect

@get("/api/{path:path}", sync_to_thread=False)
async def api_legacy_redirect(path: str) -> Redirect:
    return Redirect(f"/api/v1/{path}", status_code=301)
```

Registered in `route_handlers` list. The `{path:path}` converter captures everything after `/api/`.

**Order matters**: This handler must be registered AFTER the health check and protected endpoint but BEFORE the controllers. Litestar's router matches in registration order for same-prefix routes.

### 3. JWT exclude paths update

In `backend/app/guards/jwt_guard.py`, update the `exclude` list:
- `/api/products` → `/api/v1/products`
- `/api/categories` → `/api/v1/categories`
- `/api/promotions` → `/api/v1/promotions`
- `/api/cart` → `/api/v1/cart`
- `/api/checkout` → `/api/v1/checkout`
- `/api/stripe/webhook` → `/api/v1/stripe/webhook`

### 4. Frontend URL changes

All hardcoded `/api/` strings in services, interceptors, and spec files become `/api/v1/`. No architectural change — the frontend continues to use `HttpClient` with relative URLs.

### 5. Proxy configuration

`proxy.conf.json`: The `/api` proxy entry remains for the legacy redirect to work. A new `/api/v1` entry is added:

```json
"/api/v1": {
    "target": "http://backend:8000",
    "secure": false,
    "logLevel": "debug"
}
```

### 6. Environment files

Create `frontend/src/environments/environment.ts` and `environment.prod.ts` (Angular standard pattern) with `apiUrl: '/api/v1'` for future use. Note: current services use hardcoded paths; this file enables future centralization.

## Sequence Diagram

```
Client                Litestar App           Controller
  |                        |                      |
  | GET /api/v1/products   |                      |
  |----------------------->|                      |
  |                        | matches controller   |
  |                        | path="/api/v1/products"
  |                        |--------------------->|
  |                        |                      | handler executes
  |                        |<---------------------|
  | 200 + JSON             |                      |
  |<-----------------------|                      |
  |                        |                      |
  | GET /api/products (old)|                      |
  |----------------------->|                      |
  |                        | matches redirect     |
  | 301 Location:          |                      |
  |   /api/v1/products     |                      |
  |<-----------------------|                      |
  |                        |                      |
  | GET /api/v1/products   |                      |
  |----------------------->|                      |
  |                        |----------------------|
  | 200 + JSON             |                      |
  |<-----------------------|                      |
```

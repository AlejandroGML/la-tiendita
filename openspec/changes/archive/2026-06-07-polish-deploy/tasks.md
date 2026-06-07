# Tasks: Polish & Production Deployment

## Budget Forecast

| Metric | Value |
|--------|-------|
| Estimated total lines (additions + deletions) | ~680 |
| Budget per PR | 400 |
| Recommended slices | 3 |
| Slice strategy | Stacked-to-main (each PR targets `main`) |

**Decision needed before apply: No**
**Chained PRs recommended: Yes**
**400-line budget risk: High** (680 > 400 — MUST split)

---

## Slice 1: Production Docker Infrastructure (~145 lines, autonomous)

> **PR #1 → main** — Zero code changes. Pure infrastructure. Can be verified independently with `docker compose up`.

### Task 1.1: Backend Production Dockerfile
- **File**: `backend/Dockerfile` (new, ~20 lines) ✅
- Multi-stage: builder installs deps → runtime copies app, runs uvicorn
- Expose port 8000, CMD uvicorn

### Task 1.2: Frontend Production Dockerfile
- **File**: `frontend/Dockerfile` (new, ~20 lines) ✅
- Multi-stage: node builder runs `pnpm build --configuration production` → nginx:alpine serves dist
- Include `frontend/nginx.conf` for internal routing (API proxy + SPA fallback)

### Task 1.3: Frontend Nginx Config (container-internal)
- **File**: `frontend/nginx.conf` (new, ~25 lines) ✅
- `try_files $uri /index.html` for Angular deep links
- Proxy `/api/` → `backend:8000`, `/uploads/` → `backend:8000/uploads/`

### Task 1.4: Standalone Nginx Proxy Config (production)
- **File**: `nginx.prod.conf` (new, ~25 lines) ✅
- Routes: `/` → `frontend:80`, `/api/` → `backend:8000`, `/uploads/` → `backend:8000/uploads/`

### Task 1.5: Production docker-compose Override
- **Files**: `docker-compose.prod.yml` (new, ~40 lines), `README.md` (modify, ~15 lines) ✅
- Override backend/frontend to build from Dockerfiles instead of dev images
- Add `nginx` service (ports `80:80`, uses `nginx.prod.conf`)
- Add persistent `uploads` volume
- Add healthchecks for all services
- Update README with production deployment instructions

**Slice 1 verification**:
- `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- `curl http://localhost/health` → `{"status": "ok"}`
- `curl http://localhost/api/products` → `[]` or product data
- `curl http://localhost/` → Angular SPA HTML
- `docker compose ps` → all 4 services `healthy`

---

## Slice 2: Backend Polish — Email + i18n (~345 lines)

> **PR #2 → main** — Backend-only changes. No frontend changes. Depends on Slice 1 for production verification.

### Task 2.1: Email Config Fields ✅
- **File**: `backend/app/config.py` (modify, ~8 lines added)
- Add: `EMAIL_MODE`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`
- All have safe defaults (`log` mode, empty SMTP creds)

### Task 2.2: Email Utility ✅
- **File**: `backend/app/utils/email.py` (new, ~110 lines)
- `send_email(to, subject, html_body)` — log or SMTP based on `EMAIL_MODE`
- `render_template(name, **ctx)` — Jinja2 `FileSystemLoader` rooted at `app/templates/`, templates referenced as `"emails/name.html"`
- Use `logging` module for console output
- Lang-aware: loads i18n JSON from `app/i18n/{lang}.json`, injects as `messages`

### Task 2.3: Server-Side i18n JSONs ✅
- **Files**: `backend/app/i18n/es.json`, `en.json`, `sv.json` (new, ~35 lines each)
- Keys: `emails.password_reset.*`, `emails.order_confirmation.*`, `errors.*`, `footer.*`
- Each language file mirrors the same keys with translated values

### Task 2.4: Jinja2 Email Templates ✅
- **Files**: `backend/app/templates/emails/password_reset.html`, `order_confirmation.html` (created in Phase 1)
- `password_reset.html`: greeting, reset link button, expiry notice
- `order_confirmation.html`: order ID, item list, total, shipping address
- Templates reference `{{ messages.emails.password_reset.subject }}` etc. from context

### Task 2.5: Auth Service — Password Reset Email ✅
- **File**: `backend/app/services/auth_service.py` (modify, ~25 lines)
- **File**: `backend/app/controllers/auth.py` (modify, +1 parameter — session injection)
- In `forgot_password()`: looks up user, generates reset token, renders template, calls `send_email()`
- Pass `user.preferred_lang.value` and `user.name` to template context
- Returns silently if email not found (prevents user enumeration)

### Task 2.6: Order Service — Confirmation Email ✅
- **File**: `backend/app/services/order_service.py` (modify, ~65 lines)
- In `checkout()`: after savepoint commit, calls `_send_confirmation_email()` helper
- New `_send_confirmation_email()`: looks up user, builds item list from snapshots, formats shipping address, renders template, calls `send_email()`
- Pass `user.preferred_lang.value`, `user.name`, `order.id`, `order.total`, `order_items`, `shipping_address` to context

### Task 2.7: Jinja2 Dependency ✅
- **File**: `backend/pyproject.toml` (modify, +1 line)
- Add `"jinja2>=3.1"` to dependencies

**Slice 2 verification**:
- `POST /auth/forgot-password` → console shows rendered email with reset link
- `POST /api/checkout` → console shows rendered order confirmation email
- Template rendering test: verify `{{ user_name }}` and `{{ reset_link }}` interpolation
- i18n test: Swedish user gets Swedish email, Spanish user gets Spanish email

---

## Slice 3: Frontend Polish — Dark Mode + SEO + Responsive (~190 lines)

> **PR #3 → main** — Frontend-only changes. No backend changes.

### Task 3.1: Theme Service ✅
- **File**: `frontend/src/app/core/services/theme.service.ts` (new, ~50 lines)
- `signal<'light'|'dark'>`, toggle(), init from localStorage → prefers-color-scheme
- Apply/remove `dark-theme` class on `document.documentElement`

### Task 3.2: Dark Theme CSS ✅
- **File**: `frontend/src/styles.scss` (modify, ~25 lines)
- Import `pink-bluegrey.css` prebuilt theme scoped to `html.dark-theme` via nested `@import`
- Add CSS custom properties for non-Material elements

### Task 3.3: Theme Toggle in Header ✅
- **File**: `frontend/src/app/layout/header/header.html`, `header.ts` (modify, ~12 lines)
- Add `mat-icon-button` with `light_mode`/`dark_mode` icon
- Call `themeService.toggle()` on click

### Task 3.4: SEO Meta Tags — Static ✅
- **File**: `frontend/src/index.html` (modify, ~15 lines)
- Add: `description`, `og:title`, `og:description`, `og:type`, `og:locale`, `twitter:card`
- Add `<html lang="es">` attribute

### Task 3.5: SEO Meta Tags — Dynamic ✅
- **File**: `frontend/src/app/app.ts` (modify, ~25 lines)
- Inject `Title` and `Meta` from `@angular/platform-browser`
- On `NavigationEnd`, set title to "Route | La Tiendita"
- ProductDetail and ProductList update `og:title` + `description` after data load

### Task 3.6: Responsive Header — Hamburger Menu ✅
- **File**: `frontend/src/app/layout/header/header.html`, `header.ts` (modify, ~20 lines)
- Collapse nav links into `mat-menu` or toggle visibility at <640px
- Show hamburger icon, hide nav links at mobile

### Task 3.7: Responsive Product Grid ✅
- **File**: `frontend/src/app/features/products/product-list.html` (modify, ~5 lines)
- Ensure `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`

### Task 3.8: Responsive Cart Table ✅
- **File**: `frontend/src/app/features/cart/cart.html` (already had `overflow-x-auto`)
- Already present — no change needed

**Slice 3 verification**:
- Dark mode toggle switches theme, persists across reload
- View page source shows `<meta property="og:title">` and description tags
- Navigate to `/productos/chaqueta-denim` → browser tab title is "Chaqueta Denim | La Tiendita"
- Resize to 375px → header shows hamburger, product grid is 1 column
- Cart at 375px → table horizontally scrollable

---

## Review Forecast Summary

| Slice | Lines | Files | Review Complexity | Target Branch |
|-------|-------|-------|-------------------|---------------|
| PR #1 — Docker infra | ~145 | 6 new, 1 modified | Low (config only) | main |
| PR #2 — Backend polish | ~345 | 4 new, 4 modified | Medium (new utility + templates) | main |
| PR #3 — Frontend polish | ~190 | 3 new, 7 modified | Low (CSS + HTML tweaks) | main |
| **Total** | **~680** | **25** | — | — |

All slices are autonomous: each can be built, verified, and rolled back independently. No slice depends on another for correctness — Slice 2's email works with or without Slice 1's Dockerfiles. Slice 3's frontend works with or without Slice 2's backend changes.

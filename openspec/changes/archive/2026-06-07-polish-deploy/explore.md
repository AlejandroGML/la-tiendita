# Explore: polish-deploy

## Quick scan — what exists vs. what's missing

### Backend

| Target | Status | Detail |
|--------|--------|--------|
| `utils/email.py` | **MISSING** | No email utility. `config.py` has no SMTP fields. Plan calls for console-log MVP + Jinja2 templates. |
| `i18n/{es,en,sv}.json` | **MISSING** | `middleware/i18n.py` works (lang detection), but locale JSONs for server-side messages never created. |
| Rate limiting | **DONE** | `middleware/rate_limit.py` — per-IP in-memory counter. 5 req/60s on /auth/login + /auth/register. No changes needed. |
| Config | **PARTIAL** | `config.py` has all current fields. Needs SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, EMAIL_MODE (log/smtp). |

### Frontend

| Target | Status | Detail |
|--------|--------|--------|
| Dark mode toggle | **MISSING** | Uses prebuilt indigo-pink theme. No theme service, no CSS variables for dark/light switching. |
| SEO meta tags | **MINIMAL** | `index.html` has only title + viewport. No Open Graph, no description, no Angular Meta service. |
| Responsive polish | **PARTIAL** | Tailwind responsive classes exist but no systematic audit. Header nav, product grid, cart table need mobile verification. |

### Docker

| Target | Status | Detail |
|--------|--------|--------|
| backend/Dockerfile | **MISSING** | No multi-stage production Dockerfile. Dev uses `python:3.14-slim` directly in compose. |
| frontend/Dockerfile | **MISSING** | No production build. Dev uses `node:24-slim` with `ng serve`. Needs Angular build → nginx stage. |
| docker-compose.yml | **DEV ONLY** | Three services (db, backend, frontend) for dev. No production services, no nginx proxy, no persistent uploads volume. |

## Key findings

1. **Email is the biggest gap** — needs utils + templates + config fields. Console log MVP is acceptable per Plan.
2. **i18n JSONs are needed** — middleware works but return messages use hardcoded strings, not locale files.
3. **Rate limiting is complete** — no further work needed despite Plan Change 7 mentioning it.
4. **Dark mode** requires Angular Material theme switching (light/dark via `@include mat.all-component-themes`).
5. **Production Docker** needs two multi-stage Dockerfiles + docker-compose production profile.
6. **SEO** needs Angular Meta service + Open Graph tags in index.html + dynamic title updates per route.

## Recommendations

- Skip rate limiting work (already done in Change 2)
- Prioritize email utils (password reset depends on it per auth spec R7)
- Bundle dark mode + SEO under frontend-core delta (they're UI config)
- Production Docker is self-contained — no code changes, just infrastructure
- Total file estimate: ~15 files (slightly over Plan's ~10 but all infrastructure/config)

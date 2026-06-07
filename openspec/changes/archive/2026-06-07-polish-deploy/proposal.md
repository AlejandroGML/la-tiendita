# Proposal: Polish & Production Deployment

## Intent

Finalize TiendaVirtual for production MVP: add email notifications, server-side i18n messages, dark mode, SEO meta tags, responsive polish, and production Docker infrastructure. This is the last change before shipping.

## Scope

### In Scope
- Backend email utility (console-log mode for MVP) + Jinja2 password-reset/order-confirmation templates
- Server-side i18n locale JSONs (es/en/sv) for API error/notification messages
- Angular Material dark mode theme toggle (light/dark via CSS variables + theme service)
- SEO meta tags (Open Graph, description, dynamic titles via Angular Meta service)
- Responsive layout audit and fixes (header nav, product grid, cart table at mobile)
- Multi-stage production Dockerfile for backend (uvicorn) and frontend (Angular build → nginx)
- Production docker-compose.yml with nginx reverse proxy, persistent volumes, healthchecks

### Out of Scope
- Real SMTP integration (MVP uses console logging)
- Redis for rate limiting (in-memory is adequate for single-process MVP)
- E2E/Playwright visual regression tests
- CDN/image optimization pipeline

## Capabilities

### New Capabilities
- `email-notifications`: Email sending (console-log MVP) with Jinja2 templates for password reset and order confirmation
- `production-deployment`: Multi-stage Dockerfiles + nginx proxy + production docker-compose with persistent volumes

### Modified Capabilities
- `backend-core`: Add SMTP/email config fields to Settings
- `frontend-core`: Add dark mode theme toggle requirement, SEO meta tags, responsive breakpoint coverage
- `auth`: Password reset now sends email (via email-notifications) instead of just console log
- `dev-environment`: Extend docker-compose with production profile (override file)

## Approach

- **Email**: `app/utils/email.py` with `send_email()` that logs to console in `log` mode, sends via SMTP in `smtp` mode. Jinja2 `templates/emails/` for HTML body.
- **i18n JSONs**: Create `app/i18n/{es,en,sv}.json` with API message keys. Load in middleware, expose via `request.state.messages`.
- **Dark mode**: `ThemeService` in Angular core toggles `dark-theme` class on `<body>`. SCSS defines `@include mat.all-component-themes($dark-theme)` under `.dark-theme`.
- **SEO**: `Meta` and `Title` from `@angular/platform-browser`. Set in `AppComponent` + per-route resolvers.
- **Docker**: Backend stage 1 installs deps, stage 2 copies app + runs `uvicorn`. Frontend stage 1 `ng build`, stage 2 serves via nginx.
- **docker-compose**: New `docker-compose.prod.yml` overrides services: backend uses Dockerfile, frontend uses nginx, adds `nginx` proxy service, persistent `uploads` volume.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/utils/email.py` | New | Email sending utility |
| `backend/app/templates/emails/` | New | Jinja2 email templates |
| `backend/app/i18n/` | New | Server-side locale JSONs |
| `backend/app/config.py` | Modified | Add SMTP config fields |
| `backend/Dockerfile` | New | Multi-stage production image |
| `frontend/Dockerfile` | New | Angular build → nginx |
| `frontend/src/styles.scss` | Modified | Dark theme CSS |
| `frontend/src/app/core/services/theme.service.ts` | New | Theme toggle logic |
| `frontend/src/index.html` | Modified | SEO meta tags |
| `docker-compose.yml` | Modified | Production profile |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Dark theme breaks Material component contrast | Low | Use official Angular Material `define-dark-theme()` |
| nginx config wrong → 404 on deep links | Low | Test `try_files $uri $uri/ /index.html` |
| Production compose env vars clash with dev | Low | Use separate `.env.prod` + override compose file |

## Rollback Plan

- Revert to last commit. All changes are additive (new files + optional config). No database migrations. docker-compose.yml dev section untouched — production overrides in separate file.

## Dependencies

- None. This is the final change; all other 6 changes are complete.

## Success Criteria

- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml up` starts all 4 services (db, backend, frontend, nginx) and health checks pass
- [ ] `POST /auth/forgot-password` logs reset link to console with language-aware message
- [ ] `POST /api/checkout` logs order confirmation email to console
- [ ] Dark mode toggle switches theme without page reload
- [ ] `<meta property="og:title">` and `<meta name="description">` render in page source
- [ ] Product grid collapses to single column at 640px breakpoint

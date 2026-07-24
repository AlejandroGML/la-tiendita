# Proposal: api-versioning

## Intent
Prefix all API routes with `/api/v1/` to enable future API versioning without breaking existing consumers. Add a legacy redirect from `/api/*` → `/api/v1/*` (301 Moved Permanently) so existing clients and external integrations continue to work.

## Scope
- **Backend**: 16 `path = "/api..."` declarations across 12 controller files → prefix with `/v1`
- **Backend**: Add legacy 301 redirect handler in `main.py`
- **Backend**: Update `jwt_guard.py` exclude paths
- **Backend**: Update all test files referencing `/api/` paths
- **Frontend**: All hardcoded `/api/` strings in services, interceptors, and tests → `/api/v1/`
- **Frontend**: Create `environment.ts` and `environment.prod.ts` with `apiUrl: '/api/v1'`
- **Frontend**: Update `proxy.conf.json` to proxy `/api/v1` to backend

## Approach
Mechanical string replacement. No logic changes, no structural refactoring. Every `/api/` literal becomes `/api/v1/` in source code. A single redirect handler in `main.py` preserves backward compatibility.

## Rollback
Revert the commit. All changes are mechanical string substitutions with no database migrations or config changes.

## Capabilities Affected
- `backend-core`: Route prefixes, JWT exclude list, tests
- `frontend-core`: Service URLs, interceptor URL checks, proxy config

## Risk: Low
Mechanical prefix change. No behavioral change. Legacy redirect ensures zero-downtime migration for external consumers.

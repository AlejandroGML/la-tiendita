# Tasks: api-versioning

> **Review Workload Forecast**  
> Decision needed before apply: No  
> Chained PRs recommended: No  
> 400-line budget risk: High (estimated ~500 lines changed across 40+ files, but all mechanical string replacements)  

## Phase 1: Backend Route Prefix

- [x] 1.1 Change all controller `path = "/api..."` to `path = "/api/v1..."` (16 declarations, 12 files)
- [x] 1.2 Add legacy redirect handler in `main.py`: `GET /api/{path:path}` → 301 → `/api/v1/{path}`
- [x] 1.3 Update `jwt_guard.py` exclude paths from `/api/*` to `/api/v1/*`
- [x] 1.4 Update all backend test files: `/api/` → `/api/v1/`

## Phase 2: Frontend URL Update

- [x] 2.1 Update all hardcoded `/api/` strings in frontend services to `/api/v1/`
- [x] 2.2 Update all hardcoded `/api/` strings in frontend interceptors to `/api/v1/`
- [x] 2.3 Update all hardcoded `/api/` strings in frontend spec files to `/api/v1/`
- [x] 2.4 Update `proxy.conf.json`: add `/api/v1` proxy entry
- [x] 2.5 Create `frontend/src/environments/environment.ts` with `apiUrl: '/api/v1'`
- [x] 2.6 Create `frontend/src/environments/environment.prod.ts` with `apiUrl: '/api/v1'`

## Phase 3: Verification

- [x] 3.1 Verify backend app imports correctly: `python -c "from app.main import app; print('app OK')"` → ✅ `app OK`
- [ ] 3.2 Verify legacy redirect works: `curl /api/products` → 301, `curl /api/v1/products` → 200 (requires running server)

## Summary
11 tasks | Mechanical string replacement | Low risk | Estimated 500 changed lines

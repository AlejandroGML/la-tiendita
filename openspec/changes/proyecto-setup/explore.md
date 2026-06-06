# Explore: proyecto-setup

> Phase: Explore | Change: proyecto-setup | Project: TiendaVirtual

## Status

**Status:** Complete — ready for proposal
**Date:** 2026-06-06

## Executive Summary

The `proyecto-setup` change scaffolds the entire TiendaVirtual project from scratch. Tooling is largely available, but there are version discrepancies between PLAN.md assumptions and the tools actually installed on this machine. The most notable: Angular 22 (not 18), Tailwind v4 (not v3), and Python 3.14 (not 3.12). All needed Python packages are available on PyPI and npm.

## Key Findings

### 1. Version Discrepancies with PLAN.md

| Item | PLAN.md Says | Actual | Impact |
|------|-------------|--------|--------|
| Python | 3.12+ | 3.14.5 | Compatible — fine |
| Angular | 18+ | 22.0.0 | Scaffolds Angular 22 (new build system) |
| Angular Material | 18+ | 22.0.0 | Compatible |
| Tailwind CSS | v3 (config file) | v4.3.0 | **Significant** — v4 is CSS-first, no `tailwind.config.js` |
| Angular Build | — | `@angular/build` 22.0.0 | New "application" builder, not "browser" |
| ngx-translate | 18+ | 17.0.0 | Compatible (peers `@angular/core >=16`) |

### 2. Package Availability

**Backend (Python)** — all available on PyPI at latest versions:
- `litestar>=2.23.0`
- `sqlalchemy[asyncio]>=2.0.50` (already globally installed)
- `asyncpg>=0.31.0`
- `alembic>=1.18.4`
- `pydantic-settings>=2.14.1`
- `python-jose[cryptography]>=3.5.0`
- `httpx-oauth>=0.17.0`
- `pillow>=12.2.0` (already globally installed)
- `bcrypt>=5.0.0`
- `python-multipart>=0.0.32`

**Frontend (npm)** — all available:
- `@angular/core@22.0.0`
- `@angular/material@22.0.0`
- `@ngx-translate/core@17.0.0`
- `@ngx-translate/http-loader` (latest compatible)
- `tailwindcss@4.3.0` (or pin `@3` for PLAN.md compatibility)

### 3. Key Architecture Notes

- Angular 22 uses the **application builder** (`@angular/build`) by default — the old `@angular-devkit/build-angular:browser` is deprecated
- Angular 17+ uses **built-in control flow** (`@if`, `@for`) — no need for `*ngIf`/`*ngFor`
- Tailwind v4 uses `@import "tailwindcss"` in CSS files, **no `tailwind.config.js`** needed
- Using `pnpm` for npm operations (project rule)
- Python must use a **virtual environment** (venv) — no global pip installs

## Tooling Report

| Tool | Version | Status | Notes |
|------|---------|--------|-------|
| Python | 3.14.5 | ✅ Available | Use `python3 -m venv` |
| Node.js | 26.2.0 | ✅ Available | |
| pnpm | 11.1.1 | ✅ Available | Default package manager |
| Angular CLI | 22.0.0 | ✅ Available via npx | Not globally installed — use `npx @angular/cli` |
| Docker | 29.5.2 | ✅ Available | |
| Docker Compose | 5.1.4 | ✅ Available | |
| Git | 2.54.0 | ✅ Available | |
| psql | — | ❌ Not installed | Not needed (Docker PostgreSQL) |
| venv | — | ✅ Available | |
| pip | 26.1.1 | ✅ Available | |

## Risks

1. **Tailwind v4 migration**: PLAN.md explicitly lists `tailwind.config.js` and shows v3 patterns. Tailwind v4 is dramatically different. Decision needed: pin v3 or embrace v4.
2. **Angular 22 new build system**: The `@angular/build` application builder differs from the old browser builder. Angular Material setup, PostCSS config, and Tailwind integration may differ from common tutorials which assume the older build system.
3. **Python 3.14 compatibility**: Python 3.13+ removed the `imp` module. While Litestar and modern libraries should be fine, `python-jose` 3.5.0 and `httpx-oauth` 0.17.0 should be verified to work on 3.14.
4. **Angular CLI not global**: Must use `npx @angular/cli` for scaffolding — the `ng` command won't work without global install or npx.
5. **Empty testing infrastructure**: `strict_tdd: false` in config.yaml; no pytest or test runners configured yet. May affect proposal acceptance.

## Next Recommended

1. **Decide Tailwind version**: Pin `tailwindcss@3` (compatible with PLAN.md approach) or use Tailwind v4 natively
2. **Update PLAN.md**: Reflect actual Angular 22 version and new build system
3. **Proceed to proposal phase**: All tooling is adequate for a ~15-file scaffold
4. **Consider marking `strict_tdd`**: Keep `false` for setup phase since there's no code to test yet

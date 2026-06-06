# Testing Capabilities — TiendaVirtual

**Strict TDD Mode**: disabled
**Detected**: 2026-06-06
**Project Status**: PLAN phase — no source code or dependencies installed yet

## Test Runner

| Layer    | Backend             | Frontend              |
| -------- | ------------------- | --------------------- |
| Runner   | pytest              | Jasmine/Karma         |
| Status   | not_installed       | not_configured        |
| Install  | `pip install pytest` | `ng add @angular-devkit/build-angular` (auto via Angular CLI) |

## Test Layers

| Layer       | Backend Available | Backend Tool   | Frontend Available | Frontend Tool  |
| ----------- | ----------------- | -------------- | ------------------ | -------------- |
| Unit        | ❌                | pytest         | ❌                 | Jasmine        |
| Integration | ❌                | httpx (Litestar test client) | ❌       | Angular TestBed |
| E2E         | ❌                | —              | ❌                 | Playwright/Cypress (planned) |

## Coverage

| Layer    | Available | Command                       |
| -------- | --------- | ----------------------------- |
| Backend  | ❌        | `pytest --cov=app --cov-report=term-missing` |
| Frontend | ❌        | `ng test --no-watch --code-coverage`         |

## Quality Tools

| Tool         | Backend Available | Backend Command         | Frontend Available | Frontend Command       |
| ------------ | ----------------- | ----------------------- | ------------------ | ---------------------- |
| Linter       | ❌                | `ruff check .`          | ❌                 | `ng lint` (ESLint)     |
| Type checker | ❌                | `mypy .` (planned)      | ✅ (inherent)      | `tsc --noEmit`         |
| Formatter    | ❌                | `ruff format .`         | ❌                 | `prettier --write .`   |

## Notes

- No dependencies installed yet. This project is in PLAN phase.
- pytest + httpx AsyncClient is the recommended backend test stack for Litestar.
- Angular ships with Jasmine/Karma by default; Karma can be replaced with Jest for better DX.
- Once `pyproject.toml` and `package.json` are created, install dependencies and re-scan.
- TypeScript compilation (`tsc`) will be available as soon as Angular config exists.

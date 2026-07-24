# 🚀 Plan de Producción — La Tiendita

**Score actual**: 60/100
**Score objetivo**: 95/100
**Estado**: PENDIENTE (seguimos probando antes de implementar)

---

## Resultados de Auditoría

| Área | Diagnóstico | Peso |
|------|------------|------|
| **Código base** | ✅ Excelente. Tests 301/302 pass, build 0 errores, 0 raw queries, arquitectura limpia | **+40%** |
| **Docker/Deploy** | ✅ Docker compose prod listo, nginx configurado, build ~3MB frontend | **+15%** |
| **Seguridad** | ⚠️ .env.example faltante, password hardcodeado en compose prod | **-10%** |
| **Error Handling** | ❌ Sin global exception handler en Litestar | **-15%** |
| **Logging** | ❌ Sin logging configurado en app startup | **-10%** |
| **CI/CD** | ❌ Sin pipelines, sin despliegue automatizado | **-20%** |
| **Variables de Entorno** | ❌ Sin .env.example, 7 variables requeridas sin documentar | **-10%** |

---

## Phase 1: Seguridad Hardening (~2h)

### 1.1 Crear `.env.example`
**Archivo**: `backend/.env.example`
```bash
# REQUERIDAS (sin default)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db_name
SECRET_KEY=<generate-with: python3 -c "import secrets; print(secrets.token_hex(32))">

# PRODUCCIÓN (cambiar defaults)
CORS_ORIGINS=["https://latiendita.cl"]
FRONTEND_URL=https://latiendita.cl
DEBUG=false

# STRIPE (opcional hasta configurar pagos)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# EMAIL (SMTP)
EMAIL_MODE=smtp
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG....
EMAIL_FROM=hello@latiendita.cl

# OPCIONALES (defaults razonables)
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
RATE_LIMIT_REQUESTS=20
UPLOAD_DIR=./uploads
```

### 1.2 Remover passwords hardcodeados de docker-compose
**Archivo**: `docker-compose.yml`, `docker-compose.prod.yml`
- Reemplazar `postgres:postgres` por variables de entorno
- Agregar `env_file: .env` en el servicio backend de prod
- Usar Docker secrets para la password de DB

### 1.3 CORS para producción
⚠️ Ya soportado en config.py. Solo setear `CORS_ORIGINS` en `.env` para el dominio real.

---

## Phase 2: Operaciones & Observabilidad (~2h)

### 2.1 Global Exception Handler
**Archivo**: `backend/app/main.py`

Agregar al constructor de Litestar:
```python
exception_handlers={
    StripeError: lambda r, e: Response(content={"detail": "Payment service unavailable"}, status_code=502),
    StockInsufficientError: lambda r, e: Response(content={"detail": str(e)}, status_code=409),
    ValueError: lambda r, e: Response(content={"detail": str(e)}, status_code=400),
    Exception: global_exception_handler,
}
```

### 2.2 Logging Config en Startup
**Archivo**: `backend/app/main.py` (antes de crear app)
```python
import logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
```

### 2.3 Migración automática en startup
**Archivo**: `backend/app/main.py` (agregar a `on_startup`)
```python
async def on_startup() -> None:
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied")
```

---

## Phase 3: CI/CD Pipeline (~2h)

### 3.1 GitHub Actions Workflow
**Archivo**: `.github/workflows/ci.yml`
- 2 jobs: `backend` (PostgreSQL service, pytest), `frontend` (pnpm, build + test)
- Triggers: push + pull_request a main

### 3.2 `.gitignore` review
Cubrir: `.env`, `*.pyc`, `__pycache__`, `node_modules`, `dist/`, `uploads/`, `*.pem`

---

## Phase 4: Datos & Contenido (~2h)

### 4.1 Agregar `datasets` a dependencias
**Archivo**: `backend/pyproject.toml`
```toml
seed = ["datasets>=3.0"]
```

### 4.2 Seed de producción documentado
**README / DEPLOY.md**:
```bash
# Primer deploy (solo una vez):
docker compose -f docker-compose.prod.yml exec backend pip install datasets
docker compose -f docker-compose.prod.yml exec backend python -m scripts.seed_parquet --limit 500
```

### 4.3 Ajustar rate limit para producción
**Archivo**: `backend/app/config.py` — cambiar `RATE_LIMIT_REQUESTS` de 5 a 20.

### 4.4 DEPLOY.md
Crear con: prerequisitos, quick start, health checks, troubleshooting.

---

## Phase 5: Verificación Final (~1h)

Checklist para marcar VERDE antes de producción:

```bash
# □ 1. Backend tests pasan
cd backend && pytest -q          # ~302 passed

# □ 2. Frontend build sin errores
cd frontend && pnpm run build    # 0 errors

# □ 3. Frontend tests pasan
cd frontend && pnpm run test --watch=false

# □ 4. E2E tests pasan
cd frontend && pnpm run test:e2e

# □ 5. Docker compose prod arranca
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# □ 6. Health check responde
curl http://localhost:80/health  # {"status":"ok"}

# □ 7. Sin secrets en código
grep -r "SECRET\|PASSWORD\|API_KEY" --include="*.py" | grep -v test | grep -v .env.example
# → vacío

# □ 8. Sin raw queries en services
grep "select(" backend/app/services/ | grep -v "#"
# → vacío
```

---

## Resumen de Archivos

| Fase | Archivos | Cambio |
|------|----------|--------|
| **P1** | `.env.example` (nuevo), `docker-compose.yml`, `docker-compose.prod.yml` | +40 líneas |
| **P2** | `backend/app/main.py`, `backend/app/exceptions.py` | +40 líneas |
| **P3** | `.github/workflows/ci.yml` (nuevo) | +50 líneas |
| **P4** | `backend/pyproject.toml`, `backend/Dockerfile`, `DEPLOY.md` (nuevo), `backend/app/config.py` | +30 líneas |
| **P5** | `README.md` | +20 líneas |
| **Total** | **~10 archivos** | **~180 líneas** |

**Tiempo estimado**: 6-8 horas.
**Cuando implementar**: Después de terminar pruebas y mejoras en el sitio.

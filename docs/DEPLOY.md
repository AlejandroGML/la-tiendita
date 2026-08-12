# Deploy a Fly.io — single container

## Prerequisitos

1. Cuenta en [fly.io](https://fly.io) (free tier)
2. CLI: `curl -L https://fly.io/install.sh | sh` (o `brew install flyctl`)

## Pasos

### 1. Login

```bash
fly auth login
```

### 2. Lanzar la app (solo configura, sin deploy)

```bash
fly launch --copy-config --no-deploy --name la-tiendita
```

Esto crea el app con el `fly.toml` del repo. La región por defecto es `arn` (Estocolmo).

### 3. Crear la base de datos (Postgres)

```bash
fly postgres create --name la-tiendita-db
# Anota la connection string que te da
fly postgres attach la-tiendita-db --app la-tiendita
```

### 4. Crear Redis (Upstash)

```bash
fly addons create upstash_redis --name la-tiendita-redis --app la-tiendita
# Obtén la URL:
fly addons status la-tiendita-redis
```

### 5. Configurar secrets

```bash
fly secrets set \
  SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="rediss://..." \
  CORS_ORIGINS='["https://la-tiendita.fly.dev"]' \
  FRONTEND_URL="https://la-tiendita.fly.dev" \
  EMAIL_MODE="resend" \
  EMAIL_FROM="La Tiendita <onboarding@resend.dev>" \
  RESEND_API_KEY="re_..." \
  GOOGLE_CLIENT_ID="..." \
  GOOGLE_CLIENT_SECRET="..." \
  GOOGLE_OAUTH_REDIRECT_URI="https://la-tiendita.fly.dev/auth/google/callback" \
  STRIPE_SECRET_KEY="sk_test_..." \
  STRIPE_WEBHOOK_SECRET="whsec_..."
```

> **OAuth redirect URI**: en Google Cloud Console agrega
> `https://la-tiendita.fly.dev/auth/google/callback` (además del localhost).

### 6. Deploy

```bash
fly deploy
```

### 7. Seed de productos

```bash
fly ssh console
# dentro del contenedor:
python scripts/seed_real.py
```

### 8. Verificar

```bash
fly open
# Health check:
curl https://la-tiendita.fly.dev/api/v1/health/ready
```

## Notas

- El frontend compilado lo sirve el propio backend (StaticFiles) — un solo
  proceso, un solo contenedor, sin nginx.
- `auto_stop_machines = false` — la máquina NUNCA duerme (demo de portfolio).
- Swish corre en mock por defecto — el checkout completo funciona sin cuenta
  real. Para live: `SWISH_MODE=live` + certificados mTLS.
- Migraciones Alembic se aplican solas en el startup.
- Actualizar después de un cambio: `git push` + `fly deploy` (o conectar el
  repo a Fly para deploys automáticos).

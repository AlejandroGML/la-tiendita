# Design: Polish & Production Deployment

## Architecture Overview

```
Production Stack:
┌──────────────────────────────────────────────┐
│  nginx:80 (reverse proxy)                     │
│  / → frontend:80    /api/* → backend:8000     │
│  /uploads/* → backend:8000/uploads/           │
└──────┬───────────────────┬───────────────────┘
       │                   │
  ┌────▼─────┐      ┌──────▼──────┐
  │ frontend │      │  backend    │
  │ nginx:   │      │  uvicorn    │
  │ alpine   │      │  :8000      │
  │ /usr/    │      │             │
  │ share/   │      │ Jinja2      │
  │ nginx/   │      │ templates/  │
  │ html/    │      │ emails/     │
  └──────────┘      └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ PostgreSQL  │
                    │ :5432       │
                    │ pgdata vol  │
                    └─────────────┘
```

## Component Design

### 1. Email Utility (`backend/app/utils/email.py`)

```
email.py
├── def send_email(to, subject, html_body) → None
│   - EMAIL_MODE=log → logging.info(f"EMAIL to={to} ...")
│   - EMAIL_MODE=smtp → smtplib.SMTP → send_message
├── def render_template(name, **context) → str
│   - Jinja2 Environment(loader=FileSystemLoader("app/templates/emails"))
│   - Supports {{ user_name }}, {{ reset_link }}, {{ order_id }}, etc.
```

**Template structure** (`backend/app/templates/emails/`):
```
password_reset.html   — "Hej {{ user_name }}, klicka här: {{ reset_link }}"
order_confirmation.html — "Tack för din beställning #{{ order_id }}"
```

**Config fields added to `config.py`**:
```python
EMAIL_MODE: str = "log"           # "log" | "smtp"
SMTP_HOST: str = ""
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
EMAIL_FROM: str = "noreply@latiendita.local"
```

### 2. i18n Server-Side Messages (`backend/app/i18n/`)

Three JSON files with API message keys:

```json
// es.json (example keys)
{
  "emails": {
    "password_reset": {
      "subject": "Restablecer contraseña - La Tiendita",
      "greeting": "Hola {{name}}",
      "body": "Haz clic en el enlace para restablecer tu contraseña:",
      "button": "Restablecer"
    },
    "order_confirmation": {
      "subject": "Confirmación de pedido #{{order_id}}",
      "thanks": "Gracias por tu compra, {{name}}"
    }
  },
  "errors": {
    "rate_limit": "Demasiadas solicitudes. Intenta de nuevo en {{seconds}} segundos.",
    "unauthorized": "No autorizado",
    "forbidden": "Acceso denegado"
  }
}
```

**Loading strategy**: Jinja2 templates use the JSON files directly. At render time, pick the file matching user's `preferred_lang` and pass translations as template context.

### 3. Dark Mode (Frontend)

**Approach**: CSS class toggle — no runtime theme compilation needed.

```
ThemeService (core/services/theme.service.ts)
├── theme$: BehaviorSubject<'light' | 'dark'>
├── toggle() → switches, saves to localStorage
├── init() → reads localStorage, falls back to prefers-color-scheme
└── isDark(): boolean
```

**SCSS structure** (`styles.scss`):
```scss
// Light theme (default — current indigo-pink)
@import '@angular/material/prebuilt-themes/indigo-pink.css';

// Dark theme (applied when body.dark-theme)
body.dark-theme {
  // Use Angular Material's built-in pink-bluegrey dark theme
  @import '@angular/material/prebuilt-themes/pink-bluegrey.css';
  
  // Custom overrides
  --bg-primary: #1e1e2e;
  --text-primary: #cdd6f4;
}
```

**HeaderComponent changes**:
```html
<button mat-icon-button (click)="themeService.toggle()">
  <mat-icon>{{ themeService.isDark() ? 'light_mode' : 'dark_mode' }}</mat-icon>
</button>
```

### 4. SEO Meta Tags (Frontend)

**Static tags** in `index.html` (always present):
```html
<meta name="description" content="La Tiendita — Tienda virtual de ropa segunda mano">
<meta property="og:title" content="La Tiendita">
<meta property="og:description" content="Ropa segunda mano — calidad, buen precio">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_CL">
<meta name="twitter:card" content="summary">
```

**Dynamic updates** via Angular `Meta` + `Title` services in `AppComponent`:
```typescript
// app.ts
constructor(private title: Title, private meta: Meta) {
  this.router.events.subscribe(event => {
    if (event instanceof NavigationEnd) {
      this.title.setTitle(this.getTitle(route));  // "Productos | La Tiendita"
    }
  });
}
```

Per-route components (ProductDetail, ProductList) inject `Meta` and set `og:title`, `description` after data loads.

### 5. Responsive Polish

| Breakpoint | Header | Product Grid | Cart Table |
|------------|--------|-------------|------------|
| <640px | Hamburger menu | 1 column | Horizontal scroll |
| 640-1024px | Condensed nav | 2 columns | Normal table |
| >1024px | Full nav | 3-4 columns | Normal table |

Implementation: Tailwind responsive classes (`md:hidden`, `lg:grid-cols-3`, etc.) already partially in place. Audit and fix:
- Header: add `mat-sidenav` or `[hidden]` toggle for mobile
- Product grid: ensure `grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
- Cart: `overflow-x-auto` on table wrapper
- Checkout form: stack fields vertically on mobile

### 6. Production Dockerfiles

**Backend** (`backend/Dockerfile`):
```dockerfile
# Stage 1: Build
FROM python:3.14-slim AS builder
WORKDIR /app
COPY backend/ ./
RUN pip install --no-cache-dir -e .

# Stage 2: Runtime
FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY backend/app/ ./app/
COPY backend/templates/ ./templates/
RUN mkdir -p uploads
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend** (`frontend/Dockerfile`):
```dockerfile
# Stage 1: Build
FROM node:24-slim AS builder
WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build --configuration production

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist/frontend/browser /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf** (for frontend container AND standalone proxy):
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /uploads/ {
        proxy_pass http://backend:8000/uploads/;
    }
}
```

### 7. Production docker-compose

`docker-compose.prod.yml` overrides:
```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    volumes:
      - uploads:/app/uploads
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/tiendita_prod
      EMAIL_MODE: log
    # Remove dev volume mount (no hot-reload in prod)
    # Remove command override (Dockerfile CMD handles it)

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    # Remove dev volume mount
    # Remove command override

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  uploads:
```

## Data Flow: Password Reset

```
User → POST /auth/forgot-password {email}
  → AuthService.forgot_password(email)
    → generate reset_token (JWT, 1h expiry)
    → get user.preferred_lang
    → render_template("password_reset.html",
        user_name=user.name,
        reset_link=f"http://localhost:4200/reset-password?token={reset_token}",
        lang=user.preferred_lang)
    → send_email(to=email, subject=t["subject"], html_body=rendered)
      → EMAIL_MODE=log → console prints full email
      → EMAIL_MODE=smtp → sends via SMTP
  → 200 { message: "If email exists, reset link sent" }
```

## Key Decisions

1. **Theme strategy**: CSS class toggle (prebuilt themes) over runtime theme compilation. Simpler, no build step, 2 prebuilt Angular Material themes cover both modes.
2. **Email mode default**: `log` — zero config needed for MVP. SMTP is opt-in via env vars.
3. **nginx placement**: Separate `nginx` service in docker-compose, NOT embedded in frontend image. Keeps concerns separate and allows restarting frontend without dropping connections.
4. **i18n messages**: JSON files loaded by Jinja2 at render time (not cached in memory). Templates reference message keys via context dict. Trade-off: slightly slower first render, but zero memory footprint and instant updates.
5. **No rate limit changes**: Already implemented in Change 2. In-memory is adequate for single-process MVP deployment.

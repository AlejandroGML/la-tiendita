# ─────────────────────────────────────────────────────────────
# La Tiendita — single-container Dockerfile (Fly.io/Render/Railway)
#
# Stage 1: Build the Angular SPA
# Stage 2: Build Python deps
# Stage 3: Runtime — uvicorn serving API + compiled SPA via StaticFiles
# ─────────────────────────────────────────────────────────────

# ── Stage 1: Frontend build ──────────────────────────────────
FROM node:24-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm run build --configuration production

# ── Stage 2: Backend deps ────────────────────────────────────
FROM python:3.14-slim AS backend-build
WORKDIR /build
COPY backend/ ./
RUN pip install --no-cache-dir .

# ── Stage 3: Runtime ─────────────────────────────────────────
FROM python:3.14-slim
WORKDIR /app

# Copy Python env + backend code
COPY --from=backend-build /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=backend-build /usr/local/bin /usr/local/bin
COPY backend/ ./

# Copy compiled Angular SPA (served by the backend — single process)
COPY --from=frontend-build /build/dist/frontend/browser /app/frontend-dist

# Writable uploads dir for product images
RUN mkdir -p /app/uploads

ENV FRONTEND_DIST_DIR=/app/frontend-dist
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

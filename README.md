# La Tiendita

Tienda virtual de ropa segunda mano.

## Stack

| Capa | Tecnología |
|------|-----------|
| API | [Litestar](https://litestar.dev) (Python) |
| Base de datos | PostgreSQL 16 |
| Frontend | Angular 22+ |
| Estilos | [Tailwind CSS v3](https://tailwindcss.com) |
| Componentes UI | [Angular Material](https://material.angular.io) |

## Prerrequisitos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose
- [Node.js](https://nodejs.org) 24 o superior
- [Python](https://python.org) 3.14 o superior

## Arranque rápido

```bash
# Clonar el repositorio
git clone <repo-url> && cd TiendaVirtual

# Levantar todos los servicios
docker compose up
```

Servicios disponibles:
- **PostgreSQL**: `localhost:5432` (db: `tiendita_dev`, user: `postgres`, pass: `postgres`)
- **API Litestar**: `http://localhost:8000` (OpenAPI docs en `/schema`)
- **Frontend Angular**: `http://localhost:4200`

## Despliegue en producción

```bash
# Construir y levantar el stack completo (4 servicios)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

El stack productivo incluye:
- **nginx** (puerto 80) — reverse proxy, único servicio expuesto
- **frontend** (nginx:alpine) — SPA Angular compilado servido por nginx
- **backend** (python:3.14-slim) — API Litestar con uvicorn en puerto 8000
- **db** (postgres:16-alpine) — PostgreSQL con volumen persistente `pgdata`

Diferencias con el entorno de desarrollo:
- Los servicios se construyen desde sus Dockerfiles multi-etapa (imágenes más livianas)
- No hay hot-reload ni montaje de código fuente
- Las imágenes subidas (`uploads`) se guardan en un volumen persistente
- La base de datos usa `tiendita_prod` en vez de `tiendita_dev`
- Los emails se loguean a consola (`EMAIL_MODE=log`)

## Desarrollo local

Si querís correr los servicios por separado sin Docker:

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
pnpm install
pnpm dev
```

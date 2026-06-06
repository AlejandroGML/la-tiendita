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

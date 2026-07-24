# Design: Background Image Processing with ARQ

## Technical Approach

Move synchronous Pillow resize+thumbnail from the upload controller to an ARQ background worker backed by Redis. The controller saves the file, enqueues a job, and returns URLs immediately. ARQ handles retries, persistence, and at-least-once delivery. A new `worker` Docker Compose service runs the same backend image with `arq` CLI as entrypoint.

## Architecture Decisions

| Decision | Option A | Option B | Chosen | Rationale |
|----------|---------|---------|--------|-----------|
| Job queue | ARQ (Redis) | Celery (RabbitMQ) | ARQ | Redis already in stack; ARQ is async-native, zero-config, fits single-worker dev needs |
| Worker image | Same as backend | Separate Dockerfile | Same image | Reduces build surface; Pillow + helpers already installed; only CMD differs |
| Retry policy | ARQ default (exponential, max 3) | Custom retry function | Default | Sufficient for transient I/O; proposal forbids custom policies |
| Thumbnail contract | Return URL immediately, 404 OK for ≤2s | Wait synchronously | Immediate return | Matches <100ms goal; admin UI can retry on 404 |

## Data Flow

```
POST /api/upload
      │
      ▼
UploadController ──save file──► uploads/{uuid}.ext
      │
      ▼
arq.enqueue_job('process_image', file_path)
      │
      ▼
   Redis queue ──► ARQ Worker ──► _resize_image_sync()
                               ──► _generate_thumbnail_sync()
                               ──► uploads/{uuid}_thumb.webp
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/core/arq.py` | Create | ARQ settings: `RedisSettings` from `REDIS_URL`, job function registry |
| `backend/app/worker/jobs.py` | Create | `process_image` job calling existing `resize_image`/`generate_thumbnail` |
| `backend/app/controllers/upload.py` | Modify | Replace `await resize_image()` + `await generate_thumbnail()` with `await redis.enqueue_job('process_image', file_path)` |
| `docker-compose.yml` | Modify | Add `worker` service (same build context, `arq` CMD, uploads volume) |
| `backend/pyproject.toml` | Modify | Add `arq>=0.26` to dependencies |
| `backend/app/config.py` | Modify | Add `ARQ_QUEUE_NAME: str = "arq:queue"` field |

## Interfaces / Contracts

**ARQ job signature:**
```python
# backend/app/worker/jobs.py
async def process_image(ctx: WorkerContext, file_path: str) -> dict:
    await resize_image(file_path)
    thumb = await generate_thumbnail(file_path)
    return {"resized": file_path, "thumbnail": thumb}
```

**Upload controller change (key diff):**
```python
# Before (upload.py:77-78):
await resize_image(file_path)
thumb_path = await generate_thumbnail(file_path)

# After:
await redis.enqueue_job("process_image", file_path)
thumb_path = file_path.replace(ext, "_thumb.webp")  # predictable path
```

**Docker Compose worker service:**
```yaml
worker:
  build: { context: ., dockerfile: backend/Dockerfile }
  command: arq app.worker.jobs.WorkerSettings
  volumes: ["./backend/app:/app/app", "./uploads:/app/uploads"]
  environment: { REDIS_URL: "redis://redis:6379/0" }
  depends_on: { redis: { condition: service_healthy } }
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `process_image` job produces correct files | Mock `resize_image`/`generate_thumbnail`, verify call args |
| Integration | Upload enqueues job and returns URLs | `arq.worker.run_worker` in test, assert response <100ms |
| Integration | Worker processes job end-to-end | Full pipeline: upload → wait → verify files exist and have correct dimensions |
| E2E | Thumbnail becomes available within 2s | Docker Compose test: upload, poll thumbnail URL for ≤2s |

## Migration / Rollout

No data migration required. Rollback: revert `upload.py` to call `resize_image`/`generate_thumbnail` directly, remove `worker` service from compose. ARQ dependency harmless if unused.

## Open Questions

- [ ] Should the frontend implement a retry/polling mechanism for thumbnails, or is a simple 2s delay sufficient?
- [ ] Should we expose a worker health endpoint for monitoring (out of scope per proposal)?

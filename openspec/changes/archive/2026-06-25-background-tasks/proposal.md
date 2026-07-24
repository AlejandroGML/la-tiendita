# Proposal: Background Image Processing with ARQ

## Intent

Upload endpoint (`POST /api/upload`) blocks the HTTP response for 1–2 seconds running synchronous Pillow resize+thumbnail via `anyio.to_thread.run_sync`. No retry, no durability — a crash during processing loses the work. Move image processing to a background ARQ worker so the upload returns in < 100ms with resilience.

## Scope

### In Scope
- ARQ dependency (`arq>=0.26`) in `pyproject.toml`
- `process_image` ARQ job consuming Redis queue
- New `worker` service in `docker-compose.yml` (same image, `arq` CLI command)
- Refactor `UploadController.upload_image` to enqueue job instead of calling `resize_image`/`generate_thumbnail` directly
- API contract: return `image_url` immediately; `thumbnail_url` may 404 for ≤ 2s

### Out of Scope
- Thumbnail polling or WebSocket push
- Image processing for non-admin endpoints
- Custom retry policies beyond ARQ defaults
- Worker scaling (single worker for dev)

## Capabilities

### New Capabilities
- `image-processing`: ARQ-backed background worker for Pillow image resize+thumbnail. Encompasses job definition, queue configuration, worker lifecycle, and health check.

### Modified Capabilities
- `backend-core`: `UploadController` behavior changes — no longer calls `resize_image`/`generate_thumbnail` synchronously. R6 scenario for upload endpoint must reflect new response contract.

## Approach

Add `arq` to dependencies. Define `process_image` async job in `app/worker/jobs.py` that calls existing `resize_image`/`generate_thumbnail` helpers. Wire `ARQSettings` (Redis URL + queue name) into `app/config.py`. Add `worker` service to `docker-compose.yml` running `arq app.worker.main.WorkerSettings`. Refactor `UploadController.upload_image` to save file → enqueue job via `arq.connections.ArqRedis.enqueue_job` → return `image_url` with `thumbnail_url` as pending path.

Redis already available in compose and config — no new infrastructure.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/pyproject.toml` | Modified | Add `arq` dependency |
| `backend/app/config.py` | Modified | Add `REDIS_URL`, `ARQ_QUEUE_NAME` settings |
| `backend/app/worker/` | New | `jobs.py`, `main.py` (worker settings) |
| `backend/app/controllers/upload.py` | Modified | Enqueue instead of process |
| `docker-compose.yml` | Modified | Add `worker` service |
| `backend/Dockerfile` | Modified | Ensure `arq` CLI available in image |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Redis unavailable breaks upload entirely | Low | Health check on worker; upload can still save file, return 202 if queue down |
| Thumbnail not ready when admin UI loads | Med | Admin-only endpoint; natural 1–2s delay acceptable; retry on 404 in frontend |
| Worker restarts lose in-flight jobs | Low | ARQ persists jobs in Redis; at-least-once delivery |

## Rollback Plan

Revert `UploadController.upload_image` to call `resize_image`/`generate_thumbnail` directly. Remove `worker` service from compose. ARQ dependency harmless if unused — remove on next cleanup.

## Dependencies

- Redis (already in `docker-compose.yml` and `REDIS_URL` configured)
- `arq` (new PyPI dependency)

## Success Criteria

- [ ] `POST /api/upload` returns in < 100ms (excluding file I/O)
- [ ] Image resized and thumbnail generated within 2s of enqueue
- [ ] Worker handles concurrent uploads without data corruption
- [ ] Worker service starts via `docker compose up worker` and connects to Redis

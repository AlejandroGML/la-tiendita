# Tasks: Background Image Processing with ARQ

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~140 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | force-chained (PR 3 of 10, stacked-to-main) |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Add ARQ dependency, config, and settings | PR 3 | base=main; foundation for all worker code |
| 2 | Implement worker job and add Docker Compose service | PR 3 | depends on Unit 1; same PR |
| 3 | Wire upload controller + tests | PR 3 | depends on Unit 2; same PR |

All three units fit in one PR (~140 lines total). No chain split needed.

## Phase 1: Foundation

- [x] 1.1 Add `arq>=0.26` to `backend/pyproject.toml` dependencies
- [x] 1.2 Add `ARQ_QUEUE_NAME: str = "arq:queue"` to `Settings` in `backend/app/config.py`
- [x] 1.3 Create `backend/app/core/arq.py` — `RedisSettings` from `REDIS_URL`, `WorkerSettings` with function registry

## Phase 2: Worker Implementation

- [x] 2.1 Create `backend/app/worker/__init__.py` (empty package)
- [x] 2.2 Create `backend/app/worker/jobs.py` — `process_image` job calling `resize_image` + `generate_thumbnail`, return dict with paths
- [x] 2.3 Modify `backend/app/controllers/upload.py:77-78` — replace `await resize_image()` + `await generate_thumbnail()` with `await redis.enqueue_job("process_image", file_path)`; predict thumbnail path from original filename

## Phase 3: Infrastructure

- [x] 3.1 Add `worker` service to `docker-compose.yml` — same build image, `arq app.worker.jobs.WorkerSettings` command, uploads volume, depends on redis healthy

## Phase 4: Testing

- [x] 4.1 Unit test: `process_image` job calls `resize_image` and `generate_thumbnail` with correct file path
- [x] 4.2 Integration test: `POST /api/upload` enqueues ARQ job and returns response in <100ms (excluding I/O)
- [x] 4.3 Integration test: worker processes enqueued job end-to-end — upload, wait ≤2s, verify resized image + thumbnail files exist with correct dimensions

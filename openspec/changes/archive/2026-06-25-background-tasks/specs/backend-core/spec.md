# Delta for backend-core

## ADDED Requirements

### Requirement: ARQ Background Worker Configuration

The system MUST extend `Settings` with ARQ fields: `REDIS_URL` (already exists, reused as queue backend) and `ARQ_QUEUE_NAME` (str, default `"arq:queue"`). The ARQ worker settings class SHALL reference these values for Redis connection and job queue name.

#### Scenario: ARQ settings have sensible defaults

- GIVEN `.env` omits `ARQ_QUEUE_NAME`
- WHEN `Settings()` is instantiated
- THEN `ARQ_QUEUE_NAME` defaults to `"arq:queue"`

#### Scenario: Worker connects to Redis using settings

- GIVEN a running Redis instance at `REDIS_URL`
- WHEN the ARQ worker starts with `WorkerSettings`
- THEN the worker connects to Redis and polls `ARQ_QUEUE_NAME`

### Requirement: ARQ Worker Image Processing Job

The system MUST define a `process_image` ARQ job that calls existing `resize_image` and `generate_thumbnail` helpers. The job SHALL complete within 2s of dequeue for images under 5 MB. It SHALL NOT corrupt or lose the original file. ARQ retry with exponential backoff SHALL handle transient failures (max 3 retries).

#### Scenario: Worker processes image successfully

- GIVEN a `process_image` job is enqueued with a valid file path
- WHEN the ARQ worker dequeues and executes it
- THEN the image is resized (max dimension preserved) and a `_thumb.webp` is generated
- AND both files exist in the uploads directory

#### Scenario: Worker retries on transient failure

- GIVEN a `process_image` job encounters a temporary I/O error
- WHEN the first attempt fails
- THEN ARQ retries the job with exponential backoff (max 3 attempts)
- AND on final failure the job is logged and moved to dead-letter

#### Scenario: Worker handles concurrent jobs

- GIVEN three uploads are enqueued in rapid succession
- WHEN the worker processes them
- THEN each produces correctly resized and thumbnail files without data corruption

### Requirement: Worker Docker Service with Uploads Volume

The system MUST define a `worker` service in `docker-compose.yml` using the same backend image but running `arq app.worker.main.WorkerSettings` as its command. It SHALL mount the same `uploads` volume as the backend service and depend on `redis` health.

#### Scenario: Worker service starts and connects

- GIVEN `docker compose up worker -d` is executed
- WHEN the worker container starts
- THEN it connects to Redis at `redis://redis:6379/0` and begins polling the queue

#### Scenario: Worker processes enqueued jobs end-to-end

- GIVEN both `backend` and `worker` services are running
- WHEN an upload is submitted via `POST /api/upload`
- THEN the worker picks up the job, produces resized + thumbnail files, and they are visible via `/uploads/`

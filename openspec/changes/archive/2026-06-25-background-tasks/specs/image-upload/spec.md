# Delta for image-upload

## MODIFIED Requirements

### Requirement: Admin Image Upload with Processing

The system MUST provide `POST /api/upload` (admin-only). Accepted MIME types: `image/jpeg`, `image/png`, `image/webp`. Maximum file size: 5 MB. On success, the system SHALL save the uploaded file to disk and enqueue a background ARQ job for Pillow processing (resize + thumbnail). The controller MUST return in <100ms (excluding file I/O). Response MUST return `image_url` immediately; `thumbnail_url` SHALL be returned but the thumbnail file MAY NOT exist until the worker completes (≤2s).
(Previously: resize and thumbnail ran synchronously via thread pool before returning the response.)

#### Scenario: Successful upload returns immediately

- GIVEN an authenticated admin
- WHEN `POST /api/upload` with a valid 1200x800 JPEG under 5 MB
- THEN 201 with `image_url` pointing to saved original file
- AND `thumbnail_url` is returned as a predictable path
- AND response completes in <100ms (excluding file I/O)

#### Scenario: Thumbnail unavailable during processing window

- GIVEN an upload just completed and thumbnail URL is known
- WHEN `GET /uploads/{uuid}_thumb.webp` within 2s of upload
- THEN 404 is acceptable (frontend retries or shows placeholder)

#### Scenario: Thumbnail available after worker completes

- GIVEN the ARQ worker has processed the job
- WHEN `GET /uploads/{uuid}_thumb.webp` after worker completion
- THEN 200 with `Content-Type: image/webp`

#### Scenario: Invalid file type rejected

- GIVEN an authenticated admin
- WHEN `POST /api/upload` with `image/gif`
- THEN 422 with "unsupported file type: must be JPEG, PNG, or WebP"

#### Scenario: File too large rejected

- GIVEN an image file exceeding 5 MB
- WHEN `POST /api/upload`
- THEN 422 with "file exceeds maximum size of 5 MB"

#### Scenario: Non-admin blocked

- GIVEN authenticated user with `role="user"`
- WHEN `POST /api/upload`
- THEN 403 Forbidden

#### Scenario: Upload does not block for processing

- GIVEN a valid image upload in progress
- WHEN the upload controller returns the HTTP response
- THEN Pillow processing has NOT yet started (delegated to worker)
- AND other concurrent API requests are never blocked by image processing

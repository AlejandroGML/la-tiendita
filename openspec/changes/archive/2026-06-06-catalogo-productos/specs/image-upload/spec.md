# image-upload Specification

## Purpose

Admin-only image upload with server-side Pillow processing: resize to max 800px, generate 200px thumbnail, store on local filesystem under `uploads/`. Returns public URLs for both original-sized and thumbnail images.

## Requirements

### Requirement: Admin Image Upload with Processing

The system MUST provide `POST /api/upload` (admin-only). Accepted MIME types: `image/jpeg`, `image/png`, `image/webp`. Maximum file size: 5 MB. On success, the system SHALL resize the image (max 800px on the longest side, preserving aspect ratio) and generate a 200px thumbnail using Pillow. Both files SHALL be saved to `uploads/{uuid}.{ext}` and `uploads/{uuid}_thumb.{ext}`. Response MUST return `image_url` and `thumbnail_url`. Pillow operations SHALL run via thread (`sync_to_thread=True`) to avoid blocking the async event loop.

#### Scenario: Successful JPEG upload

- GIVEN an authenticated admin
- WHEN `POST /api/upload` with a valid 1200x800 JPEG under 5 MB
- THEN 201 with `image_url` (resized to 800x533) and `thumbnail_url` (200x133)
- AND both files exist in `uploads/` directory

#### Scenario: Image smaller than max width passes through

- GIVEN a 400x300 PNG
- WHEN uploaded
- THEN the image is NOT upscaled (stays 400x300)
- AND a 200px thumbnail is still generated

#### Scenario: Invalid file type rejected

- GIVEN an authenticated admin
- WHEN `POST /api/upload` with `image/gif`
- THEN 422 with "unsupported file type: must be JPEG, PNG, or WebP"

#### Scenario: File too large rejected

- GIVEN an image file exceeding 5 MB
- WHEN `POST /api/upload`
- THEN 413 or 422 with "file exceeds maximum size of 5 MB"

#### Scenario: Non-admin blocked

- GIVEN authenticated user with `role="user"`
- WHEN `POST /api/upload`
- THEN 403 Forbidden

#### Scenario: Pillow does not block event loop

- GIVEN a valid image upload in progress
- WHEN Pillow resize is executing
- THEN other concurrent API requests are NOT blocked (async event loop remains responsive)

### Requirement: Image URL Serving

The system MUST serve uploaded images at `/uploads/{filename}` as static files. Public access (no auth required). The `uploads/` directory MUST be volume-mounted in Docker for persistence across container restarts.

#### Scenario: Static image served without auth

- GIVEN an image exists at `uploads/abc123.jpg`
- WHEN `GET /uploads/abc123.jpg`
- THEN 200 with `Content-Type: image/jpeg`
- AND no auth header is required

#### Scenario: Missing image returns 404

- GIVEN no image at `uploads/nonexistent.jpg`
- WHEN `GET /uploads/nonexistent.jpg`
- THEN 404

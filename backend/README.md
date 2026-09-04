# Ace Pro video upload API

This FastAPI service is the control plane for resumable tennis-match video uploads. The client sends video bytes directly to S3-compatible object storage with presigned multipart URLs, so files up to 20 GiB do not pass through the Python API.

The current implementation includes:

- multipart upload creation, progress inspection, resume, completion, abort, and expiry;
- MOV/MP4 validation and a three-hour duration limit;
- PostgreSQL state and Alembic migrations;
- opaque S3 object keys and unlisted playback URLs;
- completed-video lookup and idempotent deletion;
- a development identity adapter and a production auth boundary;
- JSON request logs and Prometheus metrics; and
- local PostgreSQL and MinIO services plus a browser test client.

Video processing, transcoding, content inspection, thumbnails, and iOS implementation are intentionally outside this phase.

## Local setup

Python 3.11 or newer and Docker are required. From this directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
docker compose up -d
alembic upgrade head
uvicorn ace_pro_api.main:app --reload
```

Some Docker Desktop installations provide the standalone `docker-compose` command instead of `docker compose`; either form works with `compose.yaml`.

Open these local endpoints:

- API documentation: `http://127.0.0.1:8000/docs`
- health check: `http://127.0.0.1:8000/health`
- Prometheus metrics: `http://127.0.0.1:8000/metrics`
- browser upload client: `http://127.0.0.1:8000/test-client`
- MinIO console: `http://127.0.0.1:9001`

The MinIO console uses the development credentials in `.env.example`. The browser client asks only for a video, derives its filename, size, format, duration, and upload fingerprint, uploads it in parts, displays progress, and can resume using the session saved in browser storage. It is the iOS-independent acceptance harness.

The client reports the detected duration; users cannot type or override it. The API treats that value as declared metadata until future server-side media inspection verifies the stored object. Browser codec detection is not reliable, so this transfer-only client stores `unknown`; a future inspection stage can determine H.264 or HEVC authoritatively. The iOS client should follow the same user experience and obtain duration from the selected Photos asset.

Stop services without deleting local database or object data:

```bash
docker compose down
```

## API flow

All API endpoints are under `/api/v1`:

1. `POST /uploads` creates a database record and an object-storage multipart upload.
2. `POST /uploads/{upload_id}/parts` returns presigned URLs for requested part numbers.
3. The client uploads each part directly to the returned URL and retains its ETag.
4. `GET /uploads/{upload_id}` reconciles stored parts and enables resume after an interruption.
5. `POST /uploads/{upload_id}/complete` verifies the authoritative parts and declared byte count, completes the object, and returns `storage_path` plus `playback_url`.
6. `DELETE /uploads/{upload_id}` aborts an incomplete upload.
7. `GET /videos/{video_id}` retrieves a completed video record.
8. `DELETE /videos/{video_id}` deletes the object, invalidates its CDN path when configured, and marks the record deleted.

Creation accepts an `Idempotency-Key` header. Part authorization is batched up to 100 parts. The configured part size is 64 MiB, presigned URLs last 15 minutes, and upload sessions expire after 24 hours.

Development requests use `X-Dev-User` when supplied and otherwise use `local-test-user`. Production mode deliberately fails closed until the real application authentication adapter is connected.

## Verification

Run fast tests and linting:

```bash
ruff check .
pytest
```

With PostgreSQL and MinIO running, execute the real multipart storage flow:

```bash
ACE_PRO_RUN_INTEGRATION=1 pytest -m integration
```

That test creates a session, uploads through a presigned MinIO URL, checks resume state, completes and downloads the object, repeats completion to verify idempotency, then deletes it.

## Expired-upload cleanup

Run the application cleanup command periodically (for example from a future scheduled worker):

```bash
python -m ace_pro_api.cleanup
```

It aborts expired multipart uploads and updates their database state. The AWS bucket also has a one-day lifecycle rule for incomplete multipart uploads as a safety net.

## Production configuration

Configuration uses `ACE_PRO_` environment variables; `.env.example` contains the local values. A production runtime must provide at least:

- `ACE_PRO_ENVIRONMENT=production`
- `ACE_PRO_DATABASE_URL` for a managed PostgreSQL database
- `ACE_PRO_AWS_REGION=us-west-2`
- `ACE_PRO_S3_BUCKET` from Terraform output
- `ACE_PRO_PLAYBACK_BASE_URL` using the CloudFront domain
- `ACE_PRO_CLOUDFRONT_DISTRIBUTION_ID` for deletion invalidations

Do not configure an S3 endpoint or static AWS access keys in production. Attach the Terraform-generated API IAM policy to the runtime role instead. Before deployment, replace the development identity adapter with the application’s authentication implementation and set explicit allowed upload origins in Terraform.

The production-shaped AWS resources are documented in [`../infra/terraform/README.md`](../infra/terraform/README.md). No AWS resources have been applied.

## Design references

- [`../docs/video-storage-design.md`](../docs/video-storage-design.md) is the implementation handoff and decision record.
- [`../docs/video-storage-design.html`](../docs/video-storage-design.html) is the visual design explanation.
- [`../docs/adr/0001-hybrid-evidence-backed-video-analysis.md`](../docs/adr/0001-hybrid-evidence-backed-video-analysis.md) records the proposed downstream analysis architecture.
- [`../docs/video-analysis/README.md`](../docs/video-analysis/README.md) indexes the component-level video-analysis specifications.

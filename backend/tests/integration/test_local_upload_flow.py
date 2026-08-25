import os
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from ace_pro_api.main import create_app

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("ACE_PRO_RUN_INTEGRATION") != "1",
    reason="set ACE_PRO_RUN_INTEGRATION=1 with the Docker services running",
)
def test_full_local_multipart_upload_playback_and_delete() -> None:
    payload = b"ace-pro-integration-video-payload"
    idempotency_key = str(uuid4())
    with TestClient(create_app()) as client:
        created_response = client.post(
            "/api/v1/uploads",
            headers={"Idempotency-Key": idempotency_key},
            json={
                "original_filename": "integration.mp4",
                "content_type": "video/mp4",
                "container": "mp4",
                "codec": "unknown",
                "size_bytes": len(payload),
                "duration_seconds": 1,
                "source_fingerprint": idempotency_key,
            },
        )
        assert created_response.status_code == 201
        created = created_response.json()

        authorized_response = client.post(
            f"/api/v1/uploads/{created['upload_id']}/parts",
            json={"part_numbers": [1]},
        )
        assert authorized_response.status_code == 200
        upload_url = authorized_response.json()["parts"][0]["url"]

        put_response = httpx.put(upload_url, content=payload)
        assert put_response.status_code == 200
        etag = put_response.headers["etag"]

        inspected_response = client.get(f"/api/v1/uploads/{created['upload_id']}")
        assert inspected_response.status_code == 200
        assert inspected_response.json()["parts"] == [
            {
                "part_number": 1,
                "etag": etag,
                "size_bytes": len(payload),
                "checksum": None,
            }
        ]

        completed_response = client.post(
            f"/api/v1/uploads/{created['upload_id']}/complete",
            json={
                "parts": [
                    {"part_number": 1, "etag": etag, "size_bytes": len(payload)}
                ]
            },
        )
        assert completed_response.status_code == 200
        completed = completed_response.json()
        assert completed["storage_path"].startswith("s3://ace-pro-videos/")

        playback_response = httpx.get(completed["playback_url"])
        assert playback_response.status_code == 200
        assert playback_response.content == payload

        repeated_completion = client.post(
            f"/api/v1/uploads/{created['upload_id']}/complete",
            json={
                "parts": [
                    {"part_number": 1, "etag": etag, "size_bytes": len(payload)}
                ]
            },
        )
        assert repeated_completion.json() == completed

        deleted_response = client.delete(f"/api/v1/videos/{created['video_id']}")
        assert deleted_response.status_code == 204
        assert httpx.get(completed["playback_url"]).status_code == 404

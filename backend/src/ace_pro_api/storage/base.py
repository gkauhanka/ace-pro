from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredPart:
    part_number: int
    etag: str
    size_bytes: int
    checksum: str | None = None


class ObjectStorage(Protocol):
    async def create_multipart_upload(self, *, bucket: str, key: str, content_type: str) -> str: ...

    async def presign_upload_parts(
        self,
        *,
        bucket: str,
        key: str,
        multipart_upload_id: str,
        part_numbers: list[int],
        expires_seconds: int,
    ) -> dict[int, str]: ...

    async def list_uploaded_parts(
        self, *, bucket: str, key: str, multipart_upload_id: str
    ) -> list[StoredPart]: ...

    async def abort_multipart_upload(
        self, *, bucket: str, key: str, multipart_upload_id: str
    ) -> None: ...

    async def complete_multipart_upload(
        self,
        *,
        bucket: str,
        key: str,
        multipart_upload_id: str,
        parts: list[StoredPart],
    ) -> None: ...

    async def object_size(self, *, bucket: str, key: str) -> int | None: ...

    async def delete_object(self, *, bucket: str, key: str) -> None: ...

    async def download_file(self, *, bucket: str, key: str, destination: str) -> None: ...

    async def upload_file(
        self, *, bucket: str, key: str, source: str, content_type: str
    ) -> None: ...

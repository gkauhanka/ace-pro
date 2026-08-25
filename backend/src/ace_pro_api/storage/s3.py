from functools import partial
from typing import Any

import boto3
from anyio import to_thread
from botocore.config import Config
from botocore.exceptions import ClientError

from ace_pro_api.config import Settings
from ace_pro_api.storage.base import StoredPart


class S3ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        client_options: dict[str, Any] = {
            "service_name": "s3",
            "region_name": settings.aws_region,
            "config": Config(
                signature_version="s3v4",
                s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"},
            ),
        }
        if settings.s3_endpoint_url:
            client_options["endpoint_url"] = settings.s3_endpoint_url
        if settings.s3_access_key_id:
            client_options["aws_access_key_id"] = settings.s3_access_key_id
        if settings.s3_secret_access_key:
            client_options["aws_secret_access_key"] = settings.s3_secret_access_key
        self._client = boto3.client(**client_options)

    async def create_multipart_upload(self, *, bucket: str, key: str, content_type: str) -> str:
        request = {
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
        }
        if self._client.meta.endpoint_url.endswith("amazonaws.com"):
            request["ServerSideEncryption"] = "AES256"
        response = await to_thread.run_sync(
            partial(self._client.create_multipart_upload, **request)
        )
        return str(response["UploadId"])

    async def presign_upload_parts(
        self,
        *,
        bucket: str,
        key: str,
        multipart_upload_id: str,
        part_numbers: list[int],
        expires_seconds: int,
    ) -> dict[int, str]:
        return {
            part_number: self._client.generate_presigned_url(
                "upload_part",
                Params={
                    "Bucket": bucket,
                    "Key": key,
                    "UploadId": multipart_upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=expires_seconds,
                HttpMethod="PUT",
            )
            for part_number in part_numbers
        }

    async def list_uploaded_parts(
        self, *, bucket: str, key: str, multipart_upload_id: str
    ) -> list[StoredPart]:
        parts: list[StoredPart] = []
        marker = 0
        while True:
            response = await to_thread.run_sync(
                partial(
                    self._client.list_parts,
                    Bucket=bucket,
                    Key=key,
                    UploadId=multipart_upload_id,
                    PartNumberMarker=marker,
                )
            )
            parts.extend(
                StoredPart(
                    part_number=int(item["PartNumber"]),
                    etag=str(item["ETag"]),
                    size_bytes=int(item["Size"]),
                    checksum=item.get("ChecksumSHA256"),
                )
                for item in response.get("Parts", [])
            )
            if not response.get("IsTruncated"):
                break
            marker = int(response["NextPartNumberMarker"])
        return parts

    async def abort_multipart_upload(
        self, *, bucket: str, key: str, multipart_upload_id: str
    ) -> None:
        try:
            await to_thread.run_sync(
                partial(
                    self._client.abort_multipart_upload,
                    Bucket=bucket,
                    Key=key,
                    UploadId=multipart_upload_id,
                )
            )
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") != "NoSuchUpload":
                raise

    async def complete_multipart_upload(
        self,
        *,
        bucket: str,
        key: str,
        multipart_upload_id: str,
        parts: list[StoredPart],
    ) -> None:
        await to_thread.run_sync(
            partial(
                self._client.complete_multipart_upload,
                Bucket=bucket,
                Key=key,
                UploadId=multipart_upload_id,
                MultipartUpload={
                    "Parts": [
                        {"ETag": part.etag, "PartNumber": part.part_number}
                        for part in parts
                    ]
                },
            )
        )

    async def object_size(self, *, bucket: str, key: str) -> int | None:
        try:
            response = await to_thread.run_sync(
                partial(self._client.head_object, Bucket=bucket, Key=key)
            )
            return int(response["ContentLength"])
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in {
                "404",
                "NoSuchKey",
                "NotFound",
            }:
                return None
            raise

    async def delete_object(self, *, bucket: str, key: str) -> None:
        await to_thread.run_sync(partial(self._client.delete_object, Bucket=bucket, Key=key))

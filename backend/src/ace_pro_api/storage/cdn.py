from functools import partial
from typing import Protocol
from uuid import uuid4

import boto3
from anyio import to_thread


class CdnInvalidator(Protocol):
    async def invalidate(self, path: str) -> str | None: ...


class NoOpCdnInvalidator:
    async def invalidate(self, path: str) -> str | None:
        return None


class CloudFrontInvalidator:
    def __init__(self, *, distribution_id: str) -> None:
        self._distribution_id = distribution_id
        self._client = boto3.client("cloudfront")

    async def invalidate(self, path: str) -> str:
        response = await to_thread.run_sync(
            partial(
                self._client.create_invalidation,
                DistributionId=self._distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": 1, "Items": [path]},
                    "CallerReference": str(uuid4()),
                },
            )
        )
        return str(response["Invalidation"]["Id"])

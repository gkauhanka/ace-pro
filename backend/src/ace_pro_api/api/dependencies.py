from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from ace_pro_api.auth import CurrentUser, DevelopmentAuthProvider, development_identity_header
from ace_pro_api.config import get_settings
from ace_pro_api.media import FFmpegMediaProcessor, MediaProcessor
from ace_pro_api.persistence.database import create_database_engine, create_session_factory
from ace_pro_api.storage.cdn import CdnInvalidator, CloudFrontInvalidator, NoOpCdnInvalidator
from ace_pro_api.storage.s3 import S3ObjectStorage


@lru_cache
def get_database_engine() -> AsyncEngine:
    return create_database_engine(get_settings())


@lru_cache
def get_database_session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(get_database_engine())


async def get_database_session() -> AsyncIterator[AsyncSession]:
    async with get_database_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@lru_cache
def get_object_storage() -> S3ObjectStorage:
    return S3ObjectStorage(get_settings())


def get_media_processor(
    storage: S3ObjectStorage = Depends(get_object_storage),
) -> MediaProcessor:
    return FFmpegMediaProcessor(storage=storage, settings=get_settings())


@lru_cache
def get_cdn_invalidator() -> CdnInvalidator:
    distribution_id = get_settings().cloudfront_distribution_id
    if distribution_id:
        return CloudFrontInvalidator(distribution_id=distribution_id)
    return NoOpCdnInvalidator()


@lru_cache
def get_auth_provider() -> DevelopmentAuthProvider:
    return DevelopmentAuthProvider(get_settings())


async def get_current_user(
    presented_identity: str | None = Depends(development_identity_header),
) -> CurrentUser:
    return await get_auth_provider().current_user(presented_identity)

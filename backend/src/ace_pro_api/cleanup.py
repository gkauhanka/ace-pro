import asyncio
import logging

from ace_pro_api.config import get_settings
from ace_pro_api.logging import configure_logging
from ace_pro_api.persistence.database import create_database_engine, create_session_factory
from ace_pro_api.persistence.repositories import (
    SqlAlchemyUploadRepository,
    SqlAlchemyVideoRepository,
)
from ace_pro_api.services.uploads import UploadLifecycleService
from ace_pro_api.storage.s3 import S3ObjectStorage

logger = logging.getLogger(__name__)


async def cleanup_expired_uploads() -> int:
    settings = get_settings()
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    try:
        async with factory() as session:
            cleaned = await UploadLifecycleService(
                uploads=SqlAlchemyUploadRepository(session),
                videos=SqlAlchemyVideoRepository(session),
                storage=S3ObjectStorage(settings),
            ).cleanup_expired()
            await session.commit()
            return cleaned
    finally:
        await engine.dispose()


def main() -> None:
    configure_logging(get_settings().log_level)
    cleaned = asyncio.run(cleanup_expired_uploads())
    logger.info("expired_uploads_cleaned", extra={"count": cleaned})


if __name__ == "__main__":
    main()


import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ace_pro_api import __version__
from ace_pro_api.api.uploads import router as uploads_router
from ace_pro_api.api.videos import router as videos_router
from ace_pro_api.config import get_settings
from ace_pro_api.errors import install_error_handlers
from ace_pro_api.logging import configure_logging
from ace_pro_api.metrics import HTTP_REQUEST_DURATION, HTTP_REQUESTS

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("api_started", extra={"environment": settings.environment})
    yield
    logger.info("api_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ace Pro API",
        description="Control plane for resumable tennis-match video uploads.",
        version=__version__,
        lifespan=lifespan,
    )
    install_error_handlers(app)
    app.include_router(uploads_router)
    app.include_router(videos_router)

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        started_at = perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        duration = perf_counter() - started_at
        HTTP_REQUESTS.labels(request.method, route_path, str(response.status_code)).inc()
        HTTP_REQUEST_DURATION.labels(request.method, route_path).observe(duration)
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": round(duration, 6),
            },
        )
        return response

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/test-client", include_in_schema=False)
    async def test_client() -> FileResponse:
        return FileResponse(STATIC_DIR / "upload-test.html")

    return app


app = create_app()

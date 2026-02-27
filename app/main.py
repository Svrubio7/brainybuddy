import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    from app.core.logging import setup_logging

    setup_logging()

    if settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
        )

    yield
    # Shutdown
    from app.core.database import engine

    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(SecurityHeadersMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    if settings.DEBUG:
        return JSONResponse(status_code=500, content={"detail": str(exc)})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Register routers
from app.api.health import router as health_router  # noqa: E402
from app.api.auth import router as auth_router  # noqa: E402
from app.api.tasks import router as tasks_router  # noqa: E402
from app.api.courses import router as courses_router  # noqa: E402
from app.api.tags import router as tags_router  # noqa: E402
from app.api.availability import router as availability_router  # noqa: E402
from app.api.schedule import router as schedule_router  # noqa: E402
from app.api.chat import router as chat_router  # noqa: E402
from app.api.sync import router as sync_router  # noqa: E402
from app.api.time_logs import router as time_logs_router  # noqa: E402
from app.api.insights import router as insights_router  # noqa: E402
from app.api.materials import router as materials_router  # noqa: E402
from app.api.energy import router as energy_router  # noqa: E402
from app.api.what_if import router as what_if_router  # noqa: E402
from app.api.collab import router as collab_router  # noqa: E402
from app.api.integrations import router as integrations_router  # noqa: E402
from app.api.tutor import router as tutor_router  # noqa: E402

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(courses_router)
app.include_router(tags_router)
app.include_router(availability_router)
app.include_router(schedule_router)
app.include_router(chat_router)
app.include_router(sync_router)
app.include_router(time_logs_router)
app.include_router(insights_router)
app.include_router(materials_router)
app.include_router(energy_router)
app.include_router(what_if_router)
app.include_router(collab_router)
app.include_router(integrations_router)
app.include_router(tutor_router)

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    yield
    # Shutdown
    from app.core.database import engine

    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

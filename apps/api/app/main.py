from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router as system_router
from app.api.v1.auth import router as auth_router
from app.api.v1.trust import router as trust_router
from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


app.include_router(system_router, prefix=settings.api_v1_prefix)

app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(trust_router, prefix=settings.api_v1_prefix)

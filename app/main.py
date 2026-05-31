from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.routers import analytics, profiles, scraping
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.infrastructure.database.session import async_engine

settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await async_engine.dispose()


app = FastAPI(
    title="LinkForge API",
    description="Advanced LinkedIn analytics platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(analytics.router)
app.include_router(scraping.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "linkforge"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "LinkForge API", "docs": "/docs"}

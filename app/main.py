from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging
from app.core.config import get_settings
from app.infrastructure.database.session import async_engine
from app.api.v1.routers import profiles, analytics, scraping

settings = get_settings()
setup_logging(settings.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: None)
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
async def health():
    return {"status": "ok", "service": "linkforge"}

@app.get("/")
async def root():
    return {"message": "LinkForge API", "docs": "/docs"}

from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.repositories.post_repository_impl import SQLPostRepository
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository

TEST_DB_NAME = "linkforge_test"


def _async_url(database: str) -> str:
    base = get_settings().database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    prefix = base.rsplit("/", 1)[0]
    return f"{prefix}/{database}"


def _default_db_name() -> str:
    return get_settings().database_url.rsplit("/", 1)[-1]


async def _ensure_test_database() -> None:
    admin_engine = create_async_engine(_async_url(_default_db_name()), isolation_level="AUTOCOMMIT")
    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        await admin_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    await _ensure_test_database()
    engine = create_async_engine(_async_url(TEST_DB_NAME))
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with maker() as session:
            yield session
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def profile_repo(db_session: AsyncSession) -> SQLProfileRepository:
    return SQLProfileRepository(db_session)


@pytest_asyncio.fixture
async def post_repo(db_session: AsyncSession) -> SQLPostRepository:
    return SQLPostRepository(db_session)

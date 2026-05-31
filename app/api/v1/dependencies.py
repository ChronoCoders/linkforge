from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.post_repository_impl import SQLPostRepository
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository
from app.infrastructure.database.session import get_async_db


async def get_async_profile_repository(
    db: Annotated[AsyncSession, Depends(get_async_db)]
) -> SQLProfileRepository:
    return SQLProfileRepository(db)


async def get_post_repository(
    db: Annotated[AsyncSession, Depends(get_async_db)]
) -> SQLPostRepository:
    return SQLPostRepository(db)

from typing import Annotated, Optional, List, Dict, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_async_db
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository
from app.infrastructure.database.repositories.post_repository_impl import SQLPostRepository
from app.application.services.linkedin_service import LinkedInService
from app.infrastructure.scraping.linkedin_scraper import LinkedInScraper
from app.core.config import get_settings

async def get_async_profile_repository(
    db: Annotated[AsyncSession, Depends(get_async_db)]
) -> SQLProfileRepository:
    return SQLProfileRepository(db)

async def get_post_repository(
    db: Annotated[AsyncSession, Depends(get_async_db)]
) -> SQLPostRepository:
    return SQLPostRepository(db)

async def get_linkedin_service(
    profile_repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
    post_repo: Annotated[SQLPostRepository, Depends(get_post_repository)],
) -> LinkedInService:
    settings = get_settings()
    cookie_file = "cookies.json"
    return LinkedInService(profile_repo, post_repo, cookie_file=cookie_file)

async def get_authenticated_scraper(
    service: Annotated[LinkedInService, Depends(get_linkedin_service)]
) -> LinkedInScraper:
    scraper = service.scraper
    if not scraper.is_authenticated():
        await service.authenticate()
    return scraper

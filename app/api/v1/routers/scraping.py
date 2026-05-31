from typing import Annotated, Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl, ConfigDict
from app.infrastructure.scraping.linkedin_scraper import LinkedInScraper
from app.core.config import get_settings

router = APIRouter(prefix="/scraping", tags=["scraping"])

class ScrapeRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    url: HttpUrl
    max_posts: int = 12
    cookies: Optional[List[Dict[str, Any]]] = None

@router.post("/profile")
async def scrape_profile_direct(payload: ScrapeRequest):
    settings = get_settings()
    scraper = LinkedInScraper(headless=settings.playwright_headless)
    try:
        profile_data = await scraper.scrape_profile(
            str(payload.url), cookies=payload.cookies
        )
        posts = await scraper.scrape_posts_with_comments(
            str(payload.url), max_posts=payload.max_posts, cookies=payload.cookies
        )
        return {"profile": profile_data, "posts": posts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scraping failed: {str(e)}")
    finally:
        await scraper.close()

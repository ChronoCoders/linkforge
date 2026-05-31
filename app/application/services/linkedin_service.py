import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import get_settings
from app.core.exceptions import AuthError, RateLimitError, ScrapingError, ScrapingException
from app.domain.entities.post import Post
from app.domain.entities.profile import Profile
from app.domain.repositories.post_repository import PostRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.infrastructure.analysis.sentiment_analyzer import SentimentAnalyzer
from app.infrastructure.analysis.text_analyzer import TextAnalyzer
from app.infrastructure.embeddings.embedding_service import EmbeddingService
from app.infrastructure.scraping.linkedin_scraper import LinkedInScraper


class LinkedInService:
    def __init__(
        self,
        profile_repository: ProfileRepository,
        post_repository: Optional[PostRepository] = None,
        cookie_file: str = "cookies.json",
    ) -> None:
        self.profile_repository = profile_repository
        self.post_repository = post_repository
        settings = get_settings()
        self.scraper = LinkedInScraper(
            headless=settings.playwright_headless, cookie_file=cookie_file
        )
        self._load_session_cookies(settings.linkedin_session_cookies)
        self.embedding_service = EmbeddingService()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.text_analyzer = TextAnalyzer()
        self.max_retries = 3

    def _load_session_cookies(self, raw: str) -> None:
        if not raw.strip():
            return
        try:
            cookies = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("LINKEDIN_SESSION_COOKIES is not valid JSON; ignoring")
            return
        if isinstance(cookies, list):
            self.scraper.set_cookies(cookies)
        else:
            logger.warning("LINKEDIN_SESSION_COOKIES must be a JSON array; ignoring")

    def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        self.scraper.set_cookies(cookies)

    async def authenticate(self, cookies: Optional[List[Dict[str, Any]]] = None) -> bool:
        if cookies:
            self.set_cookies(cookies)
        try:
            logged_in = await self.scraper.refresh_cookies()
            if not logged_in:
                logged_in = await self.scraper.login()
            self.scraper._is_authenticated = logged_in
            return logged_in
        except Exception as e:
            raise AuthError(f"Authentication failed: {str(e)}")

    async def _execute_with_retry(
        self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any
    ) -> Any:
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                else:
                    raise
            except AuthError:
                if attempt < self.max_retries - 1:
                    await self.authenticate()
                else:
                    raise
            except Exception as e:
                last_exc = ScrapingError(str(e))
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
        raise last_exc or ScrapingException("Operation failed after retries")

    async def get_or_scrape_profile(
        self,
        linkedin_url: str,
        force_refresh: bool = False,
        cookies: Optional[List[Dict[str, Any]]] = None,
    ) -> Profile:
        if cookies:
            self.set_cookies(cookies)
        existing = await self.profile_repository.get_by_url(linkedin_url)
        if existing and not force_refresh:
            return existing
        try:
            raw_data = await self._execute_with_retry(
                self.scraper.scrape_profile, linkedin_url, self.scraper.get_cookies()
            )
        except Exception as e:
            if "auth" in str(e).lower() or "login" in str(e).lower():
                raise AuthError(str(e))
            raise ScrapingException(f"Failed to scrape profile: {str(e)}")
        profile = Profile(
            linkedin_url=linkedin_url,
            full_name=raw_data.get("full_name", "Unknown"),
            headline=raw_data.get("headline"),
            location=raw_data.get("location"),
            about=raw_data.get("about"),
            follower_count=raw_data.get("follower_count"),
            experience=raw_data.get("experience", []),
            education=raw_data.get("education", []),
            skills=raw_data.get("skills", []),
            raw_data=raw_data,
        )
        if profile.about:
            profile.embedding = self.embedding_service.generate(profile.about)
        saved = await self.profile_repository.save(profile)
        return saved

    async def scrape_and_store_posts(
        self,
        profile_id: int,
        profile_url: str,
        max_posts: int = 20,
        cookies: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Post]:
        if cookies:
            self.set_cookies(cookies)
        try:
            raw_posts = await self._execute_with_retry(
                self.scraper.scrape_posts_with_comments,
                profile_url,
                max_posts,
                self.scraper.get_cookies(),
            )
        except Exception as e:
            if "rate" in str(e).lower():
                raise RateLimitError(str(e))
            if "auth" in str(e).lower():
                raise AuthError(str(e))
            raise ScrapingException(f"Failed to scrape posts: {str(e)}")
        posts: List[Post] = []
        for rp in raw_posts:
            content = rp.get("content", "").strip()
            if not content:
                continue
            comments = rp.get("comments", [])
            sent = self.sentiment_analyzer.analyze(content, comments)
            compound = sent.get("compound", 0.0)
            theme_analysis = self.text_analyzer.analyze(content, comments)
            emb = self.embedding_service.generate(content) if len(content) > 30 else None
            rp["sentiment"] = sent
            rp["theme_analysis"] = theme_analysis
            post = Post(
                profile_id=profile_id,
                linkedin_post_id=rp.get("linkedin_post_id", f"unknown-{len(posts)}"),
                content=content[:8000],
                post_type=rp.get("post_type"),
                like_count=rp.get("like_count", 0),
                comment_count=rp.get("comment_count", 0),
                repost_count=rp.get("repost_count", 0),
                posted_at=rp.get("posted_at"),
                media_urls=rp.get("media_urls", []),
                comments=comments,
                raw_data=rp,
                sentiment_score=compound,
                embedding=emb,
            )
            posts.append(post)
        if posts and self.post_repository:
            await self.post_repository.save_many(posts)
        return posts

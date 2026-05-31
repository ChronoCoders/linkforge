from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_async
from app.infrastructure.scraping.base import BaseScraper
from app.core.exceptions import ScrapingException
from app.core.config import get_settings

class LinkedInScraper(BaseScraper):
    def __init__(self, headless: bool = True, cookie_file: str = "cookies.json"):
        super().__init__(cookie_file=cookie_file, headless=headless)
        self.settings = get_settings()
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._playwright = None

    async def _ensure_browser(self, cookies: Optional[List[Dict]] = None) -> tuple[BrowserContext, Page]:
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
        if self._context is None:
            self._context = await self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                locale="en-US",
            )
            await stealth_async(self._context)
            if cookies:
                await self._context.add_cookies(cookies)
        page = await self._context.new_page()
        return self._context, page

    async def close(self):
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def scrape_profile(self, url: str, cookies: Optional[List[Dict]] = None) -> Dict[str, Any]:
        context, page = await self._ensure_browser(cookies)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2200)
            data: Dict[str, Any] = {
                "full_name": "",
                "headline": "",
                "location": "",
                "about": "",
                "follower_count": None,
                "experience": [],
                "education": [],
                "skills": [],
            }
            try:
                h1 = page.locator("h1").first
                data["full_name"] = (await h1.inner_text(timeout=6000)).strip()
            except PlaywrightTimeout:
                pass
            try:
                headline = page.locator(".text-body-medium.break-words").first
                data["headline"] = (await headline.inner_text(timeout=4000)).strip()
            except PlaywrightTimeout:
                pass
            try:
                about_section = page.locator("#about").locator("xpath=..").locator("span[aria-hidden='true']").first
                data["about"] = (await about_section.inner_text(timeout=5000)).strip()
            except PlaywrightTimeout:
                pass
            return data
        except Exception as e:
            raise ScrapingException(f"Profile scrape failed: {str(e)}")
        finally:
            await page.close()

    async def scrape_posts_with_comments(self, profile_url: str, max_posts: int = 15, cookies: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        context, page = await self._ensure_browser(cookies)
        posts: List[Dict[str, Any]] = []
        try:
            activity_url = profile_url.rstrip("/") + "/recent-activity/all/"
            await page.goto(activity_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2400)
            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 1400)")
                await page.wait_for_timeout(1100)
            post_locators = page.locator("div[data-urn*='urn:li:activity']").all()
            post_elements = await post_locators
            for i, el in enumerate(post_elements[:max_posts]):
                try:
                    post_urn = await el.get_attribute("data-urn") or f"post-{i}"
                    linkedin_id = post_urn.split(":")[-1] if ":" in post_urn else post_urn
                    content = ""
                    try:
                        content_el = el.locator(".feed-shared-update-v2__description, .update-components-text").first
                        content = (await content_el.inner_text(timeout=3000)).strip()
                    except PlaywrightTimeout:
                        content = (await el.inner_text(timeout=2000)).strip()[:6000]
                    reactions = await self._extract_reactions(el)
                    comments = await self._extract_visible_comments(el, max_comments=4)
                    posts.append({
                        "linkedin_post_id": linkedin_id,
                        "content": content,
                        "post_type": "article" if "article" in content.lower() else "text",
                        "like_count": reactions.get("likes", 0),
                        "comment_count": reactions.get("comments", 0),
                        "repost_count": reactions.get("reposts", 0),
                        "media_urls": [],
                        "comments": comments,
                        "raw_data": {"urn": post_urn},
                    })
                except Exception:
                    continue
            return posts
        except Exception as e:
            raise ScrapingException(f"Posts scrape failed: {str(e)}")
        finally:
            await page.close()

    async def _extract_reactions(self, container) -> Dict[str, int]:
        result = {"likes": 0, "comments": 0, "reposts": 0}
        try:
            social = container.locator(".social-details-social-counts")
            text = await social.inner_text(timeout=2500)
            lowered = text.lower()
            if "like" in lowered:
                parts = text.split()
                for i, p in enumerate(parts):
                    if "like" in p.lower() and i > 0:
                        result["likes"] = int(parts[i-1].replace(",", "").replace(".", ""))
            if "comment" in lowered:
                parts = text.split()
                for i, p in enumerate(parts):
                    if "comment" in p.lower() and i > 0:
                        result["comments"] = int(parts[i-1].replace(",", ""))
            if "repost" in lowered or "repost" in lowered:
                parts = text.split()
                for i, p in enumerate(parts):
                    if "repost" in p.lower() and i > 0:
                        result["reposts"] = int(parts[i-1].replace(",", ""))
        except Exception:
            pass
        return result

    async def _extract_visible_comments(self, container, max_comments: int = 4) -> List[Dict[str, Any]]:
        comments: List[Dict[str, Any]] = []
        try:
            comment_items = container.locator(".comments-comment-item").all()
            items = await comment_items
            for item in items[:max_comments]:
                try:
                    text = (await item.locator(".comments-comment-item-content").first.inner_text(timeout=1500)).strip()
                    author = ""
                    try:
                        author = (await item.locator(".comments-post-meta__name").first.inner_text(timeout=800)).strip()
                    except Exception:
                        pass
                    like_count = 0
                    try:
                        likes_text = await item.locator(".comments-comment-item__likes").first.inner_text(timeout=800)
                        like_count = int(likes_text.split()[0].replace(",", "")) if likes_text else 0
                    except Exception:
                        pass
                    quality = min(1.0, (len(text) / 280.0) * 0.6 + (0.4 if "?" in text or "!" in text else 0))
                    comments.append({
                        "text": text[:2800],
                        "author": author,
                        "like_count": like_count,
                        "quality_score": round(quality, 3),
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return comments

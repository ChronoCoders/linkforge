import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaseScraper(ABC):
    def __init__(self, cookie_file: str = "cookies.json", headless: bool = True):
        self.cookie_file = Path(cookie_file)
        self.headless = headless
        self._cookies: List[Dict[str, Any]] = []
        self._is_authenticated = False
        self.load_cookies()

    def load_cookies(self) -> List[Dict[str, Any]]:
        if self.cookie_file.exists():
            try:
                data = json.loads(self.cookie_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._cookies = data
            except Exception:
                self._cookies = []
        return self._cookies

    def save_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        self._cookies = cookies
        try:
            self.cookie_file.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_cookies(self) -> List[Dict[str, Any]]:
        return self._cookies

    def clear_cookies(self) -> None:
        self._cookies = []
        self._is_authenticated = False
        if self.cookie_file.exists():
            try:
                self.cookie_file.unlink()
            except Exception:
                pass

    def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        self._cookies = cookies or []
        self._is_authenticated = len(self._cookies) > 0

    def is_authenticated(self) -> bool:
        return self._is_authenticated and len(self._cookies) > 0

    async def refresh_cookies(self) -> bool:
        self._is_authenticated = False
        return False

    async def login(self) -> bool:
        return False

    @abstractmethod
    async def scrape_profile(
        self, url: str, cookies: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def scrape_posts_with_comments(
        self, profile_url: str, max_posts: int = 15, cookies: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        pass

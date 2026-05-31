from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.post import Post

class PostRepository(ABC):
    @abstractmethod
    async def get_by_id(self, post_id: int) -> Optional[Post]:
        pass

    @abstractmethod
    async def get_by_profile_id(self, profile_id: int, limit: int = 100) -> List[Post]:
        pass

    @abstractmethod
    async def save(self, post: Post) -> Post:
        pass

    @abstractmethod
    async def save_many(self, posts: List[Post]) -> List[Post]:
        pass

    @abstractmethod
    async def delete_by_profile(self, profile_id: int) -> int:
        pass

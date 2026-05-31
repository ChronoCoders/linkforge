from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.profile import Profile

class ProfileRepository(ABC):
    @abstractmethod
    async def get_by_id(self, profile_id: int) -> Optional[Profile]:
        pass

    @abstractmethod
    async def get_by_url(self, linkedin_url: str) -> Optional[Profile]:
        pass

    @abstractmethod
    async def list_recent(self, limit: int = 50) -> List[Profile]:
        pass

    @abstractmethod
    async def save(self, profile: Profile) -> Profile:
        pass

    @abstractmethod
    async def update(self, profile: Profile) -> Profile:
        pass

    @abstractmethod
    async def delete(self, profile_id: int) -> bool:
        pass

    @abstractmethod
    async def search_similar(self, embedding: List[float], limit: int = 10) -> List[Profile]:
        pass

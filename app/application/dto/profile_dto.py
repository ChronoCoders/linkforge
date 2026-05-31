from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl

from app.domain.entities.profile import Education, Experience


class ProfileCreateDTO(BaseModel):
    linkedin_url: HttpUrl
    force_refresh: bool = False


class ProfileResponseDTO(BaseModel):
    id: int
    linkedin_url: str
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    follower_count: Optional[int] = None
    connection_count: Optional[int] = None
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProfileListDTO(BaseModel):
    profiles: List[ProfileResponseDTO]
    total: int

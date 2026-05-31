from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class Experience(BaseModel):
    title: str
    company: str
    duration: Optional[str] = None
    description: Optional[str] = None

class Education(BaseModel):
    school: str
    degree: Optional[str] = None
    field: Optional[str] = None
    years: Optional[str] = None

class Profile(BaseModel):
    id: Optional[int] = None
    linkedin_url: HttpUrl
    full_name: str = Field(..., min_length=1)
    headline: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None
    follower_count: Optional[int] = None
    connection_count: Optional[int] = None
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

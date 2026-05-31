from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class Comment(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    text: str = Field(..., min_length=1, max_length=3000)
    author: Optional[str] = Field(default=None, max_length=200)
    like_count: int = Field(default=0, ge=0)
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class Post(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True, extra="forbid")
    id: Optional[int] = None
    profile_id: int = Field(..., gt=0)
    linkedin_post_id: str = Field(..., min_length=3, max_length=120)
    content: str = Field(..., min_length=1, max_length=12000)
    post_type: Optional[str] = Field(default=None, max_length=50)
    like_count: int = Field(default=0, ge=0)
    comment_count: int = Field(default=0, ge=0)
    repost_count: int = Field(default=0, ge=0)
    posted_at: Optional[datetime] = None
    media_urls: List[str] = Field(default_factory=list)
    comments: List[Comment] = Field(default_factory=list)
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    sentiment_score: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    embedding: Optional[List[float]] = Field(default=None, min_length=384, max_length=384)
    created_at: Optional[datetime] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("content must not be empty after stripping")
        return v

    @field_validator("media_urls")
    @classmethod
    def validate_media_urls(cls, v: List[str]) -> List[str]:
        return [u for u in v if u and len(u) < 1000]

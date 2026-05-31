from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.infrastructure.database.base import Base

class ProfileModel(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    linkedin_url: Mapped[str] = mapped_column(String(600), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    headline: Mapped[Optional[str]] = mapped_column(String(400))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    about: Mapped[Optional[str]] = mapped_column(Text)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(600))
    follower_count: Mapped[Optional[int]] = mapped_column(Integer)
    connection_count: Mapped[Optional[int]] = mapped_column(Integer)
    experience: Mapped[list] = mapped_column(JSONB, default=list)
    education: Mapped[list] = mapped_column(JSONB, default=list)
    skills: Mapped[list] = mapped_column(JSONB, default=list)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    posts: Mapped[List[PostModel]] = relationship(back_populates="profile", cascade="all, delete-orphan")

class PostModel(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    linkedin_post_id: Mapped[Optional[str]] = mapped_column(String(120), unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[Optional[str]] = mapped_column(String(50))
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    repost_count: Mapped[int] = mapped_column(Integer, default=0)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    media_urls: Mapped[list] = mapped_column(JSONB, default=list)
    comments: Mapped[list] = mapped_column(JSONB, default=list)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    sentiment_score: Mapped[Optional[float]] = mapped_column(default=None)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped[ProfileModel] = relationship(back_populates="posts")

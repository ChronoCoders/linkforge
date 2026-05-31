from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.post import Comment, Post
from app.domain.repositories.post_repository import PostRepository
from app.infrastructure.database.models import PostModel


class SQLPostRepository(PostRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: PostModel) -> Post:
        comments = []
        for c in model.comments or []:
            if isinstance(c, dict):
                comments.append(Comment(**c))
        return Post(
            id=model.id,
            profile_id=model.profile_id,
            linkedin_post_id=model.linkedin_post_id or "",
            content=model.content,
            post_type=model.post_type,
            like_count=model.like_count or 0,
            comment_count=model.comment_count or 0,
            repost_count=model.repost_count or 0,
            posted_at=model.posted_at,
            media_urls=model.media_urls or [],
            comments=comments,
            raw_data=model.raw_data or {},
            sentiment_score=model.sentiment_score,
            embedding=list(model.embedding) if model.embedding is not None else None,
            created_at=model.created_at,
        )

    async def get_by_id(self, post_id: int) -> Optional[Post]:
        model = await self.db.get(PostModel, post_id)
        return self._to_entity(model) if model else None

    async def get_by_profile_id(self, profile_id: int, limit: int = 100) -> List[Post]:
        stmt = (
            select(PostModel)
            .where(PostModel.profile_id == profile_id)
            .order_by(PostModel.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def list_posts_with_analysis(self, profile_id: int, limit: int = 50) -> List[Post]:
        stmt = (
            select(PostModel)
            .where(PostModel.profile_id == profile_id)
            .order_by(
                (PostModel.like_count + PostModel.comment_count * 2 + PostModel.repost_count).desc()
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_posts_for_training(self, limit: int = 500) -> List[Post]:
        stmt = select(PostModel).order_by(PostModel.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, post: Post) -> Post:
        model = PostModel(
            profile_id=post.profile_id,
            linkedin_post_id=post.linkedin_post_id,
            content=post.content,
            post_type=post.post_type,
            like_count=post.like_count,
            comment_count=post.comment_count,
            repost_count=post.repost_count,
            posted_at=post.posted_at,
            media_urls=post.media_urls,
            comments=[c.model_dump() for c in post.comments],
            raw_data=post.raw_data,
            sentiment_score=post.sentiment_score,
            embedding=post.embedding,
        )
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def save_many(self, posts: List[Post]) -> List[Post]:
        models = []
        for p in posts:
            m = PostModel(
                profile_id=p.profile_id,
                linkedin_post_id=p.linkedin_post_id,
                content=p.content,
                post_type=p.post_type,
                like_count=p.like_count,
                comment_count=p.comment_count,
                repost_count=p.repost_count,
                posted_at=p.posted_at,
                media_urls=p.media_urls,
                comments=[c.model_dump() for c in p.comments],
                raw_data=p.raw_data,
                sentiment_score=p.sentiment_score,
                embedding=p.embedding,
            )
            models.append(m)
        self.db.add_all(models)
        await self.db.commit()
        for m in models:
            await self.db.refresh(m)
        return [self._to_entity(m) for m in models]

    async def delete_by_profile(self, profile_id: int) -> int:
        stmt = delete(PostModel).where(PostModel.profile_id == profile_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0

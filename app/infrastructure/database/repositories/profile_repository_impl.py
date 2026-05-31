from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.profile import Education, Experience, Profile
from app.domain.repositories.profile_repository import ProfileRepository
from app.infrastructure.database.models import ProfileModel


class SQLProfileRepository(ProfileRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: ProfileModel) -> Profile:
        return Profile(
            id=model.id,
            linkedin_url=model.linkedin_url,
            full_name=model.full_name,
            headline=model.headline,
            location=model.location,
            about=model.about,
            follower_count=model.follower_count,
            connection_count=model.connection_count,
            experience=[Experience(**e) for e in (model.experience or [])],
            education=[Education(**e) for e in (model.education or [])],
            skills=model.skills or [],
            raw_data=model.raw_data or {},
            embedding=list(model.embedding) if model.embedding is not None else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, profile: Profile) -> ProfileModel:
        return ProfileModel(
            id=profile.id,
            linkedin_url=str(profile.linkedin_url),
            full_name=profile.full_name,
            headline=profile.headline,
            location=profile.location,
            about=profile.about,
            follower_count=profile.follower_count,
            connection_count=profile.connection_count,
            experience=[e.model_dump() for e in profile.experience],
            education=[e.model_dump() for e in profile.education],
            skills=profile.skills,
            raw_data=profile.raw_data,
            embedding=profile.embedding,
        )

    async def get_by_id(self, profile_id: int) -> Optional[Profile]:
        model = await self.db.get(ProfileModel, profile_id)
        return self._to_entity(model) if model else None

    async def get_by_url(self, linkedin_url: str) -> Optional[Profile]:
        stmt = select(ProfileModel).where(ProfileModel.linkedin_url == linkedin_url)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_recent(self, limit: int = 50) -> List[Profile]:
        stmt = select(ProfileModel).order_by(ProfileModel.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, profile: Profile) -> Profile:
        model = self._to_model(profile)
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def update(self, profile: Profile) -> Profile:
        model = await self.db.get(ProfileModel, profile.id)
        if not model:
            return await self.save(profile)
        model_data = self._to_model(profile)
        for key, value in model_data.__dict__.items():
            if key not in ("_sa_instance_state", "id"):
                setattr(model, key, value)
        await self.db.commit()
        await self.db.refresh(model)
        return self._to_entity(model)

    async def delete(self, profile_id: int) -> bool:
        model = await self.db.get(ProfileModel, profile_id)
        if model:
            await self.db.delete(model)
            await self.db.commit()
            return True
        return False

    async def search_similar(self, embedding: List[float], limit: int = 10) -> List[Profile]:
        stmt = (
            select(ProfileModel)
            .order_by(ProfileModel.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

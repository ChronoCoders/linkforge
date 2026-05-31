from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_async_profile_repository
from app.api.v1.schemas.profile import ProfileCreateRequest, ProfileListResponse, ProfileResponse
from app.application.dto.profile_dto import ProfileCreateDTO, ProfileResponseDTO
from app.application.use_cases.scrape_and_analyze import ScrapeAndAnalyzeUseCase
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileResponse)
async def create_profile(
    payload: ProfileCreateRequest,
    repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
) -> ProfileResponseDTO:
    use_case = ScrapeAndAnalyzeUseCase(repo)
    try:
        return await use_case.execute(ProfileCreateDTO(**payload.model_dump()))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int, repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)]
) -> ProfileResponse:
    profile = await repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(
        id=profile.id or 0,
        linkedin_url=str(profile.linkedin_url),
        full_name=profile.full_name,
        headline=profile.headline,
        location=profile.location,
        about=profile.about,
        follower_count=profile.follower_count,
        experience=profile.experience,
        education=profile.education,
        skills=profile.skills,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)], limit: int = 50
) -> ProfileListResponse:
    profiles = await repo.list_recent(limit=limit)
    return ProfileListResponse(
        profiles=[
            ProfileResponse(
                id=p.id or 0,
                linkedin_url=str(p.linkedin_url),
                full_name=p.full_name,
                headline=p.headline,
                location=p.location,
                about=p.about,
                follower_count=p.follower_count,
                experience=p.experience,
                education=p.education,
                skills=p.skills,
                created_at=p.created_at,
            )
            for p in profiles
        ],
        total=len(profiles),
    )

from typing import Annotated, Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.v1.schemas.profile import ProfileCreateRequest, ProfileResponse, ProfileListResponse
from app.application.use_cases.scrape_and_analyze import ScrapeAndAnalyzeUseCase
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository
from app.api.v1.dependencies import get_async_profile_repository

router = APIRouter(prefix="/profiles", tags=["profiles"])

class CookieUpdateRequest(BaseModel):
    cookies: List[Dict[str, Any]]

class ProfileWithCookiesResponse(ProfileResponse):
    has_cookies: bool = False

@router.post("", response_model=ProfileResponse)
async def create_profile(
    payload: ProfileCreateRequest,
    repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
):
    use_case = ScrapeAndAnalyzeUseCase(repo)
    try:
        return await use_case.execute(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: int, repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)]):
    profile = await repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileResponse(
        id=profile.id,
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
async def list_profiles(repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)], limit: int = 50):
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

@router.post("/{profile_id}/cookies")
async def update_profile_cookies(
    profile_id: int,
    payload: CookieUpdateRequest,
    repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
):
    profile = await repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.raw_data = profile.raw_data or {}
    profile.raw_data["cookies"] = payload.cookies
    await repo.update(profile)
    return {"status": "cookies updated", "profile_id": profile_id}

@router.get("/{profile_id}/cookies")
async def get_profile_cookies(
    profile_id: int,
    repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
):
    profile = await repo.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    cookies = (profile.raw_data or {}).get("cookies", [])
    return {"profile_id": profile_id, "cookies": cookies, "has_cookies": len(cookies) > 0}

@router.get("/with_auth", response_model=List[ProfileWithCookiesResponse])
async def list_profiles_with_auth_status(repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)], limit: int = 50):
    profiles = await repo.list_recent(limit=limit)
    result = []
    for p in profiles:
        cookies = (p.raw_data or {}).get("cookies", [])
        resp = ProfileWithCookiesResponse(
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
            has_cookies=len(cookies) > 0,
        )
        result.append(resp)
    return result

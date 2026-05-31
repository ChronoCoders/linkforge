from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.v1.dependencies import get_async_profile_repository, get_post_repository
from app.api.v1.schemas.analytics import AnalyticsRequest, AnalyticsResponse
from app.application.dto.analytics_dto import AnalyticsRequestDTO
from app.application.use_cases.get_insights import GetProfileInsightsUseCase
from app.infrastructure.database.repositories.post_repository_impl import SQLPostRepository
from app.infrastructure.database.repositories.profile_repository_impl import SQLProfileRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])


class RecommendationRequest(BaseModel):
    profile_id: int


class ComparisonRequest(BaseModel):
    profile_id: int
    post_ids: List[int]


@router.post("/profile", response_model=AnalyticsResponse)
async def get_profile_analytics(
    payload: AnalyticsRequest,
    profile_repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
    post_repo: Annotated[SQLPostRepository, Depends(get_post_repository)],
) -> AnalyticsResponse:
    use_case = GetProfileInsightsUseCase(profile_repo, post_repo)
    try:
        result = await use_case.execute(AnalyticsRequestDTO(**payload.model_dump()))
        return AnalyticsResponse(**result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations")
async def get_next_post_recommendations(
    payload: RecommendationRequest,
    profile_repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
    post_repo: Annotated[SQLPostRepository, Depends(get_post_repository)],
) -> dict[str, Any]:
    use_case = GetProfileInsightsUseCase(profile_repo, post_repo)
    try:
        result = await use_case.execute(
            AnalyticsRequestDTO(profile_id=payload.profile_id, include_posts=True)
        )
        return {
            "profile_id": payload.profile_id,
            "next_post_plan": result.next_post_plan,
            "ml_recommendations": result.next_best_posts,
            "recommendation": result.recommendation,
            "recommendation_confidence": result.recommendation_confidence,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends")
async def get_trends(
    payload: RecommendationRequest,
    profile_repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
    post_repo: Annotated[SQLPostRepository, Depends(get_post_repository)],
) -> dict[str, Any]:
    use_case = GetProfileInsightsUseCase(profile_repo, post_repo)
    try:
        result = await use_case.execute(
            AnalyticsRequestDTO(
                profile_id=payload.profile_id, include_posts=True, include_historical=True
            )
        )
        return {
            "profile_id": payload.profile_id,
            "trend_data": result.trend_data,
            "historical_comparison": result.historical_comparison,
            "post_performance_reports": result.post_performance_reports,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_posts(
    payload: ComparisonRequest,
    profile_repo: Annotated[SQLProfileRepository, Depends(get_async_profile_repository)],
    post_repo: Annotated[SQLPostRepository, Depends(get_post_repository)],
) -> dict[str, Any]:
    use_case = GetProfileInsightsUseCase(profile_repo, post_repo)
    try:
        result = await use_case.execute(
            AnalyticsRequestDTO(profile_id=payload.profile_id, include_posts=True)
        )
        reports = result.post_performance_reports
        selected = [r for r in reports if r.get("post_id") in payload.post_ids]
        return {
            "profile_id": payload.profile_id,
            "compared_posts": selected,
            "comparison_summary": {
                "count": len(selected),
                "avg_engagement": sum(r.get("engagement_score", 0) for r in selected)
                / max(len(selected), 1),
                "top_theme": selected[0].get("themes", [""])[0] if selected else "",
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

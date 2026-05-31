from app.application.dto.profile_dto import ProfileCreateDTO, ProfileResponseDTO
from app.application.services.linkedin_service import LinkedInService
from app.domain.repositories.post_repository import PostRepository
from app.domain.repositories.profile_repository import ProfileRepository


class ScrapeAndAnalyzeUseCase:
    def __init__(
        self, profile_repository: ProfileRepository, post_repository: PostRepository | None = None
    ) -> None:
        self.service = LinkedInService(profile_repository, post_repository)

    async def execute(self, dto: ProfileCreateDTO) -> ProfileResponseDTO:
        profile = await self.service.get_or_scrape_profile(
            str(dto.linkedin_url), force_refresh=dto.force_refresh
        )
        if self.service.post_repository:
            await self.service.scrape_and_store_posts(
                profile_id=profile.id or 0,
                profile_url=str(dto.linkedin_url),
                max_posts=12,
            )
        return ProfileResponseDTO(
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

from datetime import datetime
from typing import Any, Dict, List

from app.application.dto.analytics_dto import AnalyticsRequestDTO, AnalyticsResponseDTO
from app.application.services.recommendation_service import RecommendationService
from app.domain.repositories.post_repository import PostRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.infrastructure.analysis.performance_predictor import PerformancePredictor
from app.infrastructure.analysis.sentiment_analyzer import SentimentAnalyzer
from app.infrastructure.analysis.text_analyzer import TextAnalyzer


class GetProfileInsightsUseCase:
    def __init__(
        self, profile_repository: ProfileRepository, post_repository: PostRepository
    ) -> None:
        self.profile_repository = profile_repository
        self.post_repository = post_repository
        self.sentiment_analyzer = SentimentAnalyzer()
        self.text_analyzer = TextAnalyzer()
        self.predictor = PerformancePredictor()
        self.recommendation_service = RecommendationService()

    def _compute_post_performance(self, posts: List[Any]) -> List[Dict[str, Any]]:
        reports = []
        for post in posts:
            if not post.content:
                continue
            engagement = (
                (post.like_count or 0)
                + (post.comment_count or 0) * 3
                + (post.repost_count or 0) * 2
            )
            sentiment = self.sentiment_analyzer.analyze(
                post.content, getattr(post, "comments", None)
            )
            themes = self.text_analyzer.detect_themes(post.content, getattr(post, "comments", None))
            score = engagement * (
                1 + sentiment.get("pragmatic", 0) - sentiment.get("tribalism", 0) * 0.5
            )
            reports.append(
                {
                    "post_id": post.id,
                    "content_snippet": (
                        post.content[:200] + "..." if len(post.content) > 200 else post.content
                    ),
                    "engagement_score": engagement,
                    "sentiment_compound": sentiment.get("compound", 0.0),
                    "pragmatic_score": sentiment.get("pragmatic", 0.0),
                    "tribalism_score": sentiment.get("tribalism", 0.0),
                    "themes": themes,
                    "performance_score": round(score, 2),
                    "posted_at": str(post.posted_at) if post.posted_at else None,
                }
            )
        reports.sort(key=lambda x: x["performance_score"], reverse=True)
        return reports

    async def execute(self, dto: AnalyticsRequestDTO) -> AnalyticsResponseDTO:
        profile = await self.profile_repository.get_by_id(dto.profile_id)
        if not profile:
            raise ValueError("Profile not found")

        posts = (
            await self.post_repository.get_posts_for_training(limit=200)
            if dto.include_posts
            else []
        )
        profile_posts = [p for p in posts if getattr(p, "profile_id", None) == dto.profile_id][:30]

        all_text = profile.about or ""
        all_comments: List[Dict[str, Any]] = []

        for post in profile_posts:
            all_text += " " + (post.content or "")
            all_comments.extend(getattr(post, "comments", []) or [])

        sentiment = self.sentiment_analyzer.analyze(all_text, all_comments)
        theme_analysis = self.text_analyzer.analyze(all_text, all_comments)

        self.predictor.train(posts)
        ml_recommendations = self.predictor.generate_recommendations(
            sentiment, theme_analysis.get("themes", []), num=3
        )

        next_post_plan = self.recommendation_service.generate_next_post_plan(profile_posts, profile)

        post_reports = self._compute_post_performance(profile_posts)

        best_rec = ml_recommendations[0] if ml_recommendations else {}
        performance_prediction = best_rec.get("success_probability", 0.0) if best_rec else 0.0

        response = AnalyticsResponseDTO(
            profile_id=dto.profile_id,
            overall_sentiment=sentiment.get("compound"),
            sentiment_breakdown=sentiment,
            themes=theme_analysis.get("themes", []),
            polarization_score=theme_analysis.get("polarization_score", 0.0),
            performance_prediction=round(performance_prediction, 4),
            post_count=len(profile_posts),
            generated_at=datetime.utcnow(),
        )

        response.recommendation = {
            "suggested_tone": best_rec.get("tone", "pragmatic_balance"),
            "suggested_themes": (
                [best_rec.get("theme", "technical_deep_dive")]
                if best_rec
                else ["technical_deep_dive"]
            ),
            "predicted_engagement": best_rec.get("predicted_engagement", 0.0) if best_rec else 0.0,
            "confidence": best_rec.get("confidence", 0.65) if best_rec else 0.5,
            "alternatives": ml_recommendations[1:] if len(ml_recommendations) > 1 else [],
        }
        response.next_best_posts = ml_recommendations
        response.next_post_plan = next_post_plan
        response.post_performance_reports = post_reports
        response.next_post_strategy = {
            "topic": next_post_plan.get("topic"),
            "tone": next_post_plan.get("tone"),
            "structure": next_post_plan.get("structure", []),
            "hook": next_post_plan.get("hook"),
            "recommended_length": next_post_plan.get("recommended_length"),
            "why_it_works": next_post_plan.get("why_it_works"),
            "predicted_lift": next_post_plan.get("predicted_engagement_lift", 0.0),
        }
        return response

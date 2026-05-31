from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalyticsRequestDTO(BaseModel):
    profile_id: int
    include_posts: bool = True
    include_sentiment: bool = True
    include_historical: bool = False

class AnalyticsResponseDTO(BaseModel):
    profile_id: int
    overall_sentiment: Optional[float] = None
    sentiment_breakdown: Dict[str, float] = Field(default_factory=dict)
    themes: List[str] = Field(default_factory=list)
    theme_confidences: Dict[str, float] = Field(default_factory=dict)
    polarization_score: float = 0.0
    polarization_details: Dict[str, float] = Field(default_factory=dict)
    performance_prediction: float = 0.0
    post_count: int = 0
    post_performance_reports: List[Dict[str, Any]] = Field(default_factory=list)
    next_post_strategy: Dict[str, Any] = Field(default_factory=dict)
    recommendation: Dict[str, Any] = Field(default_factory=dict)
    next_best_posts: List[Dict[str, Any]] = Field(default_factory=list)
    next_post_plan: Dict[str, Any] = Field(default_factory=dict)
    recommendation_confidence: Dict[str, float] = Field(default_factory=dict)
    historical_comparison: Dict[str, Any] = Field(default_factory=dict)
    trend_data: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

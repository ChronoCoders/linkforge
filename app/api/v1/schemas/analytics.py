from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime

class AnalyticsRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    profile_id: int
    include_posts: bool = True
    include_sentiment: bool = True

class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)
    profile_id: int
    overall_sentiment: Optional[float] = None
    sentiment_breakdown: Dict[str, float] = Field(default_factory=dict)
    themes: List[str] = Field(default_factory=list)
    polarization_score: float = 0.0
    performance_prediction: float = 0.0
    post_count: int = 0
    generated_at: datetime

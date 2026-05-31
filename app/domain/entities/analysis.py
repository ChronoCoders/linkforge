from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CommentQualityMetrics(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    avg_length: float = 0.0
    question_ratio: float = 0.0
    positive_ratio: float = 0.0
    avg_quality_score: float = 0.0


class AnalysisResult(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True, extra="forbid")
    id: Optional[int] = None
    profile_id: int = Field(..., gt=0)
    analysis_type: str = Field(..., min_length=2, max_length=80)
    scores: Dict[str, float] = Field(default_factory=dict)
    summary: Optional[str] = Field(default=None, max_length=2000)
    clusters: Optional[List[int]] = None
    keywords: List[str] = Field(default_factory=list)
    comment_metrics: Optional[CommentQualityMetrics] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

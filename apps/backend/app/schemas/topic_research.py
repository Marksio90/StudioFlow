from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TopicResearchRecommendation(str, Enum):
    approved = "approved"
    needs_more_research = "needs_more_research"
    too_generic = "too_generic"
    reject = "reject"


class TopicResearchScores(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    demand_score: float = Field(ge=0, le=100)
    competition_score: float = Field(ge=0, le=100)
    novelty_score: float = Field(ge=0, le=100)
    channel_fit_score: float = Field(ge=0, le=100)
    execution_risk_score: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)


class TopicResearchReportOut(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    recommendation: TopicResearchRecommendation
    rationale: str = Field(min_length=1)
    summary: str = ""
    audience_fit: str = ""
    key_points: list[str] = Field(default_factory=list)
    demand_signals: list[str] = Field(default_factory=list)
    competition_notes: list[str] = Field(default_factory=list)
    content_gaps: list[str] = Field(default_factory=list)
    suggested_angles: list[str] = Field(default_factory=list)
    source_queries: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    scores: TopicResearchScores


class TopicResearchAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    notes: str = Field(default="", max_length=12000)
    channel_context_overrides: dict = Field(default_factory=dict)
    channel_memory_overrides: dict = Field(default_factory=dict)


class TopicResearchAnalyzeResponseOut(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: UUID
    content_idea_id: UUID
    channel_id: UUID
    report: TopicResearchReportOut
    created_at: datetime


class TopicResearchReportListOut(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    items: list[TopicResearchAnalyzeResponseOut]

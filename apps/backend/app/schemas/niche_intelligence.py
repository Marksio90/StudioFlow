from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NicheScoreSet(BaseModel):
    demand_score: float = Field(ge=0, le=100)
    competition_score: float = Field(ge=0, le=100)
    originality_potential: float = Field(ge=0, le=100)
    production_difficulty: float = Field(ge=0, le=100)
    monetization_potential: float = Field(ge=0, le=100)
    compliance_risk: float = Field(ge=0, le=100)
    long_term_depth: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)


class NicheAnalysisResult(BaseModel):
    summary: str = Field(min_length=1)
    score_explanations: dict[str, str]
    strengths: list[str]
    weaknesses: list[str]
    risks: list[str]
    recommended_positioning: str
    content_pillar_suggestions: list[str]
    differentiation_opportunities: list[str]
    compliance_notes: list[str]
    next_actions: list[str]
    scores: NicheScoreSet


class NicheAnalyzeRequest(BaseModel):
    notes: str = Field(default='', max_length=12000)


class NicheIntelligenceReportOut(BaseModel):
    id: UUID
    channel_id: UUID
    summary: str
    score_explanations: dict[str, str]
    strengths: list[str]
    weaknesses: list[str]
    risks: list[str]
    recommended_positioning: str
    content_pillar_suggestions: list[str]
    differentiation_opportunities: list[str]
    compliance_notes: list[str]
    next_actions: list[str]
    scores: NicheScoreSet
    created_at: datetime


class NicheIntelligenceReportListOut(BaseModel):
    items: list[NicheIntelligenceReportOut]

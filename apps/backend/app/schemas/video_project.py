from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.enums import ComplianceRiskLevel, PublishingPlanStatus, VideoProjectStatus
from app.schemas.topic_research import (
    TopicResearchAnalyzeResponseOut as ContentIdeaResearchAnalyzeResponse,
    TopicResearchReportListOut as ContentIdeaResearchReportListResponse,
    TopicResearchReportOut as ContentIdeaResearchReportPayload,
)


class VideoProjectCreate(BaseModel):
    organization_id: UUID
    workspace_id: UUID
    channel_id: UUID
    title: str = Field(min_length=1, max_length=255)


class VideoProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[VideoProjectStatus] = None


class ApprovalAggregateOut(BaseModel):
    video_project_id: UUID
    status: str
    requested_at: datetime | None = None
    decided_at: datetime | None = None
    decided_by_user_id: UUID | None = None
    latest_comment: str | None = None


class VideoProjectOut(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    channel_id: UUID
    title: str
    status: VideoProjectStatus
    approval: ApprovalAggregateOut | None = None
    created_at: datetime
    updated_at: datetime


class PaginatedVideoProjects(BaseModel):
    items: list[VideoProjectOut]
    total: int
    limit: int
    offset: int


class WorkflowRunOut(BaseModel):
    id: UUID
    video_project_id: UUID
    state: str


class WorkflowEventOut(BaseModel):
    id: UUID
    workflow_run_id: UUID
    event_type: str
    payload: dict


class ComplianceOut(BaseModel):
    risk_level: ComplianceRiskLevel
    findings: Optional[str] = None


class ComplianceReportOut(BaseModel):
    video_project_id: UUID
    score: int
    risk_level: ComplianceRiskLevel
    requires_ai_disclosure: bool
    disclosure_decision_missing: bool
    ai_disclosure_risk: str
    inauthentic_content_risk: str
    repetitive_content_risk: str
    copyright_risk: str
    sensitive_claims_risk: str
    clickbait_risk: str
    asset_license_risk: str
    synthetic_media_realism_risk: str
    reasons: list[str]
    recommendations: list[str]
    blocking_issues: list[str]




class ApprovalDecisionIn(BaseModel):
    comment: str | None = None
    decided_by_user_id: UUID


class ApprovalDecisionOut(BaseModel):
    id: UUID
    video_project_id: UUID
    status: str
    comment: str | None = None
    decided_by_user_id: UUID
    created_at: datetime


class AnalyticsSnapshotIn(BaseModel):
    channel_id: UUID
    youtube_video_id: str
    views: int
    watch_time_minutes: float
    average_view_duration: float
    ctr: float
    likes: int
    comments: int
    subscribers_gained: int
    estimated_revenue: float
    snapshot_at: datetime


class AnalyticsSnapshotOut(AnalyticsSnapshotIn):
    id: UUID
    video_project_id: UUID
    created_at: datetime
    updated_at: datetime


class PublishingPlanCreate(BaseModel):
    video_project_id: UUID
    channel_id: UUID
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    visibility: str = "private"
    selected_title_variant_id: UUID | None = None
    selected_thumbnail_concept_id: UUID | None = None
    final_description_snapshot: str | None = None
    final_tags_snapshot: list[str] | None = None
    compliance_report_id: UUID | None = None
    asset_bundle_metadata: dict | None = None


class PublishingPlanSchedule(BaseModel):
    scheduled_at: datetime


class PublishingPlanOut(BaseModel):
    id: UUID
    video_project_id: UUID
    channel_id: UUID
    scheduled_at: datetime | None
    status: PublishingPlanStatus
    youtube_video_id: str | None
    title: str
    description: str
    tags: list[str]
    visibility: str
    selected_title_variant_id: UUID | None = None
    selected_thumbnail_concept_id: UUID | None = None
    final_description_snapshot: str | None = None
    final_tags_snapshot: list[str] | None = None
    compliance_report_id: UUID | None = None
    asset_bundle_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime


class ChannelMemoryCreate(BaseModel):
    channel_id: UUID
    memory: dict


class ProjectScopedEntityBase(BaseModel):
    video_project_id: UUID
    status: str | None = None


class ResearchBriefCreate(ProjectScopedEntityBase):
    brief: dict


class AngleCreate(ProjectScopedEntityBase):
    angle: dict


class HookVariantCreate(ProjectScopedEntityBase):
    hook: dict


class RetentionReviewCreate(ProjectScopedEntityBase):
    review: dict


class VisualPlanCreate(ProjectScopedEntityBase):
    plan: dict


class VisualSceneCreate(ProjectScopedEntityBase):
    scene: dict


class AudioBriefCreate(ProjectScopedEntityBase):
    brief: dict


class TitleVariantCreate(ProjectScopedEntityBase):
    title_variant: dict


class ThumbnailConceptCreate(ProjectScopedEntityBase):
    concept: dict


class MonetizationPlanCreate(ProjectScopedEntityBase):
    plan: dict


class ContentIdeaBase(BaseModel):
    video_project_id: UUID
    channel_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    status: str = "idea"
    content_pillar: str = ""
    target_keyword: str = ""
    viewer_problem: str = ""
    viewer_promise: str = ""
    notes: str = ""
    niche_score: float = 0
    topic_score: float = 0
    originality_score: float = 0
    risk_score: float = 0
    # Backward-compatible alias field.
    idea_text: str | None = None


class ContentIdeaCreate(ContentIdeaBase):
    """Deprecated create schema kept for backward compatibility."""


class ContentIdeaScorePayload(BaseModel):
    niche_score: float = 0
    topic_score: float = 0
    originality_score: float = 0
    risk_score: float = 0


class ContentIdeaCreatePayload(BaseModel):
    video_project_id: UUID
    channel_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    content_pillar: str = ""
    target_keyword: str = ""
    viewer_problem: str = ""
    viewer_promise: str = ""
    notes: str = ""
    status: str = "idea"
    scores: ContentIdeaScorePayload | None = None
    idea_text: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _map_legacy_fields(cls, data):
        if not isinstance(data, dict):
            return data
        payload = dict(data)
        scores = payload.get("scores") if isinstance(payload.get("scores"), dict) else {}
        for field in ("niche_score", "topic_score", "originality_score", "risk_score"):
            if field in payload and field not in scores:
                scores[field] = payload[field]
        if scores:
            payload["scores"] = scores
        return payload


class ContentIdeaUpdatePayload(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    content_pillar: str | None = None
    target_keyword: str | None = None
    viewer_problem: str | None = None
    viewer_promise: str | None = None
    notes: str | None = None
    scores: ContentIdeaScorePayload | None = None
    idea_text: str | None = None

    model_config = ConfigDict(extra="forbid")


class ContentIdeaStatusChangePayload(BaseModel):
    status: str


class ContentIdeaListFilters(BaseModel):
    status: str | None = None
    content_pillar: str | None = None
    q: str | None = None
    include_archived: bool = False


class ContentIdeaOut(ContentIdeaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ContentIdeaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_project_id: UUID
    channel_id: UUID | None = None
    title: str
    description: str
    status: str
    content_pillar: str
    target_keyword: str
    viewer_problem: str
    viewer_promise: str
    notes: str
    scores: ContentIdeaScorePayload
    created_at: datetime
    updated_at: datetime
    idea_text: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _inflate_scores(cls, data):
        if not isinstance(data, dict):
            data = getattr(data, "__dict__", {})
        payload = dict(data)
        if "scores" not in payload or payload.get("scores") is None:
            payload["scores"] = {
                "niche_score": payload.get("niche_score", 0),
                "topic_score": payload.get("topic_score", 0),
                "originality_score": payload.get("originality_score", 0),
                "risk_score": payload.get("risk_score", 0),
            }
        return payload


# Deprecated compatibility aliases for existing VideoIdea naming.
VideoIdeaBase = ContentIdeaBase
VideoIdeaCreate = ContentIdeaCreate
VideoIdeaOut = ContentIdeaOut


def content_idea_from_video_idea_payload(payload: dict) -> ContentIdeaCreate:
    """Backward-compatible request adapter from VideoIdea payload shape."""
    canonical = ContentIdeaCreatePayload(**payload)
    data = canonical.model_dump()
    scores = data.pop("scores") or {}
    return ContentIdeaCreate(**data, **scores)


def content_idea_to_video_idea_response(content_idea: ContentIdeaOut | ContentIdeaResponse) -> VideoIdeaOut:
    """Backward-compatible response adapter to VideoIdea schema."""
    data = content_idea.model_dump()
    if "scores" in data:
        scores = data.pop("scores") or {}
        data.update(scores)
    return VideoIdeaOut(**data)

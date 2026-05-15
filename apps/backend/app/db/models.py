from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.enums import ApprovalStatus, ComplianceRiskLevel, PublishingPlanStatus, VideoProjectStatus


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_code: Mapped[str] = mapped_column(String(64), nullable=False, default="starter")


class Workspace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspaces"
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)


class Membership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memberships"
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)


class Channel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("organization_id", "workspace_id", "slug", name="uq_channels_org_workspace_slug"),
        Index("ix_channels_workspace_slug", "workspace_id", "slug"),
    )

    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    niche: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    language: Mapped[str] = mapped_column(String(32), nullable=False, default="en")
    target_audience: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tone_of_voice: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_pillars: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    brand_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    youtube_channel_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class VideoProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "video_projects"
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False)
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[VideoProjectStatus] = mapped_column(Enum(VideoProjectStatus), default=VideoProjectStatus.draft, nullable=False)


class ContentIdea(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "video_ideas"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled idea")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="idea")
    content_pillar: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    target_keyword: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    viewer_problem: Mapped[str] = mapped_column(Text, nullable=False, default="")
    viewer_promise: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    niche_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    topic_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    originality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    # Deprecated compatibility field preserved for existing callers.
    idea_text: Mapped[str] = mapped_column(Text, nullable=False)


# Deprecated alias for backward compatibility.
VideoIdea = ContentIdea


class ScriptDraft(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "script_drafts"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class SEORecommendation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "seo_recommendations"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ComplianceReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_reports"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    risk_level: Mapped[ComplianceRiskLevel] = mapped_column(Enum(ComplianceRiskLevel), nullable=False)
    findings: Mapped[str] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class WorkflowRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_runs"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    state: Mapped[str] = mapped_column(String(64), nullable=False)


class WorkflowStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_steps"
    workflow_run_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    step_name: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)


class WorkflowEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_events"
    workflow_run_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class TaskExecution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "task_executions"
    workflow_run_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=True, index=True)
    task_name: Mapped[str] = mapped_column(String(128), nullable=False)
    business_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TaskAttempt(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "task_attempts"
    task_execution_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("task_executions.id"), nullable=False, index=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ApprovalDecision(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "approval_decisions"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.awaiting_review, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    decided_by_user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class Approval(Base):
    __tablename__ = "approvals"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), primary_key=True)
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.awaiting_review, nullable=False)
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    latest_comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class LLMCall(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "llm_calls"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_template_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_template_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_preview: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    output_preview: Mapped[str | None] = mapped_column(String(512), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class LLMCostLedgerEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "llm_cost_ledger_entries"
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False)
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)


class YouTubeQuotaLedgerEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "youtube_quota_ledger_entries"
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False)
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    workflow_run_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), index=True, nullable=True)
    youtube_method: Mapped[str] = mapped_column(String(128), nullable=False)
    quota_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    retry_of_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("youtube_quota_ledger_entries.id"), nullable=True)


class AnalyticsSnapshot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analytics_snapshots"
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class PublishingPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "publishing_plans"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PublishingPlanStatus] = mapped_column(Enum(PublishingPlanStatus), default=PublishingPlanStatus.draft, nullable=False)
    youtube_video_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="private")
    selected_title_variant_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("title_variants.id"), nullable=True)
    selected_thumbnail_concept_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("thumbnail_concepts.id"), nullable=True)
    final_description_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_tags_snapshot: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    compliance_report_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("compliance_reports.id"), nullable=True)
    asset_bundle_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class Asset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assets"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)


class AssetLicense(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "asset_licenses"
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    license_type: Mapped[str] = mapped_column(String(128), nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ChannelMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "channel_memories"
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    memory: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ResearchBrief(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "research_briefs"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    brief: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Angle(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "angles"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    angle: Mapped[dict] = mapped_column(JSONB, nullable=False)


class HookVariant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "hook_variants"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    hook: Mapped[dict] = mapped_column(JSONB, nullable=False)


class RetentionReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "retention_reviews"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    review: Mapped[dict] = mapped_column(JSONB, nullable=False)


class VisualPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "visual_plans"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    plan: Mapped[dict] = mapped_column(JSONB, nullable=False)


class VisualScene(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "visual_scenes"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    scene: Mapped[dict] = mapped_column(JSONB, nullable=False)


class AudioBrief(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audio_briefs"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    brief: Mapped[dict] = mapped_column(JSONB, nullable=False)


class TitleVariant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "title_variants"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    title_variant: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ThumbnailConcept(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "thumbnail_concepts"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    concept: Mapped[dict] = mapped_column(JSONB, nullable=False)


class MonetizationPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "monetization_plans"
    video_project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=True)
    channel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    plan: Mapped[dict] = mapped_column(JSONB, nullable=False)


Index("ix_video_projects_org_workspace_channel", VideoProject.organization_id, VideoProject.workspace_id, VideoProject.channel_id)
Index("ix_channel_memories_channel_created_at", ChannelMemory.channel_id, ChannelMemory.created_at)
Index("ix_research_briefs_project_created_at", ResearchBrief.video_project_id, ResearchBrief.created_at)
Index("ix_angles_project_created_at", Angle.video_project_id, Angle.created_at)
Index("ix_hook_variants_project_created_at", HookVariant.video_project_id, HookVariant.created_at)
Index("ix_retention_reviews_project_created_at", RetentionReview.video_project_id, RetentionReview.created_at)
Index("ix_visual_plans_project_created_at", VisualPlan.video_project_id, VisualPlan.created_at)
Index("ix_visual_scenes_project_created_at", VisualScene.video_project_id, VisualScene.created_at)
Index("ix_audio_briefs_project_created_at", AudioBrief.video_project_id, AudioBrief.created_at)
Index("ix_title_variants_project_created_at", TitleVariant.video_project_id, TitleVariant.created_at)
Index("ix_thumbnail_concepts_project_created_at", ThumbnailConcept.video_project_id, ThumbnailConcept.created_at)
Index("ix_monetization_plans_project_created_at", MonetizationPlan.video_project_id, MonetizationPlan.created_at)


class NicheIntelligenceReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "niche_intelligence_reports"
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    score_explanations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    risks: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    recommended_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    content_pillar_suggestions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    differentiation_opportunities: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    compliance_notes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    next_actions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class TopicResearchReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "topic_research_reports"
    content_idea_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_ideas.id"), index=True, nullable=False)
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    report: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

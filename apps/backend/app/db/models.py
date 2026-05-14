from sqlalchemy import Boolean, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.enums import ApprovalStatus, ComplianceRiskLevel, VideoProjectStatus


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(255), nullable=False)


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
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    youtube_channel_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class VideoProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "video_projects"
    organization_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False)
    channel_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("channels.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[VideoProjectStatus] = mapped_column(Enum(VideoProjectStatus), default=VideoProjectStatus.draft, nullable=False)


class VideoIdea(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "video_ideas"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    idea_text: Mapped[str] = mapped_column(Text, nullable=False)


class ScriptDraft(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "script_drafts"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class SEORecommendation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "seo_recommendations"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ComplianceReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "compliance_reports"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    risk_level: Mapped[ComplianceRiskLevel] = mapped_column(Enum(ComplianceRiskLevel), nullable=False)
    findings: Mapped[str] = mapped_column(Text, nullable=True)


class WorkflowRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_runs"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)


class WorkflowStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_steps"
    workflow_run_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    step_name: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False)


class WorkflowEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_events"
    workflow_run_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class ApprovalDecision(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "approval_decisions"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.pending, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)


class LLMCall(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "llm_calls"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)


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
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    scheduled_for: Mapped[str] = mapped_column(String(64), nullable=False)


class Asset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assets"
    video_project_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("video_projects.id"), index=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)


class AssetLicense(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "asset_licenses"
    asset_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    license_type: Mapped[str] = mapped_column(String(128), nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


Index("ix_video_projects_org_workspace_channel", VideoProject.organization_id, VideoProject.workspace_id, VideoProject.channel_id)

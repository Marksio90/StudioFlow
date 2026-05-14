"""domain core models

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260514_0001"
down_revision = None
branch_labels = None
depends_on = None

video_project_status_enum = sa.Enum("draft","researching","script_generating","seo_generating","compliance_checking","awaiting_review","approved","rejected","needs_changes","scheduled","published","analytics_pending","completed","failed","cancelled", name="videoprojectstatus")
compliance_risk_level_enum = sa.Enum("low", "medium", "high", "blocked", name="compliancerisklevel")
approval_status_enum = sa.Enum("awaiting_review", "approved", "rejected", "needs_changes", name="approvalstatus")
publishing_plan_status_enum = sa.Enum("draft", "scheduled", "uploading", "published", "failed", "cancelled", name="publishingplanstatus")


def _base_cols():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for enum_t in (video_project_status_enum, compliance_risk_level_enum, approval_status_enum, publishing_plan_status_enum):
        enum_t.create(bind, checkfirst=True)

    op.create_table("organizations", sa.Column("name", sa.String(255), nullable=False), *_base_cols(), sa.PrimaryKeyConstraint("id"))
    op.create_table("users", sa.Column("email", sa.String(255), nullable=False), sa.Column("display_name", sa.String(255), nullable=False), *_base_cols(), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("email"))
    op.create_table("workspaces", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("name", sa.String(255), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["organization_id"],["organizations.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_workspaces_organization_id"), "workspaces", ["organization_id"])
    op.create_table("memberships", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("role", sa.String(64), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["organization_id"],["organizations.id"]), sa.ForeignKeyConstraint(["workspace_id"],["workspaces.id"]), sa.ForeignKeyConstraint(["user_id"],["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_memberships_organization_id"), "memberships", ["organization_id"])
    op.create_index(op.f("ix_memberships_workspace_id"), "memberships", ["workspace_id"])
    op.create_table("channels", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("name", sa.String(255), nullable=False), sa.Column("youtube_channel_id", sa.String(255), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["organization_id"],["organizations.id"]), sa.ForeignKeyConstraint(["workspace_id"],["workspaces.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("youtube_channel_id"))
    op.create_index(op.f("ix_channels_organization_id"), "channels", ["organization_id"])
    op.create_index(op.f("ix_channels_workspace_id"), "channels", ["workspace_id"])
    op.create_table("video_projects", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("status", video_project_status_enum, nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["organization_id"],["organizations.id"]), sa.ForeignKeyConstraint(["workspace_id"],["workspaces.id"]), sa.ForeignKeyConstraint(["channel_id"],["channels.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_video_projects_organization_id"), "video_projects", ["organization_id"])
    op.create_index(op.f("ix_video_projects_workspace_id"), "video_projects", ["workspace_id"])
    op.create_index(op.f("ix_video_projects_channel_id"), "video_projects", ["channel_id"])
    op.create_index("ix_video_projects_org_workspace_channel", "video_projects", ["organization_id", "workspace_id", "channel_id"])
    
    op.create_table("video_ideas", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("idea_text", sa.Text(), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_video_ideas_video_project_id"), "video_ideas", ["video_project_id"])
    op.create_table("script_drafts", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("content", sa.Text(), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_script_drafts_video_project_id"), "script_drafts", ["video_project_id"])
    op.create_table("seo_recommendations", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_seo_recommendations_video_project_id"), "seo_recommendations", ["video_project_id"])
    op.create_table("compliance_reports", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("risk_level", compliance_risk_level_enum, nullable=False), sa.Column("findings", sa.Text(), nullable=True), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_compliance_reports_video_project_id"), "compliance_reports", ["video_project_id"])
    op.create_table("workflow_runs", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("state", sa.String(64), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_workflow_runs_video_project_id"), "workflow_runs", ["video_project_id"])
    op.create_table("workflow_steps", sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("step_name", sa.String(128), nullable=False), sa.Column("state", sa.String(64), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["workflow_run_id"],["workflow_runs.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("workflow_events", sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("event_type", sa.String(128), nullable=False), sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["workflow_run_id"],["workflow_runs.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("approval_decisions", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("status", approval_status_enum, nullable=False), sa.Column("comment", sa.Text(), nullable=True), sa.Column("decided_by_user_id", postgresql.UUID(as_uuid=True), nullable=True), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.ForeignKeyConstraint(["decided_by_user_id"],["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_approval_decisions_video_project_id"), "approval_decisions", ["video_project_id"])
    op.create_table("llm_calls", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("prompt_tokens", sa.Integer(), nullable=False), sa.Column("completion_tokens", sa.Integer(), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_llm_calls_video_project_id"), "llm_calls", ["video_project_id"])
    op.create_table("llm_cost_ledger_entries", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("cost_usd", sa.Float(), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["organization_id"],["organizations.id"]), sa.ForeignKeyConstraint(["workspace_id"],["workspaces.id"]), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_llm_cost_ledger_entries_organization_id"), "llm_cost_ledger_entries", ["organization_id"])
    op.create_index(op.f("ix_llm_cost_ledger_entries_workspace_id"), "llm_cost_ledger_entries", ["workspace_id"])
    op.create_index(op.f("ix_llm_cost_ledger_entries_video_project_id"), "llm_cost_ledger_entries", ["video_project_id"])
    op.create_table("youtube_quota_ledger_entries", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("youtube_method", sa.String(128), nullable=False), sa.Column("quota_cost", sa.Integer(), nullable=False), sa.Column("success", sa.Boolean(), nullable=False), sa.Column("retry_of_id", postgresql.UUID(as_uuid=True), nullable=True), *_base_cols(), sa.ForeignKeyConstraint(["organization_id"],["organizations.id"]), sa.ForeignKeyConstraint(["workspace_id"],["workspaces.id"]), sa.ForeignKeyConstraint(["channel_id"],["channels.id"]), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.ForeignKeyConstraint(["workflow_run_id"],["workflow_runs.id"]), sa.ForeignKeyConstraint(["retry_of_id"],["youtube_quota_ledger_entries.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_youtube_quota_ledger_entries_organization_id"), "youtube_quota_ledger_entries", ["organization_id"])
    op.create_index(op.f("ix_youtube_quota_ledger_entries_workspace_id"), "youtube_quota_ledger_entries", ["workspace_id"])
    op.create_index(op.f("ix_youtube_quota_ledger_entries_channel_id"), "youtube_quota_ledger_entries", ["channel_id"])
    op.create_index(op.f("ix_youtube_quota_ledger_entries_video_project_id"), "youtube_quota_ledger_entries", ["video_project_id"])
    op.create_index(op.f("ix_youtube_quota_ledger_entries_workflow_run_id"), "youtube_quota_ledger_entries", ["workflow_run_id"])
    op.create_table("analytics_snapshots", sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=True), sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["channel_id"],["channels.id"]), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_analytics_snapshots_channel_id"), "analytics_snapshots", ["channel_id"])
    op.create_index(op.f("ix_analytics_snapshots_video_project_id"), "analytics_snapshots", ["video_project_id"])
    op.create_table("publishing_plans", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True), sa.Column("status", publishing_plan_status_enum, nullable=False), sa.Column("youtube_video_id", sa.String(255), nullable=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column("visibility", sa.String(32), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.ForeignKeyConstraint(["channel_id"],["channels.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_publishing_plans_video_project_id"), "publishing_plans", ["video_project_id"])
    op.create_index(op.f("ix_publishing_plans_channel_id"), "publishing_plans", ["channel_id"])
    op.create_table("assets", sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("asset_type", sa.String(64), nullable=False), sa.Column("url", sa.String(1024), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["video_project_id"],["video_projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_assets_video_project_id"), "assets", ["video_project_id"])
    op.create_table("asset_licenses", sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("license_type", sa.String(128), nullable=False), sa.Column("is_valid", sa.Boolean(), nullable=False), *_base_cols(), sa.ForeignKeyConstraint(["asset_id"],["assets.id"]), sa.PrimaryKeyConstraint("id"))


def downgrade() -> None:
    for t in ["asset_licenses","assets","publishing_plans","analytics_snapshots","youtube_quota_ledger_entries","llm_cost_ledger_entries","llm_calls","approval_decisions","workflow_events","workflow_steps","workflow_runs","compliance_reports","seo_recommendations","script_drafts","video_ideas","video_projects","channels","memberships","workspaces","users","organizations"]:
        op.drop_table(t)
    bind = op.get_bind()
    for enum_t in (publishing_plan_status_enum, approval_status_enum, compliance_risk_level_enum, video_project_status_enum):
        enum_t.drop(bind, checkfirst=True)

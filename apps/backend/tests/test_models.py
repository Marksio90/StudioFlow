from app.db.base import Base
from app.db.enums import ComplianceRiskLevel, VideoProjectStatus


def test_required_tables_exist() -> None:
    expected = {
        "organizations",
        "workspaces",
        "users",
        "memberships",
        "channels",
        "video_projects",
        "video_ideas",
        "script_drafts",
        "seo_recommendations",
        "compliance_reports",
        "workflow_runs",
        "workflow_steps",
        "workflow_events",
        "approval_decisions",
        "approvals",
        "llm_calls",
        "llm_cost_ledger_entries",
        "youtube_quota_ledger_entries",
        "analytics_snapshots",
        "publishing_plans",
        "assets",
        "asset_licenses",
    }
    assert expected.issubset(Base.metadata.tables.keys())


def test_video_project_statuses() -> None:
    assert VideoProjectStatus.draft.value == "draft"
    assert VideoProjectStatus.completed.value == "completed"


def test_compliance_levels() -> None:
    assert {e.value for e in ComplianceRiskLevel} == {"low", "medium", "high", "blocked"}

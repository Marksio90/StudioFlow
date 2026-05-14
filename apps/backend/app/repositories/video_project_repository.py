from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.db.enums import ApprovalStatus, ComplianceRiskLevel, VideoProjectStatus


class InMemoryVideoProjectRepository:
    def __init__(self) -> None:
        self.projects: dict[UUID, dict] = {}
        self.workflow_runs: dict[UUID, list[dict]] = {}
        self.events: dict[UUID, list[dict]] = {}

    def list(self, limit: int, offset: int, status: VideoProjectStatus | None, channel_id: UUID | None, workspace_id: UUID | None):
        items = list(self.projects.values())
        if status:
            items = [i for i in items if i["status"] == status]
        if channel_id:
            items = [i for i in items if i["channel_id"] == channel_id]
        if workspace_id:
            items = [i for i in items if i["workspace_id"] == workspace_id]
        total = len(items)
        return items[offset : offset + limit], total

    def create(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        row = {"id": uuid4(), **payload, "status": VideoProjectStatus.draft, "created_at": now, "updated_at": now}
        self.projects[row["id"]] = row
        return row

    def get(self, project_id: UUID):
        return self.projects.get(project_id)

    def update(self, project_id: UUID, data: dict):
        row = self.projects[project_id]
        row.update({k: v for k, v in data.items() if v is not None})
        row["updated_at"] = datetime.now(timezone.utc)
        return row

    def delete(self, project_id: UUID):
        self.projects.pop(project_id, None)

    def create_workflow(self, project_id: UUID):
        run = {"id": uuid4(), "video_project_id": project_id, "state": "created"}
        self.workflow_runs.setdefault(project_id, []).append(run)
        evt = {"id": uuid4(), "workflow_run_id": run["id"], "event_type": "workflow.created", "payload": {"video_project_id": str(project_id)}}
        self.events.setdefault(project_id, []).append(evt)
        return run

    def set_approval(self, project_id: UUID, approved: bool):
        row = self.projects[project_id]
        row["status"] = VideoProjectStatus.approved if approved else VideoProjectStatus.awaiting_review
        return {"status": ApprovalStatus.approved if approved else ApprovalStatus.rejected}

    def get_events(self, project_id: UUID):
        return self.events.get(project_id, [])

    def get_costs(self, project_id: UUID):
        return {"video_project_id": project_id, "total_cost_usd": 0.0}

    def get_quota(self, project_id: UUID):
        return {"video_project_id": project_id, "units_used": 0}

    def get_compliance(self, project_id: UUID):
        return {"risk_level": ComplianceRiskLevel.low, "findings": "No checks run yet"}

    def get_analytics(self, project_id: UUID):
        return {"video_project_id": project_id, "views": 0, "watch_time": 0}

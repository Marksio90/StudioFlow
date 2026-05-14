from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.db.enums import ApprovalStatus, ComplianceRiskLevel, PublishingPlanStatus, VideoProjectStatus


class InMemoryVideoProjectRepository:
    def __init__(self) -> None:
        self.projects: dict[UUID, dict] = {}
        self.workflow_runs: dict[UUID, list[dict]] = {}
        self.workflow_steps: dict[UUID, list[dict]] = {}
        self.events: dict[UUID, list[dict]] = {}
        self.compliance_reports: dict[UUID, dict] = {}
        self.llm_calls: dict[UUID, list[dict]] = {}
        self.llm_cost_ledger_entries: dict[UUID, list[dict]] = {}
        self.youtube_quota_ledger_entries: list[dict] = []
        self.approval_decisions: dict[UUID, list[dict]] = {}
        self.analytics_snapshots: dict[UUID, list[dict]] = {}
        self.publishing_plans: dict[UUID, dict] = {}

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

    def update_project_status(self, project_id: UUID, status: VideoProjectStatus):
        return self.update(project_id, {"status": status})

    def delete(self, project_id: UUID):
        self.projects.pop(project_id, None)

    def create_workflow_run(self, video_project_id: UUID):
        run = {"id": uuid4(), "video_project_id": video_project_id, "state": "running", "created_at": datetime.now(timezone.utc)}
        self.workflow_runs.setdefault(video_project_id, []).append(run)
        return run

    def get_latest_workflow_run(self, video_project_id: UUID):
        runs = self.workflow_runs.get(video_project_id, [])
        return runs[-1] if runs else None

    def create_workflow_step(self, workflow_run_id: UUID, video_project_id: UUID, step_name: str, status: str, attempt: int, idempotency_key: str, input_json: dict):
        step = {
            "id": uuid4(),
            "workflow_run_id": workflow_run_id,
            "video_project_id": video_project_id,
            "step_name": step_name,
            "status": status,
            "idempotency_key": idempotency_key,
            "attempt": attempt,
            "input_json": input_json,
            "output_json": {},
            "error_message": None,
            "started_at": None,
            "finished_at": None,
        }
        self.workflow_steps.setdefault(video_project_id, []).append(step)
        return step

    def append_event(self, video_project_id: UUID, event: dict):
        self.events.setdefault(video_project_id, []).append(event)

    def get_events(self, project_id: UUID):
        return self.events.get(project_id, [])

    def log_llm_call(self, project_id: UUID, call: dict):
        self.llm_calls.setdefault(project_id, []).append(call)

    def log_llm_cost_entry(self, project_id: UUID, entry: dict):
        self.llm_cost_ledger_entries.setdefault(project_id, []).append(entry)

    def get_costs(self, project_id: UUID):
        total = sum(item.get("cost_usd", 0.0) for item in self.llm_cost_ledger_entries.get(project_id, []))
        return {"video_project_id": project_id, "total_cost_usd": round(total, 8)}

    def log_youtube_quota_entry(self, entry: dict):
        self.youtube_quota_ledger_entries.append(entry)
        return entry

    def get_quota(self, project_id: UUID):
        project = self.get(project_id)
        if not project:
            return {"video_project_id": project_id, "project_quota_cost": 0, "channel_quota_cost": 0}

        project_total = sum(item.get("quota_cost", 0) for item in self.youtube_quota_ledger_entries if item.get("video_project_id") == project_id)
        channel_total = sum(item.get("quota_cost", 0) for item in self.youtube_quota_ledger_entries if item.get("channel_id") == project.get("channel_id"))
        return {"video_project_id": project_id, "channel_id": project.get("channel_id"), "project_quota_cost": project_total, "channel_quota_cost": channel_total}

    def get_compliance(self, project_id: UUID):
        return self.compliance_reports.get(
            project_id,
            {
                "video_project_id": project_id,
                "score": 100,
                "risk_level": ComplianceRiskLevel.low,
                "requires_ai_disclosure": False,
                "disclosure_decision_missing": False,
                "ai_disclosure_risk": "low",
                "inauthentic_content_risk": "low",
                "repetitive_content_risk": "low",
                "copyright_risk": "low",
                "sensitive_claims_risk": "low",
                "clickbait_risk": "low",
                "asset_license_risk": "low",
                "synthetic_media_realism_risk": "low",
                "reasons": [],
                "recommendations": [],
                "blocking_issues": [],
            },
        )

    def save_compliance_report(self, project_id: UUID, report: dict):
        self.compliance_reports[project_id] = report
        return report

    def create_analytics_snapshot(self, payload: dict):
        now = datetime.now(timezone.utc)
        row = {"id": uuid4(), **payload, "created_at": now, "updated_at": now}
        self.analytics_snapshots.setdefault(payload["video_project_id"], []).append(row)
        return row

    def get_analytics(self, project_id: UUID):
        return self.analytics_snapshots.get(project_id, [])

    def add_approval_decision(self, project_id: UUID, status: ApprovalStatus, comment: str | None, decided_by_user_id: UUID):
        decision = {
            "id": uuid4(),
            "video_project_id": project_id,
            "status": status.value,
            "comment": comment,
            "decided_by_user_id": decided_by_user_id,
            "created_at": datetime.now(timezone.utc),
        }
        self.approval_decisions.setdefault(project_id, []).append(decision)
        return decision

    def get_approval_decisions(self, project_id: UUID):
        return self.approval_decisions.get(project_id, [])

    def create_publishing_plan(self, payload: dict):
        now = datetime.now(timezone.utc)
        row = {
            "id": uuid4(),
            **payload,
            "status": PublishingPlanStatus.draft,
            "youtube_video_id": None,
            "scheduled_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self.publishing_plans[row["id"]] = row
        return row

    def get_publishing_plan(self, plan_id: UUID):
        return self.publishing_plans.get(plan_id)

    def update_publishing_plan(self, plan_id: UUID, data: dict):
        row = self.publishing_plans[plan_id]
        row.update({k: v for k, v in data.items() if v is not None})
        row["updated_at"] = datetime.now(timezone.utc)
        return row

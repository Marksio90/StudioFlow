from datetime import datetime, timezone
from uuid import uuid4

from app.db.enums import VideoProjectStatus
from app.services.compliance_service import ComplianceService
from app.services.workflow_events import WorkflowEventEmitter

STEP_SEQUENCE = [
    "create_video_project",
    "generate_research",
    "generate_script",
    "generate_seo",
    "run_compliance_check",
    "request_human_approval",
    "wait_for_approval",
    "schedule_or_publish",
    "sync_analytics",
]


class WorkflowEngine:
    def __init__(self, repo):
        self.repo = repo
        self.events = WorkflowEventEmitter(repo)
        self.compliance = ComplianceService()

    def start(self, video_project_id):
        run = self.repo.create_workflow_run(video_project_id)
        self.events.emit(video_project_id, run["id"], "workflow.created", {"run_id": str(run["id"])})
        for idx, name in enumerate(STEP_SEQUENCE):
            status = "waiting_for_approval" if name == "wait_for_approval" else "pending"
            step = self.repo.create_workflow_step(
                workflow_run_id=run["id"],
                video_project_id=video_project_id,
                step_name=name,
                status=status,
                attempt=0,
                idempotency_key=f"{video_project_id}:{name}",
                input_json={},
            )
            self.events.emit(video_project_id, run["id"], "workflow.step_created", {"step_id": str(step["id"]), "step_name": name})
            if name == "wait_for_approval":
                self.repo.update_project_status(video_project_id, VideoProjectStatus.awaiting_review)
                self.events.emit(video_project_id, run["id"], "workflow.waiting_for_approval", {})
                break
        return run

    def approve(self, video_project_id):
        run = self.repo.get_latest_workflow_run(video_project_id)
        report = self.repo.get_compliance(video_project_id)
        if report.get("risk_level") == "blocked" or report.get("blocking_issues"):
            self.events.emit(video_project_id, run["id"], "workflow.approval_blocked", {"blocking_issues": report.get("blocking_issues", [])})
            return {"status": "blocked", "blocking_issues": report.get("blocking_issues", [])}
        self.repo.update_project_status(video_project_id, VideoProjectStatus.approved)
        self.events.emit(video_project_id, run["id"], "workflow.approved", {})
        return {"status": "approved"}

    def reject(self, video_project_id):
        run = self.repo.get_latest_workflow_run(video_project_id)
        self.repo.update_project_status(video_project_id, VideoProjectStatus.failed)
        self.events.emit(video_project_id, run["id"], "workflow.rejected", {"state": "needs_changes"})
        return {"status": "needs_changes"}

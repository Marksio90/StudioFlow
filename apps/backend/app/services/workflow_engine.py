from uuid import UUID

from app.db.enums import ApprovalStatus, VideoProjectStatus
from app.services.compliance_service import ComplianceService
from app.services.workflow_events import WorkflowEventEmitter

STEP_SEQUENCE = ["create_video_project", "generate_research", "generate_script", "generate_seo", "run_compliance_check", "request_human_approval", "wait_for_approval", "schedule_or_publish", "sync_analytics"]


class WorkflowEngine:
    def __init__(self, repo):
        self.repo = repo
        self.events = WorkflowEventEmitter(repo)
        self.compliance = ComplianceService()

    async def start(self, video_project_id: UUID):
        run = await self.repo.create_workflow_run(video_project_id)
        await self.events.emit(video_project_id, run["id"], "workflow.created", {"run_id": str(run["id"])})
        for name in STEP_SEQUENCE:
            status = "waiting_for_approval" if name == "wait_for_approval" else "pending"
            step = await self.repo.create_workflow_step(run["id"], video_project_id, name, status, 0, f"{video_project_id}:{name}", {})
            await self.events.emit(video_project_id, run["id"], "workflow.step_created", {"step_id": str(step["id"]), "step_name": name})
            if name == "wait_for_approval":
                await self.repo.update_project_status(video_project_id, VideoProjectStatus.awaiting_review)
                await self.events.emit(video_project_id, run["id"], "workflow.waiting_for_approval", {})
                break
        return run

    async def approve(self, video_project_id: UUID, comment: str | None, decided_by_user_id: UUID) -> dict:
        compliance = await self.repo.get_compliance(video_project_id)
        blocking = compliance.get("blocking_issues", [])
        if blocking:
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail=f"Cannot approve: compliance blocking issues present: {blocking}")
        await self.repo.add_approval_decision(video_project_id, ApprovalStatus.approved, comment, decided_by_user_id)
        project = await self.repo.update_project_status(video_project_id, VideoProjectStatus.approved)
        run = await self.repo.get_latest_workflow_run(video_project_id)
        if run:
            await self.events.emit(video_project_id, run["id"], "workflow.approved", {"comment": comment, "decided_by": str(decided_by_user_id)})
        return project

    async def reject(self, video_project_id: UUID, comment: str | None, decided_by_user_id: UUID) -> dict:
        await self.repo.add_approval_decision(video_project_id, ApprovalStatus.rejected, comment, decided_by_user_id)
        project = await self.repo.update_project_status(video_project_id, VideoProjectStatus.rejected)
        run = await self.repo.get_latest_workflow_run(video_project_id)
        if run:
            await self.events.emit(video_project_id, run["id"], "workflow.rejected", {"comment": comment, "decided_by": str(decided_by_user_id)})
        return project

    async def needs_changes(self, video_project_id: UUID, comment: str | None, decided_by_user_id: UUID) -> dict:
        await self.repo.add_approval_decision(video_project_id, ApprovalStatus.needs_changes, comment, decided_by_user_id)
        project = await self.repo.update_project_status(video_project_id, VideoProjectStatus.needs_changes)
        run = await self.repo.get_latest_workflow_run(video_project_id)
        if run:
            await self.events.emit(video_project_id, run["id"], "workflow.needs_changes", {"comment": comment, "decided_by": str(decided_by_user_id)})
        return project

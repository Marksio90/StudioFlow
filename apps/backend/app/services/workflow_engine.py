from app.db.enums import ApprovalStatus, VideoProjectStatus
from app.services.compliance_service import ComplianceService
from app.services.workflow_events import WorkflowEventEmitter

STEP_SEQUENCE = ["create_video_project","generate_research","generate_script","generate_seo","run_compliance_check","request_human_approval","wait_for_approval","schedule_or_publish","sync_analytics"]


class WorkflowEngine:
    def __init__(self, repo):
        self.repo = repo
        self.events = WorkflowEventEmitter(repo)
        self.compliance = ComplianceService()

    async def start(self, video_project_id):
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

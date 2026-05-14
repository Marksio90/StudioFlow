from uuid import UUID

from app.db.enums import ApprovalStatus, ComplianceRiskLevel, PublishingPlanStatus, VideoProjectStatus
from app.schemas.video_project import VideoProjectCreate, VideoProjectUpdate
from app.services.analytics_service import AnalyticsService
from app.services.compliance_service import ComplianceInput, ComplianceService
from app.services.workflow_engine import WorkflowEngine
from app.services.youtube_quota_service import YouTubeCallContext, YouTubeQuotaService
from app.services.usage_service import UsageService
from app.observability import metrics

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000000")


class VideoProjectService:
    def __init__(self, repo: object, usage_service: UsageService | None = None):
        self.repo = repo
        self.engine = WorkflowEngine(repo)
        self.compliance_service = ComplianceService()
        self.analytics_service = AnalyticsService(repo)
        self.quota_service = YouTubeQuotaService(repo)
        self.usage_service = usage_service or UsageService(repo)

    async def list_projects(self, limit: int, offset: int, status: VideoProjectStatus | None, channel_id: UUID | None, workspace_id: UUID | None):
        return await self.repo.list(limit=limit, offset=offset, status=status, channel_id=channel_id, workspace_id=workspace_id)

    async def create_project(self, payload: VideoProjectCreate):
        await self.usage_service.assert_can_create_project(payload.organization_id)
        await self.repo.register_channel(payload.organization_id, payload.channel_id)
        return await self.repo.create(payload.model_dump())

    async def get_project(self, project_id: UUID):
        return await self.repo.get(project_id)

    async def update_project(self, project_id: UUID, payload: VideoProjectUpdate):
        return await self.repo.update(project_id, payload.model_dump(exclude_unset=True))

    async def delete_project(self, project_id: UUID):
        return await self.repo.delete(project_id)

    async def start_workflow(self, project_id: UUID):
        started = await self.engine.start(project_id)
        metrics.observe("cycle_time", 0.0)
        return started

    async def request_approval(self, project_id: UUID):
        await self.repo.add_approval_decision(project_id, status=ApprovalStatus.awaiting_review, comment="Approval requested", decided_by_user_id=SYSTEM_USER_ID)
        return await self.repo.update(project_id, {"status": VideoProjectStatus.awaiting_review})

    async def approve(self, project_id: UUID, comment: str | None, decided_by_user_id: UUID):
        metrics.observe("approval_latency", 0.0)
        return await self.engine.approve(project_id, comment, decided_by_user_id)

    async def reject(self, project_id: UUID, comment: str | None, decided_by_user_id: UUID):
        return await self.engine.reject(project_id, comment, decided_by_user_id)

    async def needs_changes(self, project_id: UUID, comment: str | None, decided_by_user_id: UUID):
        metrics.inc("rework_rate", 1)
        return await self.engine.needs_changes(project_id, comment, decided_by_user_id)

    async def get_events(self, project_id: UUID):
        return await self.repo.get_events(project_id)

    async def get_approval_decisions(self, project_id: UUID):
        return await self.repo.get_approval_decisions(project_id)

    async def get_costs(self, project_id: UUID):
        return await self.repo.get_costs(project_id)

    async def get_quota(self, project_id: UUID):
        return await self.repo.get_quota(project_id)

    async def get_compliance(self, project_id: UUID):
        return await self.repo.get_compliance(project_id)

    async def run_compliance(self, project_id: UUID, metadata: dict | None = None, disclosure_decision_missing: bool = False):
        report = self.compliance_service.evaluate(
            ComplianceInput(
                video_project_id=project_id,
                metadata=metadata or {},
                disclosure_decision_missing=disclosure_decision_missing,
            )
        )
        return await self.repo.save_compliance_report(project_id, report.model_dump())

    async def get_analytics(self, project_id: UUID):
        return await self.analytics_service.list_project_analytics(project_id)

    async def create_analytics_snapshot(self, project_id: UUID, payload: dict):
        return await self.analytics_service.save_snapshot(project_id, payload)

    async def create_publishing_plan(self, payload: dict):
        return await self.repo.create_publishing_plan(payload)

    async def schedule_publishing(self, plan_id: UUID, scheduled_at):
        plan = await self.repo.get_publishing_plan(plan_id)
        project_id = plan["video_project_id"]
        decisions = await self.repo.get_approval_decisions(project_id)
        latest_status = decisions[-1]["status"] if decisions else ApprovalStatus.awaiting_review.value
        if latest_status != ApprovalStatus.approved.value:
            raise ValueError("Project is not approved")
        compliance = await self.repo.get_compliance(project_id)
        if compliance["risk_level"] == ComplianceRiskLevel.blocked:
            raise ValueError("Project is compliance blocked")
        return await self.repo.update_publishing_plan(plan_id, {"scheduled_at": scheduled_at, "status": PublishingPlanStatus.scheduled})

    async def publish_video(self, plan_id: UUID):
        plan = await self.repo.get_publishing_plan(plan_id)
        if plan["status"] != PublishingPlanStatus.scheduled:
            raise ValueError("Plan is not scheduled")
        decisions = await self.repo.get_approval_decisions(plan["video_project_id"])
        latest_status = decisions[-1]["status"] if decisions else ApprovalStatus.awaiting_review.value
        if latest_status != ApprovalStatus.approved.value:
            raise ValueError("Project is not approved")
        compliance = await self.repo.get_compliance(plan["video_project_id"])
        if compliance["risk_level"] == ComplianceRiskLevel.blocked:
            raise ValueError("Project is compliance blocked")
        await self.repo.update_publishing_plan(plan_id, {"status": PublishingPlanStatus.uploading})
        metrics.inc("quota_usage", 1)
        await self.quota_service.log_call(
            YouTubeCallContext(
                organization_id=(await self.repo.get(plan["video_project_id"]))["organization_id"],
                workspace_id=(await self.repo.get(plan["video_project_id"]))["workspace_id"],
                channel_id=plan["channel_id"],
                video_project_id=plan["video_project_id"],
            ),
            youtube_method="videos.insert",
            success=True,
        )
        published = await self.repo.update_publishing_plan(plan_id, {"status": PublishingPlanStatus.published, "youtube_video_id": f"yt_{plan_id.hex[:10]}"})
        metrics.inc("llm_cost_usd", 0.0)
        return published

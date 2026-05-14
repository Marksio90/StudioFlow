from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ApprovalStatus, ComplianceRiskLevel, PublishingPlanStatus, VideoProjectStatus
from app.db.models import ApprovalDecision, AnalyticsSnapshot, Channel, ComplianceReport, LLMCostLedgerEntry, Membership, Organization, PublishingPlan, TaskAttempt, TaskExecution, VideoProject, WorkflowEvent, WorkflowRun, WorkflowStep, YouTubeQuotaLedgerEntry


class DBVideoProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, limit: int, offset: int, status: VideoProjectStatus | None, channel_id: UUID | None, workspace_id: UUID | None):
        stmt = select(VideoProject)
        if status:
            stmt = stmt.where(VideoProject.status == status)
        if channel_id:
            stmt = stmt.where(VideoProject.channel_id == channel_id)
        if workspace_id:
            stmt = stmt.where(VideoProject.workspace_id == workspace_id)
        total = await self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = (await self.session.scalars(stmt.offset(offset).limit(limit))).all()
        return [self._project_to_dict(r) for r in rows], int(total or 0)

    async def create(self, payload: dict) -> dict:
        row = VideoProject(**payload, status=VideoProjectStatus.draft)
        self.session.add(row)
        await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return self._project_to_dict(row)

    def _project_to_dict(self, row: VideoProject):
        return {"id": row.id, "organization_id": row.organization_id, "workspace_id": row.workspace_id, "channel_id": row.channel_id, "title": row.title, "status": row.status, "created_at": row.created_at, "updated_at": row.updated_at}

    async def get(self, project_id: UUID):
        row = await self.session.get(VideoProject, project_id)
        return self._project_to_dict(row) if row else None

    async def update(self, project_id: UUID, data: dict):
        row = await self.session.get(VideoProject, project_id)
        for k, v in data.items():
            if v is not None:
                setattr(row, k, v)
        await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return self._project_to_dict(row)

    async def update_project_status(self, project_id: UUID, status: VideoProjectStatus): return await self.update(project_id, {"status": status})
    async def delete(self, project_id: UUID): await self.session.execute(VideoProject.__table__.delete().where(VideoProject.id == project_id)); await self.session.commit()
    async def create_workflow_run(self, video_project_id: UUID):
        row = WorkflowRun(video_project_id=video_project_id, state="running")
        self.session.add(row); await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return {"id": row.id, "video_project_id": row.video_project_id, "state": row.state, "created_at": row.created_at}
    async def get_latest_workflow_run(self, video_project_id: UUID):
        row = (await self.session.scalars(select(WorkflowRun).where(WorkflowRun.video_project_id == video_project_id).order_by(WorkflowRun.created_at.desc(), WorkflowRun.id.desc()))).first()
        return {"id": row.id} if row else None
    async def create_workflow_step(self, workflow_run_id: UUID, video_project_id: UUID, step_name: str, status: str, attempt: int, idempotency_key: str, input_json: dict):
        row = WorkflowStep(workflow_run_id=workflow_run_id, step_name=step_name, state=status)
        self.session.add(row); await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return {"id": row.id, "step_name": row.step_name, "status": row.state}
    async def append_event(self, video_project_id: UUID, event: dict):
        run = await self.get_latest_workflow_run(video_project_id)
        workflow_run_id = run["id"] if run else None
        if workflow_run_id:
            self.session.add(WorkflowEvent(workflow_run_id=workflow_run_id, correlation_id=event.get("correlation_id"), event_type=event["event_type"], payload=event["payload"]))
            await self.session.commit()
    async def get_or_create_task_execution(self, task_name: str, business_key: str, idempotency_key: str, workflow_run_id: UUID | None = None):
        existing = (await self.session.scalars(select(TaskExecution).where(TaskExecution.business_key == business_key))).first()
        if existing:
            return existing
        row = TaskExecution(workflow_run_id=workflow_run_id, task_name=task_name, business_key=business_key, idempotency_key=idempotency_key, status="pending", retry_count=0)
        self.session.add(row); await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return row
    async def mark_task_execution(self, execution_id: UUID, status: str, retry_count: int, error_code: str | None = None):
        row = await self.session.get(TaskExecution, execution_id)
        row.status = status; row.retry_count = retry_count; row.error_code = error_code
        await self.session.commit(); await self.session.refresh(row)
        return row
    async def add_task_attempt(self, execution_id: UUID, attempt_no: int, status: str, error_code: str | None = None):
        row = TaskAttempt(task_execution_id=execution_id, attempt_no=attempt_no, status=status, error_code=error_code)
        self.session.add(row); await self.session.commit()
        return row
    async def get_events(self, project_id: UUID):
        stmt = (
            select(WorkflowEvent)
            .join(WorkflowRun, WorkflowRun.id == WorkflowEvent.workflow_run_id)
            .where(WorkflowRun.video_project_id == project_id)
            .order_by(WorkflowEvent.created_at.asc(), WorkflowEvent.id.asc())
        )
        rows = (await self.session.scalars(stmt)).all()
        return [{"id": r.id, "workflow_run_id": r.workflow_run_id, "event_type": r.event_type, "payload": r.payload, "created_at": r.created_at} for r in rows]
    async def log_llm_call(self, project_id: UUID, call: dict): return None
    async def log_llm_cost_entry(self, project_id: UUID, entry: dict):
        p = await self.get(project_id)
        self.session.add(LLMCostLedgerEntry(organization_id=p["organization_id"], workspace_id=p["workspace_id"], video_project_id=project_id, cost_usd=entry.get("cost_usd",0.0)))
        await self.session.commit()
    async def get_costs(self, project_id: UUID):
        total = await self.session.scalar(select(func.coalesce(func.sum(LLMCostLedgerEntry.cost_usd),0.0)).where(LLMCostLedgerEntry.video_project_id==project_id))
        return {"video_project_id": project_id, "total_cost_usd": round(float(total), 8)}
    async def log_youtube_quota_entry(self, entry: dict): self.session.add(YouTubeQuotaLedgerEntry(**entry)); await self.session.commit(); return entry
    async def get_quota(self, project_id: UUID):
        project = await self.get(project_id)
        project_total = await self.session.scalar(select(func.coalesce(func.sum(YouTubeQuotaLedgerEntry.quota_cost), 0)).where(YouTubeQuotaLedgerEntry.video_project_id == project_id))
        channel_total = await self.session.scalar(select(func.coalesce(func.sum(YouTubeQuotaLedgerEntry.quota_cost), 0)).where(YouTubeQuotaLedgerEntry.channel_id == project["channel_id"])) if project else 0
        return {"video_project_id": project_id, "project_quota_cost": int(project_total or 0), "channel_quota_cost": int(channel_total or 0)}
    async def get_compliance(self, project_id: UUID):
        row = (await self.session.scalars(select(ComplianceReport).where(ComplianceReport.video_project_id==project_id).order_by(ComplianceReport.created_at.desc()))).first()
        if row:
            payload = json.loads(row.findings) if row.findings else {}
            return {"video_project_id": project_id, **payload, "risk_level": row.risk_level}
        return {"video_project_id":project_id,"score":100,"risk_level":ComplianceRiskLevel.low,"requires_ai_disclosure":False,"disclosure_decision_missing":False,"ai_disclosure_risk":"low","inauthentic_content_risk":"low","repetitive_content_risk":"low","copyright_risk":"low","sensitive_claims_risk":"low","clickbait_risk":"low","asset_license_risk":"low","synthetic_media_realism_risk":"low","reasons":[],"recommendations":[],"blocking_issues":[]}
    async def save_compliance_report(self, project_id: UUID, report: dict):
        row = ComplianceReport(video_project_id=project_id, risk_level=report.get("risk_level", ComplianceRiskLevel.low), findings=json.dumps(report, default=str))
        self.session.add(row); await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return report
    async def create_analytics_snapshot(self, payload: dict):
        row = AnalyticsSnapshot(**payload)
        self.session.add(row)
        await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return {"id": row.id, "video_project_id": row.video_project_id, "channel_id": row.channel_id, "youtube_video_id": row.payload["youtube_video_id"], "views": row.payload["views"], "watch_time_minutes": row.payload["watch_time_minutes"], "average_view_duration": row.payload["average_view_duration"], "ctr": row.payload["ctr"], "likes": row.payload["likes"], "comments": row.payload["comments"], "subscribers_gained": row.payload["subscribers_gained"], "estimated_revenue": row.payload["estimated_revenue"], "snapshot_at": row.payload["snapshot_at"], "created_at": row.created_at, "updated_at": row.updated_at}
    async def get_analytics(self, project_id: UUID):
        rows = (await self.session.scalars(select(AnalyticsSnapshot).where(AnalyticsSnapshot.video_project_id == project_id).order_by(AnalyticsSnapshot.created_at.asc(), AnalyticsSnapshot.id.asc()))).all()
        return [{"id": r.id, "video_project_id": r.video_project_id, "channel_id": r.channel_id, "youtube_video_id": r.payload["youtube_video_id"], "views": r.payload["views"], "watch_time_minutes": r.payload["watch_time_minutes"], "average_view_duration": r.payload["average_view_duration"], "ctr": r.payload["ctr"], "likes": r.payload["likes"], "comments": r.payload["comments"], "subscribers_gained": r.payload["subscribers_gained"], "estimated_revenue": r.payload["estimated_revenue"], "snapshot_at": r.payload["snapshot_at"], "created_at": r.created_at, "updated_at": r.updated_at} for r in rows]
    async def add_approval_decision(self, project_id: UUID, status: ApprovalStatus, comment: str | None, decided_by_user_id: UUID):
        row = ApprovalDecision(video_project_id=project_id,status=status,comment=comment,decided_by_user_id=decided_by_user_id)
        self.session.add(row); await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return {"status": status.value, "comment": comment}
    async def get_approval_decisions(self, project_id: UUID):
        rows = (await self.session.scalars(select(ApprovalDecision).where(ApprovalDecision.video_project_id == project_id).order_by(ApprovalDecision.created_at.asc(), ApprovalDecision.id.asc()))).all()
        return [{"id": r.id, "video_project_id": r.video_project_id, "status": r.status.value, "comment": r.comment, "decided_by_user_id": r.decided_by_user_id, "created_at": r.created_at} for r in rows]
    async def create_publishing_plan(self, payload: dict):
        row = PublishingPlan(**payload, status=PublishingPlanStatus.draft)
        self.session.add(row)
        await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return self._publishing_plan_to_dict(row)
    async def get_publishing_plan(self, plan_id: UUID):
        row = await self.session.get(PublishingPlan, plan_id)
        return self._publishing_plan_to_dict(row) if row else None
    async def update_publishing_plan(self, plan_id: UUID, data: dict):
        row = await self.session.get(PublishingPlan, plan_id)
        for k, v in data.items():
            if v is not None:
                setattr(row, k, v)
        await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return self._publishing_plan_to_dict(row)

    def _publishing_plan_to_dict(self, row: PublishingPlan):
        return {"id": row.id, "video_project_id": row.video_project_id, "channel_id": row.channel_id, "scheduled_at": row.scheduled_at, "status": row.status, "youtube_video_id": row.youtube_video_id, "title": row.title, "description": row.description, "tags": row.tags, "visibility": row.visibility, "created_at": row.created_at, "updated_at": row.updated_at}
    async def set_plan(self, organization_id: UUID, plan_code: str):
        org = await self.session.get(Organization, organization_id)
        if org:
            org.plan_code = plan_code
            await self.session.commit()
    async def get_plan(self, organization_id: UUID) -> str:
        org = await self.session.get(Organization, organization_id)
        return getattr(org, "plan_code", None) or "starter"
    async def register_channel(self, organization_id: UUID, channel_id: UUID): return None
    async def register_user(self, organization_id: UUID, user_id: UUID): return None
    async def get_monthly_usage(self, organization_id: UUID, month_start):
        projects = await self.session.scalar(select(func.count()).select_from(VideoProject).where(VideoProject.organization_id==organization_id))
        channels = await self.session.scalar(select(func.count()).select_from(Channel).where(Channel.organization_id==organization_id))
        users = await self.session.scalar(select(func.count(func.distinct(Membership.user_id))).select_from(Membership).where(Membership.organization_id==organization_id))
        ai_cost = await self.session.scalar(select(func.coalesce(func.sum(LLMCostLedgerEntry.cost_usd),0.0)).where(LLMCostLedgerEntry.organization_id==organization_id))
        quota = await self.session.scalar(select(func.coalesce(func.sum(YouTubeQuotaLedgerEntry.quota_cost),0)).where(YouTubeQuotaLedgerEntry.organization_id==organization_id))
        return {"projects":int(projects or 0),"channels":int(channels or 0),"ai_cost_usd":float(ai_cost or 0.0),"youtube_quota":int(quota or 0),"users":int(users or 0)}
    async def create_monthly_usage_snapshot(self, payload: dict): return payload

InMemoryVideoProjectRepository = DBVideoProjectRepository

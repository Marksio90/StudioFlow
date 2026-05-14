from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ApprovalStatus, ComplianceRiskLevel, PublishingPlanStatus, VideoProjectStatus
from app.db.models import ApprovalDecision, AnalyticsSnapshot, PublishingPlan, VideoProject, WorkflowEvent, WorkflowRun, WorkflowStep, YouTubeQuotaLedgerEntry, LLMCostLedgerEntry


class DBVideoProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.compliance_reports: dict[UUID, dict] = {}
        self.organization_plans: dict[UUID, str] = {}
        self.organization_channels: dict[UUID, set[UUID]] = {}
        self.organization_users: dict[UUID, set[UUID]] = {}

    def _run(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def list(self, limit: int, offset: int, status: VideoProjectStatus | None, channel_id: UUID | None, workspace_id: UUID | None):
        async def _q():
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
        return self._run(_q())

    def create(self, payload: dict) -> dict:
        async def _q():
            row = VideoProject(**payload, status=VideoProjectStatus.draft)
            self.session.add(row)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(row)
            return self._project_to_dict(row)
        return self._run(_q())

    def _project_to_dict(self, row: VideoProject):
        return {"id": row.id, "organization_id": row.organization_id, "workspace_id": row.workspace_id, "channel_id": row.channel_id, "title": row.title, "status": row.status, "created_at": row.created_at, "updated_at": row.updated_at}

    def get(self, project_id: UUID):
        async def _q():
            row = await self.session.get(VideoProject, project_id)
            return self._project_to_dict(row) if row else None
        return self._run(_q())

    def update(self, project_id: UUID, data: dict):
        async def _q():
            row = await self.session.get(VideoProject, project_id)
            for k, v in data.items():
                if v is not None:
                    setattr(row, k, v)
            await self.session.commit()
            await self.session.refresh(row)
            return self._project_to_dict(row)
        return self._run(_q())

    def update_project_status(self, project_id: UUID, status: VideoProjectStatus): return self.update(project_id, {"status": status})
    def delete(self, project_id: UUID): self._run(self.session.execute(VideoProject.__table__.delete().where(VideoProject.id == project_id))); self._run(self.session.commit())
    def create_workflow_run(self, video_project_id: UUID):
        async def _q():
            row = WorkflowRun(video_project_id=video_project_id, state="running")
            self.session.add(row); await self.session.commit(); await self.session.refresh(row)
            return {"id": row.id, "video_project_id": row.video_project_id, "state": row.state, "created_at": row.created_at}
        return self._run(_q())
    def get_latest_workflow_run(self, video_project_id: UUID):
        async def _q():
            row = (await self.session.scalars(select(WorkflowRun).where(WorkflowRun.video_project_id == video_project_id).order_by(WorkflowRun.created_at.desc()))).first()
            return {"id": row.id} if row else None
        return self._run(_q())
    def create_workflow_step(self, workflow_run_id: UUID, video_project_id: UUID, step_name: str, status: str, attempt: int, idempotency_key: str, input_json: dict):
        async def _q():
            row = WorkflowStep(workflow_run_id=workflow_run_id, step_name=step_name, state=status)
            self.session.add(row); await self.session.commit(); await self.session.refresh(row)
            return {"id": row.id, "step_name": row.step_name, "status": row.state}
        return self._run(_q())
    def append_event(self, video_project_id: UUID, event: dict):
        async def _q():
            run = self.get_latest_workflow_run(video_project_id)
            workflow_run_id = run["id"] if run else None
            if workflow_run_id:
                self.session.add(WorkflowEvent(workflow_run_id=workflow_run_id, event_type=event["event_type"], payload=event["payload"]))
                await self.session.commit()
        return self._run(_q())
    def get_events(self, project_id: UUID): return []
    def log_llm_call(self, project_id: UUID, call: dict): return None
    def log_llm_cost_entry(self, project_id: UUID, entry: dict):
        async def _q():
            p = self.get(project_id)
            self.session.add(LLMCostLedgerEntry(organization_id=p["organization_id"], workspace_id=p["workspace_id"], video_project_id=project_id, cost_usd=entry.get("cost_usd",0.0)))
            await self.session.commit()
        return self._run(_q())
    def get_costs(self, project_id: UUID):
        async def _q():
            total = await self.session.scalar(select(func.coalesce(func.sum(LLMCostLedgerEntry.cost_usd),0.0)).where(LLMCostLedgerEntry.video_project_id==project_id))
            return {"video_project_id": project_id, "total_cost_usd": round(float(total), 8)}
        return self._run(_q())
    def log_youtube_quota_entry(self, entry: dict): self._run(self._log_quota(entry)); return entry
    async def _log_quota(self, entry): self.session.add(YouTubeQuotaLedgerEntry(**entry)); await self.session.commit()
    def get_quota(self, project_id: UUID): return {"video_project_id": project_id, "project_quota_cost": 0, "channel_quota_cost": 0}
    def get_compliance(self, project_id: UUID): return self.compliance_reports.get(project_id,{"video_project_id":project_id,"score":100,"risk_level":ComplianceRiskLevel.low,"requires_ai_disclosure":False,"disclosure_decision_missing":False,"ai_disclosure_risk":"low","inauthentic_content_risk":"low","repetitive_content_risk":"low","copyright_risk":"low","sensitive_claims_risk":"low","clickbait_risk":"low","asset_license_risk":"low","synthetic_media_realism_risk":"low","reasons":[],"recommendations":[],"blocking_issues":[]})
    def save_compliance_report(self, project_id: UUID, report: dict): self.compliance_reports[project_id]=report; return report
    def create_analytics_snapshot(self, payload: dict): return payload
    def get_analytics(self, project_id: UUID): return []
    def add_approval_decision(self, project_id: UUID, status: ApprovalStatus, comment: str | None, decided_by_user_id: UUID): return {"status": status.value, "comment": comment}
    def get_approval_decisions(self, project_id: UUID): return []
    def create_publishing_plan(self, payload: dict): return {"id": uuid4(), **payload, "status": PublishingPlanStatus.draft}
    def get_publishing_plan(self, plan_id: UUID): return None
    def update_publishing_plan(self, plan_id: UUID, data: dict): return {"id": plan_id, **data}
    def set_plan(self, organization_id: UUID, plan_code: str): self.organization_plans[organization_id]=plan_code
    def get_plan(self, organization_id: UUID) -> str: return self.organization_plans.get(organization_id,"starter")
    def register_channel(self, organization_id: UUID, channel_id: UUID): self.organization_channels.setdefault(organization_id,set()).add(channel_id)
    def register_user(self, organization_id: UUID, user_id: UUID): self.organization_users.setdefault(organization_id,set()).add(user_id)
    def get_monthly_usage(self, organization_id: UUID, month_start): return {"projects":0,"channels":0,"ai_cost_usd":0.0,"youtube_quota":0,"users":0}
    def create_monthly_usage_snapshot(self, payload: dict): return payload

InMemoryVideoProjectRepository = DBVideoProjectRepository

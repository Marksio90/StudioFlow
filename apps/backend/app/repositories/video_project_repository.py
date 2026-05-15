from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import ApprovalStatus, ComplianceRiskLevel, PublishingPlanStatus, VideoProjectStatus
from app.db.models import ApprovalDecision, AnalyticsSnapshot, Angle, AudioBrief, Channel, ChannelMemory, ComplianceReport, HookVariant, LLMCostLedgerEntry, Membership, MonetizationPlan, Organization, PublishingPlan, ResearchBrief, RetentionReview, TaskAttempt, TaskExecution, ThumbnailConcept, TitleVariant, VideoProject, VisualPlan, VisualScene, WorkflowEvent, WorkflowRun, WorkflowStep, YouTubeQuotaLedgerEntry




def _default_compliance(project_id: UUID) -> dict:
    return {
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
    }
def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryVideoProjectRepository:
    """Standalone in-memory repository for unit tests that run without a real database."""

    def __init__(self) -> None:
        self._projects: dict[UUID, dict] = {}
        self._channels: dict[str, dict] = {}  # key: "{org_id}:{channel_id}"
        self._plans: dict[UUID, str] = {}
        self._approval_decisions: dict[UUID, list[dict]] = {}
        self._compliance_reports: dict[UUID, dict] = {}
        self._analytics: dict[UUID, list[dict]] = {}
        self._publishing_plans: dict[UUID, dict] = {}
        self._entity_rows: dict[str, list[dict]] = {}
        self._workflow_runs: dict[UUID, list[dict]] = {}
        self._events: dict[UUID, list[dict]] = {}
        self._task_executions: dict[str, object] = {}
        self._llm_costs: dict[UUID, list[float]] = {}
        self.youtube_quota_ledger_entries: list[dict] = []

    # ── Plan management ───────────────────────────────────────────────────────

    def set_plan(self, organization_id: UUID, plan_code: str) -> None:
        self._plans[organization_id] = plan_code

    async def get_plan(self, organization_id: UUID) -> str:
        return self._plans.get(organization_id, "starter")

    # ── Projects ──────────────────────────────────────────────────────────────

    async def create(self, payload: dict) -> dict:
        project = {"id": _uuid.uuid4(), "status": VideoProjectStatus.draft, "created_at": _now(), "updated_at": _now(), **payload}
        self._projects[project["id"]] = project
        return dict(project)

    async def get(self, project_id: UUID) -> dict | None:
        row = self._projects.get(project_id)
        return dict(row) if row else None

    async def list(self, limit: int, offset: int, status: VideoProjectStatus | None, channel_id: UUID | None, workspace_id: UUID | None):
        rows = list(self._projects.values())
        if status:
            rows = [r for r in rows if r["status"] == status]
        if channel_id:
            rows = [r for r in rows if r.get("channel_id") == channel_id]
        if workspace_id:
            rows = [r for r in rows if r.get("workspace_id") == workspace_id]
        return [dict(r) for r in rows[offset : offset + limit]], len(rows)

    async def update(self, project_id: UUID, data: dict) -> dict:
        row = self._projects[project_id]
        for k, v in data.items():
            if v is not None:
                row[k] = v
        row["updated_at"] = _now()
        return dict(row)

    async def update_project_status(self, project_id: UUID, status: VideoProjectStatus) -> dict:
        return await self.update(project_id, {"status": status})

    async def delete(self, project_id: UUID) -> None:
        self._projects.pop(project_id, None)

    # ── Channels ──────────────────────────────────────────────────────────────

    async def register_channel(self, organization_id: UUID, channel_id: UUID) -> dict:
        key = f"{organization_id}:{channel_id}"
        if key not in self._channels:
            self._channels[key] = {"organization_id": organization_id, "channel_id": channel_id, "created_at": _now()}
        return self._channels[key]

    async def register_user(self, organization_id: UUID, user_id: UUID) -> None:
        return None

    # ── Usage & plan limits ───────────────────────────────────────────────────

    async def get_monthly_usage(self, organization_id: UUID, month_start: datetime) -> dict:
        channels = sum(1 for k in self._channels if k.startswith(f"{organization_id}:"))
        projects = sum(1 for p in self._projects.values() if p.get("organization_id") == organization_id)
        ai_cost = sum(sum(costs) for pid, costs in self._llm_costs.items() if self._projects.get(pid, {}).get("organization_id") == organization_id)
        quota = sum(e["quota_cost"] for e in self.youtube_quota_ledger_entries if e.get("organization_id") == organization_id)
        return {"projects": projects, "channels": channels, "ai_cost_usd": float(ai_cost), "youtube_quota": int(quota), "users": 0}

    async def create_monthly_usage_snapshot(self, payload: dict) -> dict:
        return payload

    # ── Approval decisions ────────────────────────────────────────────────────

    async def add_approval_decision(self, project_id: UUID, status: ApprovalStatus, comment: str | None, decided_by_user_id: UUID) -> dict:
        decision = {"id": _uuid.uuid4(), "video_project_id": project_id, "status": status.value, "comment": comment, "decided_by_user_id": decided_by_user_id, "created_at": _now()}
        self._approval_decisions.setdefault(project_id, []).append(decision)
        return decision

    async def get_approval_decisions(self, project_id: UUID) -> list[dict]:
        return list(self._approval_decisions.get(project_id, []))

    # ── Compliance ────────────────────────────────────────────────────────────

    async def get_compliance(self, project_id: UUID) -> dict:
        row = self._compliance_reports.get(project_id)
        if row:
            return dict(row)
        return _default_compliance(project_id)

    async def save_compliance_report(self, project_id: UUID, report: dict) -> dict:
        self._compliance_reports[project_id] = {"video_project_id": project_id, **report}
        return report

    # ── Analytics ─────────────────────────────────────────────────────────────

    async def create_analytics_snapshot(self, payload: dict) -> dict:
        snap = {"id": _uuid.uuid4(), "created_at": _now(), "updated_at": _now(), **payload}
        pid = payload.get("video_project_id")
        self._analytics.setdefault(pid, []).append(snap)
        p = snap.get("payload", {})
        return {"id": snap["id"], "video_project_id": snap.get("video_project_id"), "channel_id": snap.get("channel_id"), "youtube_video_id": p.get("youtube_video_id"), "views": p.get("views"), "watch_time_minutes": p.get("watch_time_minutes"), "average_view_duration": p.get("average_view_duration"), "ctr": p.get("ctr"), "likes": p.get("likes"), "comments": p.get("comments"), "subscribers_gained": p.get("subscribers_gained"), "estimated_revenue": p.get("estimated_revenue"), "snapshot_at": p.get("snapshot_at"), "created_at": snap["created_at"], "updated_at": snap["updated_at"]}

    async def get_analytics(self, project_id: UUID) -> list[dict]:
        return [{"id": s["id"], "video_project_id": s.get("video_project_id"), "channel_id": s.get("channel_id"), "youtube_video_id": s.get("payload", {}).get("youtube_video_id"), "views": s.get("payload", {}).get("views"), "watch_time_minutes": s.get("payload", {}).get("watch_time_minutes"), "average_view_duration": s.get("payload", {}).get("average_view_duration"), "ctr": s.get("payload", {}).get("ctr"), "likes": s.get("payload", {}).get("likes"), "comments": s.get("payload", {}).get("comments"), "subscribers_gained": s.get("payload", {}).get("subscribers_gained"), "estimated_revenue": s.get("payload", {}).get("estimated_revenue"), "snapshot_at": s.get("payload", {}).get("snapshot_at"), "created_at": s["created_at"], "updated_at": s["updated_at"]} for s in self._analytics.get(project_id, [])]

    # ── Publishing plans ──────────────────────────────────────────────────────

    async def create_publishing_plan(self, payload: dict) -> dict:
        plan = {
            "id": _uuid.uuid4(),
            "status": PublishingPlanStatus.draft,
            "youtube_video_id": None,
            "scheduled_at": None,
            "selected_title_variant_id": None,
            "selected_thumbnail_concept_id": None,
            "final_description_snapshot": None,
            "final_tags_snapshot": None,
            "compliance_report_id": None,
            "asset_bundle_metadata": None,
            "created_at": _now(),
            "updated_at": _now(),
            **payload,
        }
        self._publishing_plans[plan["id"]] = plan
        return dict(plan)

    async def get_publishing_plan(self, plan_id: UUID) -> dict | None:
        row = self._publishing_plans.get(plan_id)
        return dict(row) if row else None

    async def update_publishing_plan(self, plan_id: UUID, data: dict) -> dict:
        row = self._publishing_plans[plan_id]
        for k, v in data.items():
            if v is not None:
                row[k] = v
        row["updated_at"] = _now()
        return dict(row)


    async def create_channel_memory(self, payload: dict) -> dict:
        row = {"id": _uuid.uuid4(), "created_at": _now(), "updated_at": _now(), **payload}
        self._entity_rows.setdefault("channel_memories", []).append(row)
        return dict(row)

    async def list_channel_memories(self, channel_id: UUID) -> list[dict]:
        rows = [r for r in self._entity_rows.get("channel_memories", []) if r.get("channel_id") == channel_id]
        return sorted(rows, key=lambda r: r["created_at"])

    async def get_channel_memory(self, memory_id: UUID) -> dict | None:
        row = next((r for r in self._entity_rows.get("channel_memories", []) if r["id"] == memory_id), None)
        return dict(row) if row else None

    async def _create_project_entity(self, key: str, payload: dict) -> dict:
        row = {"id": _uuid.uuid4(), "created_at": _now(), "updated_at": _now(), **payload}
        self._entity_rows.setdefault(key, []).append(row)
        return dict(row)

    async def _list_project_entities(self, key: str, project_id: UUID) -> list[dict]:
        rows = [r for r in self._entity_rows.get(key, []) if r.get("video_project_id") == project_id]
        return sorted(rows, key=lambda r: r["created_at"])

    async def _get_project_entity(self, key: str, entity_id: UUID) -> dict | None:
        row = next((r for r in self._entity_rows.get(key, []) if r["id"] == entity_id), None)
        return dict(row) if row else None

    async def create_research_brief(self, payload: dict) -> dict: return await self._create_project_entity("research_briefs", payload)
    async def list_research_briefs(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("research_briefs", project_id)
    async def get_research_brief(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("research_briefs", entity_id)
    async def create_angle(self, payload: dict) -> dict: return await self._create_project_entity("angles", payload)
    async def list_angles(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("angles", project_id)
    async def get_angle(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("angles", entity_id)
    async def create_hook_variant(self, payload: dict) -> dict: return await self._create_project_entity("hook_variants", payload)
    async def list_hook_variants(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("hook_variants", project_id)
    async def get_hook_variant(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("hook_variants", entity_id)
    async def create_retention_review(self, payload: dict) -> dict: return await self._create_project_entity("retention_reviews", payload)
    async def list_retention_reviews(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("retention_reviews", project_id)
    async def get_retention_review(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("retention_reviews", entity_id)
    async def create_visual_plan(self, payload: dict) -> dict: return await self._create_project_entity("visual_plans", payload)
    async def list_visual_plans(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("visual_plans", project_id)
    async def get_visual_plan(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("visual_plans", entity_id)
    async def create_visual_scene(self, payload: dict) -> dict: return await self._create_project_entity("visual_scenes", payload)
    async def list_visual_scenes(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("visual_scenes", project_id)
    async def get_visual_scene(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("visual_scenes", entity_id)
    async def create_audio_brief(self, payload: dict) -> dict: return await self._create_project_entity("audio_briefs", payload)
    async def list_audio_briefs(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("audio_briefs", project_id)
    async def get_audio_brief(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("audio_briefs", entity_id)
    async def create_title_variant(self, payload: dict) -> dict: return await self._create_project_entity("title_variants", payload)
    async def list_title_variants(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("title_variants", project_id)
    async def get_title_variant(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("title_variants", entity_id)
    async def create_thumbnail_concept(self, payload: dict) -> dict: return await self._create_project_entity("thumbnail_concepts", payload)
    async def list_thumbnail_concepts(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("thumbnail_concepts", project_id)
    async def get_thumbnail_concept(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("thumbnail_concepts", entity_id)
    async def create_monetization_plan(self, payload: dict) -> dict: return await self._create_project_entity("monetization_plans", payload)
    async def list_monetization_plans(self, project_id: UUID) -> list[dict]: return await self._list_project_entities("monetization_plans", project_id)
    async def get_monetization_plan(self, entity_id: UUID) -> dict | None: return await self._get_project_entity("monetization_plans", entity_id)

    # ── Workflow ──────────────────────────────────────────────────────────────

    async def create_workflow_run(self, video_project_id: UUID) -> dict:
        run = {"id": _uuid.uuid4(), "video_project_id": video_project_id, "state": "running", "created_at": _now()}
        self._workflow_runs.setdefault(video_project_id, []).append(run)
        return dict(run)

    async def get_latest_workflow_run(self, video_project_id: UUID) -> dict | None:
        runs = self._workflow_runs.get(video_project_id, [])
        return dict(runs[-1]) if runs else None

    async def create_workflow_step(self, workflow_run_id: UUID, video_project_id: UUID, step_name: str, status: str, attempt: int, idempotency_key: str, input_json: dict) -> dict:
        return {"id": _uuid.uuid4(), "step_name": step_name, "status": status}

    async def append_event(self, video_project_id: UUID, event: dict) -> None:
        self._events.setdefault(video_project_id, []).append({**event, "id": _uuid.uuid4(), "created_at": _now()})

    async def get_events(self, project_id: UUID) -> list[dict]:
        return [{"id": e["id"], "workflow_run_id": e.get("workflow_run_id"), "event_type": e["event_type"], "payload": e.get("payload", {}), "created_at": e["created_at"]} for e in self._events.get(project_id, [])]

    # ── Task execution tracking ───────────────────────────────────────────────

    async def get_or_create_task_execution(self, task_name: str, business_key: str, idempotency_key: str, workflow_run_id: UUID | None = None) -> object:
        if business_key not in self._task_executions:
            class _Exec:
                pass
            ex = _Exec()
            ex.id = _uuid.uuid4()  # type: ignore[attr-defined]
            ex.status = "pending"  # type: ignore[attr-defined]
            ex.retry_count = 0  # type: ignore[attr-defined]
            self._task_executions[business_key] = ex
        return self._task_executions[business_key]

    async def mark_task_execution(self, execution_id: UUID, status: str, retry_count: int, error_code: str | None = None) -> object:
        for ex in self._task_executions.values():
            if ex.id == execution_id:  # type: ignore[attr-defined]
                ex.status = status  # type: ignore[attr-defined]
                ex.retry_count = retry_count  # type: ignore[attr-defined]
                ex.error_code = error_code  # type: ignore[attr-defined]
                return ex
        return None  # type: ignore[return-value]

    async def add_task_attempt(self, execution_id: UUID, attempt_no: int, status: str, error_code: str | None = None) -> object:
        return None  # type: ignore[return-value]

    # ── LLM cost tracking ─────────────────────────────────────────────────────

    async def log_llm_call(self, project_id: UUID, call: dict) -> None:
        return None

    async def log_llm_cost_entry(self, project_id: UUID, entry: dict) -> None:
        self._llm_costs.setdefault(project_id, []).append(entry.get("cost_usd", 0.0))

    async def get_costs(self, project_id: UUID) -> dict:
        total = sum(self._llm_costs.get(project_id, []))
        return {"video_project_id": project_id, "total_cost_usd": round(total, 8)}

    # ── YouTube quota tracking ────────────────────────────────────────────────

    async def log_youtube_quota_entry(self, entry: dict) -> dict:
        self.youtube_quota_ledger_entries.append(entry)
        return entry

    async def get_quota(self, project_id: UUID) -> dict:
        project = await self.get(project_id)
        project_total = sum(e["quota_cost"] for e in self.youtube_quota_ledger_entries if e.get("video_project_id") == project_id)
        channel_id = project["channel_id"] if project else None
        channel_total = sum(e["quota_cost"] for e in self.youtube_quota_ledger_entries if e.get("channel_id") == channel_id) if channel_id else 0
        return {"video_project_id": project_id, "project_quota_cost": int(project_total), "channel_quota_cost": int(channel_total)}


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
            payload = row.payload or {}
            return {"video_project_id": project_id, **payload, "risk_level": row.risk_level}
        return _default_compliance(project_id)
    async def save_compliance_report(self, project_id: UUID, report: dict):
        row = ComplianceReport(video_project_id=project_id, risk_level=report.get("risk_level", ComplianceRiskLevel.low), payload=report, findings=None)
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
        return {
            "id": row.id,
            "video_project_id": row.video_project_id,
            "channel_id": row.channel_id,
            "scheduled_at": row.scheduled_at,
            "status": row.status,
            "youtube_video_id": row.youtube_video_id,
            "title": row.title,
            "description": row.description,
            "tags": row.tags,
            "visibility": row.visibility,
            "selected_title_variant_id": row.selected_title_variant_id,
            "selected_thumbnail_concept_id": row.selected_thumbnail_concept_id,
            "final_description_snapshot": row.final_description_snapshot,
            "final_tags_snapshot": row.final_tags_snapshot,
            "compliance_report_id": row.compliance_report_id,
            "asset_bundle_metadata": row.asset_bundle_metadata,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    async def _create_entity(self, model, payload: dict) -> dict:
        row = model(**payload)
        self.session.add(row)
        await self.session.flush(); await self.session.commit(); await self.session.refresh(row)
        return self._entity_to_dict(row)

    async def _list_entities(self, model, project_id: UUID) -> list[dict]:
        rows = (await self.session.scalars(select(model).where(model.video_project_id == project_id).order_by(model.created_at.asc(), model.id.asc()))).all()
        return [self._entity_to_dict(r) for r in rows]

    async def _get_entity(self, model, entity_id: UUID) -> dict | None:
        row = await self.session.get(model, entity_id)
        return self._entity_to_dict(row) if row else None

    def _entity_to_dict(self, row):
        data = {"id": row.id, "created_at": row.created_at, "updated_at": row.updated_at}
        for attr in ["video_project_id", "channel_id", "status", "memory", "brief", "angle", "hook", "review", "plan", "scene", "title_variant", "concept"]:
            if hasattr(row, attr):
                data[attr] = getattr(row, attr)
        return data

    async def create_channel_memory(self, payload: dict) -> dict: return await self._create_entity(ChannelMemory, payload)
    async def list_channel_memories(self, channel_id: UUID) -> list[dict]:
        rows = (await self.session.scalars(select(ChannelMemory).where(ChannelMemory.channel_id == channel_id).order_by(ChannelMemory.created_at.asc(), ChannelMemory.id.asc()))).all()
        return [self._entity_to_dict(r) for r in rows]
    async def get_channel_memory(self, entity_id: UUID) -> dict | None: return await self._get_entity(ChannelMemory, entity_id)
    async def create_research_brief(self, payload: dict) -> dict: return await self._create_entity(ResearchBrief, payload)
    async def list_research_briefs(self, project_id: UUID) -> list[dict]: return await self._list_entities(ResearchBrief, project_id)
    async def get_research_brief(self, entity_id: UUID) -> dict | None: return await self._get_entity(ResearchBrief, entity_id)
    async def create_angle(self, payload: dict) -> dict: return await self._create_entity(Angle, payload)
    async def list_angles(self, project_id: UUID) -> list[dict]: return await self._list_entities(Angle, project_id)
    async def get_angle(self, entity_id: UUID) -> dict | None: return await self._get_entity(Angle, entity_id)
    async def create_hook_variant(self, payload: dict) -> dict: return await self._create_entity(HookVariant, payload)
    async def list_hook_variants(self, project_id: UUID) -> list[dict]: return await self._list_entities(HookVariant, project_id)
    async def get_hook_variant(self, entity_id: UUID) -> dict | None: return await self._get_entity(HookVariant, entity_id)
    async def create_retention_review(self, payload: dict) -> dict: return await self._create_entity(RetentionReview, payload)
    async def list_retention_reviews(self, project_id: UUID) -> list[dict]: return await self._list_entities(RetentionReview, project_id)
    async def get_retention_review(self, entity_id: UUID) -> dict | None: return await self._get_entity(RetentionReview, entity_id)
    async def create_visual_plan(self, payload: dict) -> dict: return await self._create_entity(VisualPlan, payload)
    async def list_visual_plans(self, project_id: UUID) -> list[dict]: return await self._list_entities(VisualPlan, project_id)
    async def get_visual_plan(self, entity_id: UUID) -> dict | None: return await self._get_entity(VisualPlan, entity_id)
    async def create_visual_scene(self, payload: dict) -> dict: return await self._create_entity(VisualScene, payload)
    async def list_visual_scenes(self, project_id: UUID) -> list[dict]: return await self._list_entities(VisualScene, project_id)
    async def get_visual_scene(self, entity_id: UUID) -> dict | None: return await self._get_entity(VisualScene, entity_id)
    async def create_audio_brief(self, payload: dict) -> dict: return await self._create_entity(AudioBrief, payload)
    async def list_audio_briefs(self, project_id: UUID) -> list[dict]: return await self._list_entities(AudioBrief, project_id)
    async def get_audio_brief(self, entity_id: UUID) -> dict | None: return await self._get_entity(AudioBrief, entity_id)
    async def create_title_variant(self, payload: dict) -> dict: return await self._create_entity(TitleVariant, payload)
    async def list_title_variants(self, project_id: UUID) -> list[dict]: return await self._list_entities(TitleVariant, project_id)
    async def get_title_variant(self, entity_id: UUID) -> dict | None: return await self._get_entity(TitleVariant, entity_id)
    async def create_thumbnail_concept(self, payload: dict) -> dict: return await self._create_entity(ThumbnailConcept, payload)
    async def list_thumbnail_concepts(self, project_id: UUID) -> list[dict]: return await self._list_entities(ThumbnailConcept, project_id)
    async def get_thumbnail_concept(self, entity_id: UUID) -> dict | None: return await self._get_entity(ThumbnailConcept, entity_id)
    async def create_monetization_plan(self, payload: dict) -> dict: return await self._create_entity(MonetizationPlan, payload)
    async def list_monetization_plans(self, project_id: UUID) -> list[dict]: return await self._list_entities(MonetizationPlan, project_id)
    async def get_monetization_plan(self, entity_id: UUID) -> dict | None: return await self._get_entity(MonetizationPlan, entity_id)

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

from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_correlation_id, get_video_project_service, require_mutation_auth
from app.api.errors import structured_error
from app.db.enums import VideoProjectStatus
from app.schemas.video_project import AnalyticsSnapshotIn, AnalyticsSnapshotOut, ApprovalDecisionIn, ApprovalDecisionOut, ComplianceReportOut, PaginatedVideoProjects, PublishingPlanCreate, PublishingPlanOut, PublishingPlanSchedule, VideoProjectCreate, VideoProjectOut, VideoProjectUpdate, WorkflowEventOut
from app.services.video_project_service import VideoProjectService

router = APIRouter(prefix="/api/v1/video-projects", tags=["video-projects"])


async def _require_project(service: VideoProjectService, project_id: UUID, cid: str):
    row = await service.get_project(project_id)
    if not row:
        raise structured_error(404, "VIDEO_PROJECT_NOT_FOUND", "VideoProject not found", cid)
    return row


@router.get("", response_model=PaginatedVideoProjects)
async def list_video_projects(limit: int = 20, offset: int = 0, status: VideoProjectStatus | None = None, channel_id: UUID | None = None, workspace_id: UUID | None = None, service: VideoProjectService = Depends(get_video_project_service)):
    items, total = await service.list_projects(limit, offset, status, channel_id, workspace_id)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("", response_model=VideoProjectOut, status_code=201)
async def create_video_project(payload: VideoProjectCreate, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    try:
        return await service.create_project(payload)
    except ValueError as exc:
        raise structured_error(409, "PLAN_PROJECT_LIMIT_REACHED", str(exc), correlation_id)


@router.get("/{project_id}", response_model=VideoProjectOut)
async def get_video_project(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    return await _require_project(service, project_id, correlation_id)


@router.patch("/{project_id}", response_model=VideoProjectOut)
async def patch_video_project(project_id: UUID, payload: VideoProjectUpdate, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.update_project(project_id, payload)


@router.delete("/{project_id}", status_code=204)
async def delete_video_project(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    await service.delete_project(project_id)
    return Response(status_code=204)


@router.post("/{project_id}/start-workflow")
async def start_workflow(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.start_workflow(project_id)


@router.post("/{project_id}/request-approval")
async def request_approval(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.request_approval(project_id)


@router.post("/{project_id}/approve")
async def approve(project_id: UUID, payload: ApprovalDecisionIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.approve(project_id, payload.comment, payload.decided_by_user_id)


@router.post("/{project_id}/reject")
async def reject(project_id: UUID, payload: ApprovalDecisionIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.reject(project_id, payload.comment, payload.decided_by_user_id)


@router.post("/{project_id}/needs-changes")
async def needs_changes(project_id: UUID, payload: ApprovalDecisionIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.needs_changes(project_id, payload.comment, payload.decided_by_user_id)


@router.get("/{project_id}/approval-decisions", response_model=list[ApprovalDecisionOut])
async def approval_decisions(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    await _require_project(service, project_id, correlation_id)
    return await service.get_approval_decisions(project_id)


@router.get("/{project_id}/events", response_model=list[WorkflowEventOut])
async def events(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    await _require_project(service, project_id, correlation_id)
    return await service.get_events(project_id)


@router.get("/{project_id}/costs")
async def costs(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    await _require_project(service, project_id, correlation_id)
    return await service.get_costs(project_id)


@router.get("/{project_id}/quota")
async def quota(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    await _require_project(service, project_id, correlation_id)
    return await service.get_quota(project_id)


@router.post("/{project_id}/compliance", response_model=ComplianceReportOut)
async def run_compliance(project_id: UUID, payload: dict, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.run_compliance(
        project_id,
        metadata=payload.get("metadata", {}),
        disclosure_decision_missing=bool(payload.get("disclosure_decision_missing", False)),
    )


@router.get("/{project_id}/compliance", response_model=ComplianceReportOut)
async def compliance(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    await _require_project(service, project_id, correlation_id)
    return await service.get_compliance(project_id)


@router.get("/{project_id}/analytics", response_model=list[AnalyticsSnapshotOut])
async def analytics(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    await _require_project(service, project_id, correlation_id)
    return await service.get_analytics(project_id)


@router.post("/{project_id}/analytics", response_model=AnalyticsSnapshotOut, status_code=201)
async def create_analytics_snapshot(project_id: UUID, payload: AnalyticsSnapshotIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, project_id, correlation_id)
    return await service.create_analytics_snapshot(project_id, payload.model_dump())


@router.post("/publishing-plans", response_model=PublishingPlanOut, status_code=201)
async def create_publishing_plan(payload: PublishingPlanCreate, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    await _require_project(service, payload.video_project_id, correlation_id)
    return await service.create_publishing_plan(payload.model_dump())


@router.post("/publishing-plans/{plan_id}/schedule", response_model=PublishingPlanOut)
async def schedule_publishing(plan_id: UUID, payload: PublishingPlanSchedule, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)): 
    plan = await service.repo.get_publishing_plan(plan_id)
    if not plan:
        raise structured_error(404, "PUBLISHING_PLAN_NOT_FOUND", "PublishingPlan not found", correlation_id)
    try:
        return await service.schedule_publishing(plan_id, payload.scheduled_at)
    except ValueError as exc:
        raise structured_error(409, "PUBLISHING_PLAN_INVALID", str(exc), correlation_id)


@router.post("/publishing-plans/{plan_id}/publish", response_model=PublishingPlanOut)
async def publish_video(plan_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id), auth: None = Depends(require_mutation_auth)):
    plan = await service.repo.get_publishing_plan(plan_id)
    if not plan:
        raise structured_error(404, "PUBLISHING_PLAN_NOT_FOUND", "PublishingPlan not found", correlation_id)
    try:
        return await service.publish_video(plan_id)
    except ValueError as exc:
        raise structured_error(409, "PUBLISHING_PLAN_INVALID", str(exc), correlation_id)

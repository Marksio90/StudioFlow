from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_correlation_id, get_video_project_service
from app.api.errors import structured_error
from app.db.enums import VideoProjectStatus
from app.schemas.video_project import AnalyticsSnapshotIn, AnalyticsSnapshotOut, ApprovalDecisionIn, ApprovalDecisionOut, ComplianceReportOut, PaginatedVideoProjects, PublishingPlanCreate, PublishingPlanOut, PublishingPlanSchedule, VideoProjectCreate, VideoProjectOut, VideoProjectUpdate, WorkflowEventOut
from app.services.video_project_service import VideoProjectService

router = APIRouter(prefix="/api/v1/video-projects", tags=["video-projects"])


def _require_project(service: VideoProjectService, project_id: UUID, cid: str):
    row = service.get_project(project_id)
    if not row:
        raise structured_error(404, "VIDEO_PROJECT_NOT_FOUND", "VideoProject not found", cid)
    return row


@router.get("", response_model=PaginatedVideoProjects)
def list_video_projects(limit: int = 20, offset: int = 0, status: VideoProjectStatus | None = None, channel_id: UUID | None = None, workspace_id: UUID | None = None, service: VideoProjectService = Depends(get_video_project_service)):
    items, total = service.list_projects(limit, offset, status, channel_id, workspace_id)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("", response_model=VideoProjectOut, status_code=201)
def create_video_project(payload: VideoProjectCreate, service: VideoProjectService = Depends(get_video_project_service)):
    return service.create_project(payload)


@router.get("/{project_id}", response_model=VideoProjectOut)
def get_video_project(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    return _require_project(service, project_id, correlation_id)


@router.patch("/{project_id}", response_model=VideoProjectOut)
def patch_video_project(project_id: UUID, payload: VideoProjectUpdate, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.update_project(project_id, payload)


@router.delete("/{project_id}", status_code=204)
def delete_video_project(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    service.delete_project(project_id)
    return Response(status_code=204)


@router.post("/{project_id}/start-workflow")
def start_workflow(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.start_workflow(project_id)


@router.post("/{project_id}/request-approval")
def request_approval(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.request_approval(project_id)


@router.post("/{project_id}/approve")
def approve(project_id: UUID, payload: ApprovalDecisionIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.approve(project_id, payload.comment, payload.decided_by_user_id)


@router.post("/{project_id}/reject")
def reject(project_id: UUID, payload: ApprovalDecisionIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.reject(project_id, payload.comment, payload.decided_by_user_id)


@router.post("/{project_id}/needs-changes")
def needs_changes(project_id: UUID, payload: ApprovalDecisionIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.needs_changes(project_id, payload.comment, payload.decided_by_user_id)


@router.get("/{project_id}/approval-decisions", response_model=list[ApprovalDecisionOut])
def approval_decisions(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.get_approval_decisions(project_id)


@router.get("/{project_id}/events", response_model=list[WorkflowEventOut])
def events(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.get_events(project_id)


@router.get("/{project_id}/costs")
def costs(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.get_costs(project_id)


@router.get("/{project_id}/quota")
def quota(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.get_quota(project_id)


@router.post("/{project_id}/compliance", response_model=ComplianceReportOut)
def run_compliance(project_id: UUID, payload: dict, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.run_compliance(
        project_id,
        metadata=payload.get("metadata", {}),
        disclosure_decision_missing=bool(payload.get("disclosure_decision_missing", False)),
    )


@router.get("/{project_id}/compliance", response_model=ComplianceReportOut)
def compliance(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.get_compliance(project_id)


@router.get("/{project_id}/analytics", response_model=list[AnalyticsSnapshotOut])
def analytics(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.get_analytics(project_id)


@router.post("/{project_id}/analytics", response_model=AnalyticsSnapshotOut, status_code=201)
def create_analytics_snapshot(project_id: UUID, payload: AnalyticsSnapshotIn, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.create_analytics_snapshot(project_id, payload.model_dump())


@router.post("/publishing-plans", response_model=PublishingPlanOut, status_code=201)
def create_publishing_plan(payload: PublishingPlanCreate, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, payload.video_project_id, correlation_id)
    return service.create_publishing_plan(payload.model_dump())


@router.post("/publishing-plans/{plan_id}/schedule", response_model=PublishingPlanOut)
def schedule_publishing(plan_id: UUID, payload: PublishingPlanSchedule, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    plan = service.repo.get_publishing_plan(plan_id)
    if not plan:
        raise structured_error(404, "PUBLISHING_PLAN_NOT_FOUND", "PublishingPlan not found", correlation_id)
    try:
        return service.schedule_publishing(plan_id, payload.scheduled_at)
    except ValueError as exc:
        raise structured_error(409, "PUBLISHING_PLAN_INVALID", str(exc), correlation_id)

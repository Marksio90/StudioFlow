from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.deps import get_correlation_id, get_video_project_service
from app.api.errors import structured_error
from app.db.enums import VideoProjectStatus
from app.schemas.video_project import ComplianceReportOut, PaginatedVideoProjects, VideoProjectCreate, VideoProjectOut, VideoProjectUpdate, WorkflowEventOut
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
def approve(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.approve(project_id)


@router.post("/{project_id}/reject")
def reject(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.reject(project_id)


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


@router.get("/{project_id}/analytics")
def analytics(project_id: UUID, service: VideoProjectService = Depends(get_video_project_service), correlation_id: str = Depends(get_correlation_id)):
    _require_project(service, project_id, correlation_id)
    return service.get_analytics(project_id)

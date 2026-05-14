from uuid import UUID

from app.db.enums import VideoProjectStatus
from app.schemas.video_project import VideoProjectCreate, VideoProjectUpdate
from app.services.compliance_service import ComplianceInput, ComplianceService
from app.services.workflow_engine import WorkflowEngine


class VideoProjectService:
    def __init__(self, repo):
        self.repo = repo
        self.engine = WorkflowEngine(repo)
        self.compliance_service = ComplianceService()

    def list_projects(self, limit: int, offset: int, status: VideoProjectStatus | None, channel_id: UUID | None, workspace_id: UUID | None):
        return self.repo.list(limit=limit, offset=offset, status=status, channel_id=channel_id, workspace_id=workspace_id)

    def create_project(self, payload: VideoProjectCreate):
        return self.repo.create(payload.model_dump())

    def get_project(self, project_id: UUID):
        return self.repo.get(project_id)

    def update_project(self, project_id: UUID, payload: VideoProjectUpdate):
        return self.repo.update(project_id, payload.model_dump(exclude_unset=True))

    def delete_project(self, project_id: UUID):
        return self.repo.delete(project_id)

    def start_workflow(self, project_id: UUID):
        return self.engine.start(project_id)

    def request_approval(self, project_id: UUID):
        return self.repo.update(project_id, {"status": VideoProjectStatus.awaiting_review})

    def approve(self, project_id: UUID):
        return self.engine.approve(project_id)

    def reject(self, project_id: UUID):
        return self.engine.reject(project_id)

    def get_events(self, project_id: UUID):
        return self.repo.get_events(project_id)

    def get_costs(self, project_id: UUID):
        return self.repo.get_costs(project_id)

    def get_quota(self, project_id: UUID):
        return self.repo.get_quota(project_id)

    def get_compliance(self, project_id: UUID):
        return self.repo.get_compliance(project_id)

    def run_compliance(self, project_id: UUID, metadata: dict | None = None, disclosure_decision_missing: bool = False):
        report = self.compliance_service.evaluate(
            ComplianceInput(
                video_project_id=project_id,
                metadata=metadata or {},
                disclosure_decision_missing=disclosure_decision_missing,
            )
        )
        return self.repo.save_compliance_report(project_id, report.model_dump())

    def get_analytics(self, project_id: UUID):
        return self.repo.get_analytics(project_id)

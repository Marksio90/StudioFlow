from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.db.enums import ComplianceRiskLevel, VideoProjectStatus


class VideoProjectCreate(BaseModel):
    organization_id: UUID
    workspace_id: UUID
    channel_id: UUID
    title: str = Field(min_length=1, max_length=255)


class VideoProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[VideoProjectStatus] = None


class VideoProjectOut(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    channel_id: UUID
    title: str
    status: VideoProjectStatus
    created_at: datetime
    updated_at: datetime


class PaginatedVideoProjects(BaseModel):
    items: list[VideoProjectOut]
    total: int
    limit: int
    offset: int


class WorkflowRunOut(BaseModel):
    id: UUID
    video_project_id: UUID
    state: str


class WorkflowEventOut(BaseModel):
    id: UUID
    workflow_run_id: UUID
    event_type: str
    payload: dict


class ComplianceOut(BaseModel):
    risk_level: ComplianceRiskLevel
    findings: Optional[str] = None

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    organization_id: UUID
    workspace_id: UUID
    name: str = Field(min_length=1, max_length=255)
    youtube_channel_id: str = Field(min_length=1, max_length=255)


class ChannelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    youtube_channel_id: str | None = Field(default=None, min_length=1, max_length=255)


class ChannelOut(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    name: str
    youtube_channel_id: str
    created_at: datetime
    updated_at: datetime


class PaginatedChannels(BaseModel):
    items: list[ChannelOut]
    total: int
    limit: int
    offset: int

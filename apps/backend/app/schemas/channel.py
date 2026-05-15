from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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


class ChannelMemoryPayload(BaseModel):
    approved_title_patterns: list[str] = Field(default_factory=list)
    rejected_title_patterns: list[str] = Field(default_factory=list)
    thumbnail_rules: dict = Field(default_factory=dict)
    banned_phrases: list[str] = Field(default_factory=list)
    preferred_phrases: list[str] = Field(default_factory=list)
    compliance_preferences: dict = Field(default_factory=dict)
    narrator_style: dict = Field(default_factory=dict)
    visual_style: dict = Field(default_factory=dict)
    audience_objections: list[str] = Field(default_factory=list)
    best_performing_patterns: list[str] = Field(default_factory=list)
    worst_performing_patterns: list[str] = Field(default_factory=list)
    freeform_memory_notes: list[str] = Field(default_factory=list)

    @field_validator("banned_phrases")
    @classmethod
    def dedupe_banned_phrases(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for phrase in value:
            folded = phrase.casefold()
            if folded in seen:
                continue
            seen.add(folded)
            deduped.append(phrase)
        return deduped


class ChannelMemoryOut(BaseModel):
    channel_id: UUID
    memory: ChannelMemoryPayload = Field(default_factory=ChannelMemoryPayload)

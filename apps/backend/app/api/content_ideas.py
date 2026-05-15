from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import or_, select

from app.api.channels import _get_channel
from app.api.deps import Identity, get_correlation_id, get_db_session, get_llm_provider, repo_singleton, require_action
from app.api.errors import structured_error
from app.db.models import Channel, ChannelMemory, ContentIdea, LLMCall, TopicResearchReport
from app.schemas.channel import ChannelMemoryPayload
from app.schemas.video_project import (
    ContentIdeaCreatePayload,
    ContentIdeaResearchAnalyzeResponse,
    ContentIdeaResearchReportListResponse,
    ContentIdeaResearchReportPayload,
    ContentIdeaListFilters,
    ContentIdeaOut,
    ContentIdeaResponse,
    ContentIdeaStatusChangePayload,
    ContentIdeaUpdatePayload,
)
from app.services.ai_provider import LLMMessage, LLMProvider, LLMRequest
from app.services.prompt_registry import build_default_prompt_registry

router = APIRouter(tags=["content-ideas"])

ALLOWED_IDEA_STATUSES = {"idea", "draft", "in_review", "approved", "scheduled", "published", "archived"}
MUTABLE_FIELDS = {
    "title",
    "description",
    "status",
    "content_pillar",
    "target_keyword",
    "viewer_problem",
    "viewer_promise",
    "notes",
    "niche_score",
    "topic_score",
    "originality_score",
    "risk_score",
    "idea_text",
}
_memory_topic_reports: dict[UUID, list[ContentIdeaResearchAnalyzeResponse]] = {}


async def _generate_topic_research_report(provider: LLMProvider, *, idea, channel, channel_memory: dict) -> dict:
    prompt_registry = build_default_prompt_registry()
    payload = {
        "idea": {
            "id": str(idea.id),
            "title": idea.title,
            "description": idea.description,
            "content_pillar": idea.content_pillar,
            "target_keyword": idea.target_keyword,
            "viewer_problem": idea.viewer_problem,
            "viewer_promise": idea.viewer_promise,
            "notes": idea.notes,
        },
        "channel": {"id": str(channel.id), "name": channel.name, "niche": channel.niche, "target_audience": channel.target_audience},
        "channel_memory": channel_memory,
    }
    system_prompt, user_prompt = prompt_registry.render(
        name="topic_research_analyze",
        version="v1",
        variables={"payload_json": str(payload)},
    )
    response = provider.generate(
        LLMRequest(task_type="TopicResearchAgent", system_prompt=system_prompt, messages=[LLMMessage(role="user", content=user_prompt, trusted=False)])
    )
    parsed = response.parsed_json or {
        "summary": response.raw_text[:600],
        "audience_fit": "Needs human review",
        "demand_signals": [],
        "competition_notes": [],
        "content_gaps": [],
        "suggested_angles": [],
        "source_queries": [],
        "confidence": 0.25,
    }
    return parsed, user_prompt, response


async def _require_idea(idea_id: UUID, correlation_id: str, identity: Identity, session):
    if session is None:
        rows = repo_singleton._entity_rows.get("content_ideas", [])
        row = next((r for r in rows if r.get("id") == idea_id), None)
    else:
        result = await session.execute(select(ContentIdea).where(ContentIdea.id == idea_id))
        entity = result.scalar_one_or_none()
        row = entity

    if not row:
        raise structured_error(404, "CONTENT_IDEA_NOT_FOUND", "ContentIdea not found", correlation_id)

    channel_id = row.get("channel_id") if isinstance(row, dict) else row.channel_id
    await _get_channel(channel_id, correlation_id, identity, session)
    return row


@router.get("/api/v1/channels/{channel_id}/ideas", response_model=list[ContentIdeaOut])
async def list_content_ideas(
    channel_id: UUID,
    status: str | None = None,
    content_pillar: str | None = None,
    q: str | None = None,
    include_archived: bool = Query(False),
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("read", "channels")),
):
    _ = ContentIdeaListFilters(status=status, content_pillar=content_pillar, q=q, include_archived=include_archived)
    await _get_channel(channel_id, correlation_id, identity, session)
    if status is not None and status not in ALLOWED_IDEA_STATUSES:
        raise structured_error(422, "CONTENT_IDEA_INVALID_STATUS", "Invalid status value", correlation_id)

    if session is None:
        rows = [r for r in repo_singleton._entity_rows.get("content_ideas", []) if r.get("channel_id") == channel_id]
        if status is not None:
            rows = [r for r in rows if r.get("status") == status]
        if content_pillar is not None:
            rows = [r for r in rows if r.get("content_pillar") == content_pillar]
        if not include_archived:
            rows = [r for r in rows if r.get("status") != "archived"]
        if q:
            needle = q.lower().strip()
            rows = [r for r in rows if needle in (r.get("title", "") + " " + r.get("description", "") + " " + r.get("notes", "")).lower()]
        return sorted(rows, key=lambda r: (r.get("created_at"), r.get("id")))

    stmt = select(ContentIdea).where(ContentIdea.channel_id == channel_id)
    if status is not None:
        stmt = stmt.where(ContentIdea.status == status)
    if content_pillar is not None:
        stmt = stmt.where(ContentIdea.content_pillar == content_pillar)
    if not include_archived:
        stmt = stmt.where(ContentIdea.status != "archived")
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(ContentIdea.title.ilike(pattern), ContentIdea.description.ilike(pattern), ContentIdea.notes.ilike(pattern)))
    stmt = stmt.order_by(ContentIdea.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("/api/v1/channels/{channel_id}/ideas", response_model=ContentIdeaResponse, status_code=201)
async def create_content_idea(
    channel_id: UUID,
    payload: ContentIdeaCreatePayload,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    await _get_channel(channel_id, correlation_id, identity, session)
    if payload.channel_id is not None and payload.channel_id != channel_id:
        raise structured_error(422, "CONTENT_IDEA_INVALID_CHANNEL", "Payload channel_id must match route channel_id", correlation_id)
    if payload.status not in ALLOWED_IDEA_STATUSES:
        raise structured_error(422, "CONTENT_IDEA_INVALID_STATUS", "Invalid status value", correlation_id)

    data = payload.model_dump()
    scores = data.pop("scores") or {}
    data.update(scores)
    data["channel_id"] = channel_id
    data["idea_text"] = data.get("idea_text") or data.get("description", "")

    if session is None:
        from datetime import datetime, timezone
        import uuid as _uuid

        now = datetime.now(timezone.utc)
        row = {"id": _uuid.uuid4(), "created_at": now, "updated_at": now, **data}
        repo_singleton._entity_rows.setdefault("content_ideas", []).append(row)
        return row

    row = ContentIdea(**data)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


@router.get("/api/v1/ideas/{idea_id}", response_model=ContentIdeaOut)
async def get_content_idea(
    idea_id: UUID,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("read", "channels")),
):
    return await _require_idea(idea_id, correlation_id, identity, session)


@router.patch("/api/v1/ideas/{idea_id}", response_model=ContentIdeaResponse)
async def patch_content_idea(
    idea_id: UUID,
    payload: ContentIdeaUpdatePayload,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    row = await _require_idea(idea_id, correlation_id, identity, session)
    payload_dict = payload.model_dump(exclude_unset=True)
    if "scores" in payload_dict:
        scores = payload_dict.pop("scores") or {}
        payload_dict.update(scores)
    unknown = [k for k in payload_dict.keys() if k not in MUTABLE_FIELDS]
    if unknown:
        raise structured_error(422, "CONTENT_IDEA_INVALID_FIELDS", f"Unsupported mutable fields: {', '.join(sorted(unknown))}", correlation_id)
    if "status" in payload_dict and payload_dict["status"] not in ALLOWED_IDEA_STATUSES:
        raise structured_error(422, "CONTENT_IDEA_INVALID_STATUS", "Invalid status value", correlation_id)

    if session is None:
        for k, v in payload_dict.items():
            if v is not None:
                row[k] = v
        return row

    for k, v in payload_dict.items():
        if v is not None:
            setattr(row, k, v)
    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/api/v1/ideas/{idea_id}", status_code=204)
async def delete_content_idea(
    idea_id: UUID,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    row = await _require_idea(idea_id, correlation_id, identity, session)
    if session is None:
        repo_singleton._entity_rows["content_ideas"] = [r for r in repo_singleton._entity_rows.get("content_ideas", []) if r.get("id") != idea_id]
        return Response(status_code=204)
    await session.delete(row)
    await session.commit()
    return Response(status_code=204)


@router.post("/api/v1/ideas/{idea_id}/status", response_model=ContentIdeaResponse)
async def set_content_idea_status(
    idea_id: UUID,
    payload: ContentIdeaStatusChangePayload,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    status = payload.status
    if status not in ALLOWED_IDEA_STATUSES:
        raise structured_error(422, "CONTENT_IDEA_INVALID_STATUS", "Invalid status value", correlation_id)

    row = await _require_idea(idea_id, correlation_id, identity, session)
    if session is None:
        row["status"] = status
        return row

    row.status = status
    await session.commit()
    await session.refresh(row)
    return row


@router.post("/api/v1/ideas/{idea_id}/research/analyze", response_model=ContentIdeaResearchAnalyzeResponse, tags=["content-ideas"])
async def analyze_content_idea_research(
    idea_id: UUID,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
    provider: LLMProvider = Depends(get_llm_provider),
):
    idea = await _require_idea(idea_id, correlation_id, identity, session)
    if session is None:
        channel_memory = ChannelMemoryPayload().model_dump()
        report_payload = ContentIdeaResearchReportPayload(summary=f"Research summary for {idea.get('title', 'idea')}").model_dump()
        out = ContentIdeaResearchAnalyzeResponse.model_validate(
            {"id": idea_id, "content_idea_id": idea_id, "channel_id": idea["channel_id"], "report": report_payload, "created_at": idea["updated_at"]}
        )
        _memory_topic_reports.setdefault(idea_id, []).append(out)
        return out

    channel = (await session.execute(select(Channel).where(Channel.id == idea.channel_id))).scalar_one()
    memory = (await session.execute(select(ChannelMemory).where(ChannelMemory.channel_id == idea.channel_id).order_by(ChannelMemory.created_at.desc()))).scalars().first()
    report_data, user_prompt, llm_response = await _generate_topic_research_report(
        provider, idea=idea, channel=channel, channel_memory=(memory.memory if memory else ChannelMemoryPayload().model_dump())
    )
    validated_report = ContentIdeaResearchReportPayload.model_validate(report_data)
    row = TopicResearchReport(content_idea_id=idea.id, channel_id=idea.channel_id, report=validated_report.model_dump())
    session.add(row)
    session.add(
        LLMCall(
            video_project_id=idea.video_project_id,
            channel_id=idea.channel_id,
            provider=str(llm_response.provider_metadata.get("provider", "unknown")),
            model=str(llm_response.provider_metadata.get("model", "unknown")),
            prompt_template_name="topic_research_analyze",
            prompt_template_version="v1",
            input_preview=user_prompt[:500],
            output_preview=llm_response.raw_text[:500],
            prompt_tokens=llm_response.usage.input_tokens,
            completion_tokens=llm_response.usage.output_tokens,
            total_tokens=llm_response.usage.total_tokens,
            related_entity_type="content_idea",
            related_entity_id=idea.id,
        )
    )
    await session.commit()
    await session.refresh(row)
    return ContentIdeaResearchAnalyzeResponse(id=row.id, content_idea_id=row.content_idea_id, channel_id=row.channel_id, report=validated_report, created_at=row.created_at)


@router.get("/api/v1/ideas/{idea_id}/research/latest", response_model=ContentIdeaResearchAnalyzeResponse, tags=["content-ideas"])
async def get_latest_content_idea_research(
    idea_id: UUID,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("read", "channels")),
):
    _ = await _require_idea(idea_id, correlation_id, identity, session)
    if session is None:
        rows = sorted(_memory_topic_reports.get(idea_id, []), key=lambda r: r.created_at, reverse=True)
        if not rows:
            raise structured_error(404, "CONTENT_IDEA_RESEARCH_NOT_FOUND", "No research reports found for content idea", correlation_id)
        return rows[0]
    row = (await session.execute(select(TopicResearchReport).where(TopicResearchReport.content_idea_id == idea_id).order_by(TopicResearchReport.created_at.desc()))).scalars().first()
    if row is None:
        raise structured_error(404, "CONTENT_IDEA_RESEARCH_NOT_FOUND", "No research reports found for content idea", correlation_id)
    return ContentIdeaResearchAnalyzeResponse(id=row.id, content_idea_id=row.content_idea_id, channel_id=row.channel_id, report=row.report, created_at=row.created_at)


@router.get("/api/v1/ideas/{idea_id}/research/reports", response_model=ContentIdeaResearchReportListResponse, tags=["content-ideas"])
async def list_content_idea_research_reports(
    idea_id: UUID,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("read", "channels")),
):
    _ = await _require_idea(idea_id, correlation_id, identity, session)
    if session is None:
        rows = sorted(_memory_topic_reports.get(idea_id, []), key=lambda r: r.created_at, reverse=True)
        return {"items": rows[offset : offset + limit]}
    rows = (
        await session.execute(
            select(TopicResearchReport)
            .where(TopicResearchReport.content_idea_id == idea_id)
            .order_by(TopicResearchReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()
    return {
        "items": [
            ContentIdeaResearchAnalyzeResponse(id=r.id, content_idea_id=r.content_idea_id, channel_id=r.channel_id, report=r.report, created_at=r.created_at)
            for r in rows
        ]
    }

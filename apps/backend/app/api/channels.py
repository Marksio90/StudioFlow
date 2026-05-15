from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select

from app.api.deps import Identity, get_correlation_id, get_db_session, repo_singleton, require_action
from app.api.errors import structured_error
from app.db.models import Channel, ChannelMemory
from app.schemas.channel import ChannelCreate, ChannelMemoryOut, ChannelMemoryPayload, ChannelOut, ChannelUpdate, PaginatedChannels

router = APIRouter(prefix="/api/v1/channels", tags=["channels"])


async def _get_channel(channel_id: UUID, correlation_id: str, identity: Identity, session):
    if session is None:
        row = repo_singleton._channels.get(str(channel_id))
    else:
        result = await session.execute(select(Channel).where(Channel.id == channel_id))
        entity = result.scalar_one_or_none()
        row = None
        if entity:
            row = {
                "id": entity.id,
                "organization_id": entity.organization_id,
                "workspace_id": entity.workspace_id,
                "name": entity.name,
                "youtube_channel_id": entity.youtube_channel_id,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
            }

    if not row:
        raise structured_error(404, "CHANNEL_NOT_FOUND", "Channel not found", correlation_id)
    if not identity.dev_mode and (row["organization_id"] != identity.org_id or row["workspace_id"] != identity.workspace_id):
        raise structured_error(403, "CHANNEL_FORBIDDEN", "Channel does not belong to tenant", correlation_id)
    return row


@router.get("", response_model=PaginatedChannels)
async def list_channels(
    limit: int = 20,
    offset: int = 0,
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("read", "channels")),
):
    if session is None:
        all_items = list(repo_singleton._channels.values())
        scoped = [item for item in all_items if identity.dev_mode or (item["organization_id"] == identity.org_id and item["workspace_id"] == identity.workspace_id)]
        items = scoped[offset : offset + limit]
        total = len(scoped)
    else:
        query = select(Channel)
        count_query = select(func.count()).select_from(Channel)
        if not identity.dev_mode:
            query = query.where(Channel.organization_id == identity.org_id, Channel.workspace_id == identity.workspace_id)
            count_query = count_query.where(Channel.organization_id == identity.org_id, Channel.workspace_id == identity.workspace_id)
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()
        items = [
            {
                "id": c.id,
                "organization_id": c.organization_id,
                "workspace_id": c.workspace_id,
                "name": c.name,
                "youtube_channel_id": c.youtube_channel_id,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
            for c in result.scalars().all()
        ]

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("", response_model=ChannelOut, status_code=201)
async def create_channel(
    payload: ChannelCreate,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    if not identity.dev_mode and (payload.organization_id != identity.org_id or payload.workspace_id != identity.workspace_id):
        raise structured_error(403, "CHANNEL_FORBIDDEN", "Channel does not belong to tenant", correlation_id)

    if session is None:
        from datetime import datetime, timezone
        import uuid as _uuid

        now = datetime.now(timezone.utc)
        channel = {
            "id": _uuid.uuid4(),
            "organization_id": payload.organization_id,
            "workspace_id": payload.workspace_id,
            "name": payload.name,
            "youtube_channel_id": payload.youtube_channel_id,
            "created_at": now,
            "updated_at": now,
        }
        repo_singleton._channels[str(channel["id"])] = channel
        return channel

    entity = Channel(**payload.model_dump())
    session.add(entity)
    await session.commit()
    await session.refresh(entity)
    return entity


@router.get("/{channel_id}", response_model=ChannelOut)
async def get_channel(
    channel_id: UUID,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("read", "channels")),
):
    return await _get_channel(channel_id, correlation_id, identity, session)


@router.patch("/{channel_id}", response_model=ChannelOut)
async def patch_channel(
    channel_id: UUID,
    payload: ChannelUpdate,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    await _get_channel(channel_id, correlation_id, identity, session)
    data = payload.model_dump(exclude_unset=True)

    if session is None:
        row = repo_singleton._channels[str(channel_id)]
        for k, v in data.items():
            if v is not None:
                row[k] = v
        return row

    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    entity = result.scalar_one()
    for k, v in data.items():
        if v is not None:
            setattr(entity, k, v)
    await session.commit()
    await session.refresh(entity)
    return entity


@router.delete("/{channel_id}", status_code=204)
async def delete_channel(
    channel_id: UUID,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    await _get_channel(channel_id, correlation_id, identity, session)

    if session is None:
        repo_singleton._channels.pop(str(channel_id), None)
        return Response(status_code=204)

    result = await session.execute(select(Channel).where(Channel.id == channel_id))
    entity = result.scalar_one()
    await session.delete(entity)
    await session.commit()
    return Response(status_code=204)


@router.get("/{channel_id}/memory", response_model=ChannelMemoryOut)
async def get_channel_memory(
    channel_id: UUID,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("read", "channels")),
):
    await _get_channel(channel_id, correlation_id, identity, session)

    if session is None:
        rows = [r for r in repo_singleton._entity_rows.get("channel_memories", []) if r.get("channel_id") == channel_id]
        row = sorted(rows, key=lambda r: (r.get("created_at"), r.get("id")))[-1] if rows else None
    else:
        result = await session.execute(
            select(ChannelMemory).where(ChannelMemory.channel_id == channel_id).order_by(ChannelMemory.created_at.desc(), ChannelMemory.id.desc())
        )
        row = result.scalars().first()

    memory = ChannelMemoryPayload(**(row["memory"] if isinstance(row, dict) else (row.memory if row else {})))
    return {"channel_id": channel_id, "memory": memory}


@router.patch("/{channel_id}/memory", response_model=ChannelMemoryOut)
async def patch_channel_memory(
    channel_id: UUID,
    payload: ChannelMemoryPayload,
    correlation_id: str = Depends(get_correlation_id),
    session=Depends(get_db_session),
    identity: Identity = Depends(require_action("write", "channels")),
):
    await _get_channel(channel_id, correlation_id, identity, session)
    normalized_memory = payload.model_dump()

    if session is None:
        rows = repo_singleton._entity_rows.setdefault("channel_memories", [])
        existing = [r for r in rows if r.get("channel_id") == channel_id]
        if existing:
            row = sorted(existing, key=lambda r: (r.get("created_at"), r.get("id")))[-1]
            from datetime import datetime, timezone

            row["memory"] = normalized_memory
            row["updated_at"] = datetime.now(timezone.utc)
        else:
            from datetime import datetime, timezone
            import uuid as _uuid

            now = datetime.now(timezone.utc)
            row = {"id": _uuid.uuid4(), "channel_id": channel_id, "memory": normalized_memory, "created_at": now, "updated_at": now}
            rows.append(row)
    else:
        result = await session.execute(
            select(ChannelMemory).where(ChannelMemory.channel_id == channel_id).order_by(ChannelMemory.created_at.desc(), ChannelMemory.id.desc())
        )
        entity = result.scalars().first()
        if entity is None:
            entity = ChannelMemory(channel_id=channel_id, memory=normalized_memory)
            session.add(entity)
        else:
            entity.memory = normalized_memory
        await session.commit()

    return {"channel_id": channel_id, "memory": ChannelMemoryPayload(**normalized_memory)}

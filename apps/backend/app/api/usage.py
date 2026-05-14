from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import Identity, get_usage_service, require_action
from app.api.errors import structured_error
from app.services.usage_service import UsageService

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get("/{organization_id}")
async def get_usage(organization_id: UUID, service: UsageService = Depends(get_usage_service), identity: Identity = Depends(require_action("read", "usage"))):
    if not identity.dev_mode and organization_id != identity.org_id:
        raise structured_error(403, "USAGE_FORBIDDEN", "Usage resource does not belong to tenant", "usage-ownership")
    return await service.get_usage(organization_id)


@router.post("/{organization_id}/channels/{channel_id}")
async def register_channel(organization_id: UUID, channel_id: UUID, service: UsageService = Depends(get_usage_service), identity: Identity = Depends(require_action("manage", "usage"))):
    if not identity.dev_mode and organization_id != identity.org_id:
        raise structured_error(403, "USAGE_FORBIDDEN", "Usage resource does not belong to tenant", "usage-ownership")
    try:
        await service.assert_can_add_channel(organization_id)
    except ValueError as exc:
        raise structured_error(409, "PLAN_CHANNEL_LIMIT_REACHED", str(exc), "usage-channel-limit")
    await service.repo.register_channel(organization_id, channel_id)
    return {"organization_id": organization_id, "channel_id": channel_id, "registered": True}

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_usage_service, require_mutation_auth
from app.api.errors import structured_error
from app.services.usage_service import UsageService

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get("/{organization_id}")
def get_usage(organization_id: UUID, service: UsageService = Depends(get_usage_service)):
    return service.get_usage(organization_id)


@router.post("/{organization_id}/channels/{channel_id}")
def register_channel(organization_id: UUID, channel_id: UUID, service: UsageService = Depends(get_usage_service), auth: None = Depends(require_mutation_auth)):
    try:
        service.assert_can_add_channel(organization_id)
    except ValueError as exc:
        raise structured_error(409, "PLAN_CHANNEL_LIMIT_REACHED", str(exc), "usage-channel-limit")
    service.repo.register_channel(organization_id, channel_id)
    return {"organization_id": organization_id, "channel_id": channel_id, "registered": True}

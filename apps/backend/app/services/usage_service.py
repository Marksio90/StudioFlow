from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from app.services.plan_limit_service import PlanLimitService

@dataclass
class MonthlyUsageSnapshot:
    organization_id: UUID
    period_start: datetime
    projects_used: int
    channels_used: int
    ai_cost_used_usd: float
    youtube_quota_used: int
    users_used: int

class UsageService:
    def __init__(self, repo, plan_limit_service: PlanLimitService | None = None) -> None:
        self.repo = repo
        self.plan_limit_service = plan_limit_service or PlanLimitService()

    def _month_start(self) -> datetime:
        now = datetime.now(timezone.utc)
        return datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    async def get_usage(self, organization_id: UUID) -> dict:
        month_start = self._month_start()
        plan_code = await self.repo.get_plan(organization_id)
        limits = self.plan_limit_service.get_limits(plan_code)
        usage = await self.repo.get_monthly_usage(organization_id, month_start)
        snapshot = MonthlyUsageSnapshot(organization_id, month_start, usage["projects"], usage["channels"], usage["ai_cost_usd"], usage["youtube_quota"], usage["users"])
        await self.repo.create_monthly_usage_snapshot(snapshot.__dict__)
        return {"organization_id": organization_id, "plan": plan_code, "period_start": month_start, "usage": usage, "limits": limits.__dict__}

    async def assert_can_create_project(self, organization_id: UUID) -> None:
        data = await self.get_usage(organization_id)
        self.plan_limit_service.assert_within_limit("projects", data["usage"]["projects"], data["limits"]["max_video_projects_per_month"])

    async def assert_can_add_channel(self, organization_id: UUID) -> None:
        data = await self.get_usage(organization_id)
        self.plan_limit_service.assert_within_limit("channels", data["usage"]["channels"], data["limits"]["max_channels"])


from dataclasses import dataclass


@dataclass(frozen=True)
class PlanLimits:
    code: str
    max_workspaces: int | None
    max_channels: int | None
    max_video_projects_per_month: int | None
    max_users: int | None
    max_ai_cost_usd_per_month: float | None
    max_youtube_quota_per_month: int | None


class PlanLimitService:
    def __init__(self) -> None:
        self._plans = {
            "starter": PlanLimits("starter", 1, 1, 20, 3, 10.0, 10000),
            "pro": PlanLimits("pro", 3, 5, 200, 20, 200.0, 100000),
            "agency": PlanLimits("agency", None, None, None, None, None, None),
        }

    def get_limits(self, plan_code: str) -> PlanLimits:
        return self._plans.get(plan_code.lower(), self._plans["starter"])

    def assert_within_limit(self, metric_name: str, current_value: float, max_value: float | None) -> None:
        if max_value is not None and current_value >= max_value:
            raise ValueError(f"{metric_name} limit reached")

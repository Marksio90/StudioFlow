from datetime import datetime, timezone
from uuid import UUID

class MockYouTubeAnalyticsProvider:
    def fetch_video_analytics(self, youtube_video_id: str) -> dict:
        base = abs(hash(youtube_video_id)) % 10000
        return {"youtube_video_id": youtube_video_id, "views": 1000 + base, "watch_time_minutes": 300.0 + (base % 500), "average_view_duration": 120.0 + (base % 90), "ctr": 2.5 + (base % 50) / 10, "likes": 100 + (base % 1000), "comments": 10 + (base % 100), "subscribers_gained": 1 + (base % 20), "estimated_revenue": round((1000 + base) * 0.003, 2), "snapshot_at": datetime.now(timezone.utc)}

class AnalyticsService:
    def __init__(self, repo, provider: MockYouTubeAnalyticsProvider | None = None):
        self.repo = repo
        self.provider = provider or MockYouTubeAnalyticsProvider()

    async def save_snapshot(self, project_id: UUID, payload: dict):
        return await self.repo.create_analytics_snapshot({"video_project_id": project_id, **payload})

    async def list_project_analytics(self, project_id: UUID):
        return await self.repo.get_analytics(project_id)

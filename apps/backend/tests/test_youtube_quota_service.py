from uuid import uuid4

from app.repositories.video_project_repository import InMemoryVideoProjectRepository
from app.services.youtube_quota_service import YouTubeCallContext, YouTubeClientQuotaWrapper, YouTubeQuotaService


class DummyYouTubeClient:
    def __init__(self):
        self.should_fail = False

    def call(self, youtube_method: str, **kwargs):
        if self.should_fail:
            raise RuntimeError("boom")
        return {"method": youtube_method, "kwargs": kwargs}


def _context():
    return YouTubeCallContext(
        organization_id=uuid4(),
        workspace_id=uuid4(),
        channel_id=uuid4(),
        video_project_id=uuid4(),
        workflow_run_id=uuid4(),
    )


def test_wrapper_logs_success_and_failure_and_retry():
    repo = InMemoryVideoProjectRepository()
    quota = YouTubeQuotaService(repo, method_costs={"videos.insert": 1600})
    wrapper = YouTubeClientQuotaWrapper(DummyYouTubeClient(), quota)
    ctx = _context()

    result = wrapper.call("videos.insert", context=ctx)
    assert result["method"] == "videos.insert"
    assert len(repo.youtube_quota_ledger_entries) == 1
    first = repo.youtube_quota_ledger_entries[0]
    assert first["quota_cost"] == 1600
    assert first["success"] is True

    wrapper.client.should_fail = True
    retry_marker = uuid4()
    try:
        wrapper.call("videos.insert", context=ctx, retry_of_id=retry_marker)
    except RuntimeError:
        pass

    assert len(repo.youtube_quota_ledger_entries) == 2
    second = repo.youtube_quota_ledger_entries[1]
    assert second["success"] is False
    assert second["retry_of_id"] == retry_marker

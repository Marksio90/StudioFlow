import asyncio
from uuid import uuid4

import pytest

from app.db.enums import VideoProjectStatus
from app.services.video_project_service import VideoProjectService


class FakeRepo:
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()
        self.workflow_runs = []

    async def register_channel(self, organization_id, channel_id):
        return None

    async def create(self, payload):
        async with self.lock:
            pid = uuid4()
            row = {"id": pid, **payload, "status": VideoProjectStatus.draft}
            self.data[pid] = row
            return row

    async def update(self, project_id, data):
        async with self.lock:
            self.data[project_id].update(data)
            return self.data[project_id]

    async def get(self, project_id): return self.data.get(project_id)
    async def list(self, **kwargs): return list(self.data.values()), len(self.data)
    async def delete(self, project_id): self.data.pop(project_id, None)
    async def create_workflow_run(self, video_project_id):
        async with self.lock:
            run = {"id": uuid4(), "video_project_id": video_project_id}
            self.workflow_runs.append(run)
            return run
    async def create_workflow_step(self, *args, **kwargs): return {"id": uuid4(), "step_name": kwargs.get("step_name"), "status": kwargs.get("status")}
    async def append_event(self, *args, **kwargs): return None
    async def update_project_status(self, project_id, status): return await self.update(project_id, {"status": status})


@pytest.mark.asyncio
async def test_parallel_create_update_start_workflow_consistency():
    repo = FakeRepo()
    class Usage:
        async def assert_can_create_project(self, organization_id):
            return None
    svc = VideoProjectService(repo, usage_service=Usage())
    payload = type('P', (), {'organization_id': uuid4(), 'workspace_id': uuid4(), 'channel_id': uuid4(), 'title': 'x', 'model_dump': lambda self: {"organization_id": self.organization_id, "workspace_id": self.workspace_id, "channel_id": self.channel_id, "title": self.title}})()

    created = await asyncio.gather(*[svc.create_project(payload) for _ in range(10)])
    assert len(created) == 10

    await asyncio.gather(*[svc.update_project(r["id"], type('U', (), {'model_dump': lambda self, exclude_unset=True: {"title": "updated"}})()) for r in created])
    rows = await asyncio.gather(*[repo.get(r["id"]) for r in created])
    assert all(row["title"] == "updated" for row in rows)

    runs = await asyncio.gather(*[svc.start_workflow(r["id"]) for r in created])
    assert len(runs) == 10
    assert len(repo.workflow_runs) == 10

from uuid import uuid4


class WorkflowEventEmitter:
    def __init__(self, repo):
        self.repo = repo

    async def emit(self, video_project_id, workflow_run_id, event_type: str, payload: dict, correlation_id: str | None = None, task_id: str | None = None):
        event = {"id": uuid4(), "video_project_id": video_project_id, "workflow_run_id": workflow_run_id, "correlation_id": correlation_id, "event_type": event_type, "payload": payload | {"task_id": task_id} if task_id else payload}
        await self.repo.append_event(video_project_id, event)
        return event

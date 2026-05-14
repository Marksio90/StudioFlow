from uuid import uuid4


class WorkflowEventEmitter:
    def __init__(self, repo):
        self.repo = repo

    def emit(self, video_project_id, workflow_run_id, event_type: str, payload: dict):
        event = {
            "id": uuid4(),
            "video_project_id": video_project_id,
            "workflow_run_id": workflow_run_id,
            "event_type": event_type,
            "payload": payload,
        }
        self.repo.append_event(video_project_id, event)
        return event

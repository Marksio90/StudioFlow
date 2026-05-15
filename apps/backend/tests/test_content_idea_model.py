from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.db.models import ContentIdea
from app.schemas.video_project import ContentIdeaCreatePayload


def test_content_idea_create_payload_requires_title_and_validates_status_in_api_layer_contract() -> None:
    with pytest.raises(ValidationError):
        ContentIdeaCreatePayload(video_project_id=uuid4(), channel_id=uuid4())

    payload = ContentIdeaCreatePayload(video_project_id=uuid4(), channel_id=uuid4(), title="Idea", status="totally-invalid")
    assert payload.status == "totally-invalid"


def test_content_idea_model_requires_channel_relationship() -> None:
    channel_col = ContentIdea.__table__.c.channel_id
    assert channel_col.nullable is False
    fk_targets = {fk.target_fullname for fk in channel_col.foreign_keys}
    assert "channels.id" in fk_targets

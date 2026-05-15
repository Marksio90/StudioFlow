from app.db.models import Channel
from app.schemas.channel import ChannelMemoryPayload


def test_channel_slug_uniqueness_is_scoped_to_org_and_workspace():
    table = Channel.__table__
    uq = next(c for c in table.constraints if c.name == "uq_channels_org_workspace_slug")
    assert [col.name for col in uq.columns] == ["organization_id", "workspace_id", "slug"]


def test_channel_language_default_is_en():
    assert Channel.__table__.c.language.default.arg == "en"


def test_channel_content_pillars_is_structured_json_dict():
    column = Channel.__table__.c.content_pillars
    assert column.nullable is False
    assert column.default is not None
    assert callable(column.default.arg)
    assert column.default.arg.__name__ == "dict"


def test_banned_phrases_are_deduped_case_insensitively():
    payload = ChannelMemoryPayload(banned_phrases=["No Clickbait", "no clickbait", "NO CLICKBait", "Original"])
    assert payload.banned_phrases == ["No Clickbait", "Original"]


def test_channel_memory_defaults_to_empty_collections_when_omitted():
    payload = ChannelMemoryPayload()
    assert payload.approved_title_patterns == []
    assert payload.thumbnail_rules == {}
    assert payload.freeform_memory_notes == []


def test_channel_memory_payload_rejects_invalid_memory_field_types():
    try:
        ChannelMemoryPayload(
            approved_title_patterns="bad",  # must be list[str]
            banned_phrases=["ok"],
            thumbnail_rules=[],  # must be dict
        )
        raise AssertionError("expected validation error")
    except Exception as exc:
        assert "approved_title_patterns" in str(exc) or "thumbnail_rules" in str(exc)

"""expand video_ideas for canonical content idea workflow

Revision ID: 20260515_0008
Revises: 20260515_0007
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0008"
down_revision = "20260515_0007"
branch_labels = None
depends_on = None

IDEA_STATUSES = (
    "idea",
    "research",
    "angle_review",
    "script_draft",
    "script_review",
    "compliance_review",
    "ready_to_publish",
    "published",
    "analyzed",
    "archived",
)


def upgrade() -> None:
    op.add_column("video_ideas", sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("video_ideas", sa.Column("title", sa.String(255), nullable=False, server_default="Untitled idea"))
    op.add_column("video_ideas", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    op.add_column("video_ideas", sa.Column("status", sa.String(32), nullable=False, server_default="idea"))
    op.add_column("video_ideas", sa.Column("content_pillar", sa.String(255), nullable=False, server_default=""))
    op.add_column("video_ideas", sa.Column("target_keyword", sa.String(255), nullable=False, server_default=""))
    op.add_column("video_ideas", sa.Column("viewer_problem", sa.Text(), nullable=False, server_default=""))
    op.add_column("video_ideas", sa.Column("viewer_promise", sa.Text(), nullable=False, server_default=""))
    op.add_column("video_ideas", sa.Column("notes", sa.Text(), nullable=False, server_default=""))
    op.add_column("video_ideas", sa.Column("niche_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("video_ideas", sa.Column("topic_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("video_ideas", sa.Column("originality_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("video_ideas", sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"))

    op.execute(
        """
        UPDATE video_ideas vi
        SET
            channel_id = vp.channel_id,
            title = CASE WHEN COALESCE(NULLIF(BTRIM(vi.idea_text), ''), '') = '' THEN 'Untitled idea' ELSE LEFT(vi.idea_text, 255) END,
            description = COALESCE(vi.idea_text, ''),
            notes = COALESCE(vi.idea_text, '')
        FROM video_projects vp
        WHERE vi.video_project_id = vp.id
        """
    )

    op.create_foreign_key("fk_video_ideas_channel_id_channels", "video_ideas", "channels", ["channel_id"], ["id"])
    op.create_index(op.f("ix_video_ideas_channel_id"), "video_ideas", ["channel_id"])

    op.create_check_constraint(
        "ck_video_ideas_status_valid",
        "video_ideas",
        "status IN ('idea','research','angle_review','script_draft','script_review','compliance_review','ready_to_publish','published','analyzed','archived')",
    )

    op.alter_column("video_ideas", "channel_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("ck_video_ideas_status_valid", "video_ideas", type_="check")
    op.drop_index(op.f("ix_video_ideas_channel_id"), table_name="video_ideas")
    op.drop_constraint("fk_video_ideas_channel_id_channels", "video_ideas", type_="foreignkey")

    op.drop_column("video_ideas", "risk_score")
    op.drop_column("video_ideas", "originality_score")
    op.drop_column("video_ideas", "topic_score")
    op.drop_column("video_ideas", "niche_score")
    op.drop_column("video_ideas", "notes")
    op.drop_column("video_ideas", "viewer_promise")
    op.drop_column("video_ideas", "viewer_problem")
    op.drop_column("video_ideas", "target_keyword")
    op.drop_column("video_ideas", "content_pillar")
    op.drop_column("video_ideas", "status")
    op.drop_column("video_ideas", "description")
    op.drop_column("video_ideas", "title")
    op.drop_column("video_ideas", "channel_id")

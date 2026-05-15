"""add creative strategy entities

Revision ID: 20260515_0003
Revises: 20260514_0002
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0003"
down_revision = "20260514_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channel_memories",
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("memory", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_channel_memories_channel_id"), "channel_memories", ["channel_id"], unique=False)
    op.create_index("ix_channel_memories_channel_created_at", "channel_memories", ["channel_id", "created_at"], unique=False)

    table_specs = [
        ("research_briefs", "status", "brief", True),
        ("angles", None, "angle", False),
        ("hook_variants", None, "hook", False),
        ("retention_reviews", "status", "review", True),
        ("visual_plans", "status", "plan", True),
        ("visual_scenes", None, "scene", False),
        ("audio_briefs", "status", "brief", True),
        ("title_variants", None, "title_variant", False),
        ("thumbnail_concepts", None, "concept", False),
        ("monetization_plans", "status", "plan", True),
    ]

    for table_name, status_col, payload_col, has_status in table_specs:
        columns: list[sa.Column] = [
            sa.Column("video_project_id", postgresql.UUID(as_uuid=True), nullable=False),
        ]
        if has_status and status_col:
            columns.append(sa.Column(status_col, sa.String(length=64), nullable=False, server_default="draft"))
        columns.extend(
            [
                sa.Column(payload_col, postgresql.JSONB(astext_type=sa.Text()), nullable=False),
                sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
                sa.ForeignKeyConstraint(["video_project_id"], ["video_projects.id"]),
                sa.PrimaryKeyConstraint("id"),
            ]
        )
        op.create_table(table_name, *columns)
        op.create_index(op.f(f"ix_{table_name}_video_project_id"), table_name, ["video_project_id"], unique=False)
        op.create_index(f"ix_{table_name}_project_created_at", table_name, ["video_project_id", "created_at"], unique=False)


def downgrade() -> None:
    for table_name in [
        "monetization_plans",
        "thumbnail_concepts",
        "title_variants",
        "audio_briefs",
        "visual_scenes",
        "visual_plans",
        "retention_reviews",
        "hook_variants",
        "angles",
        "research_briefs",
    ]:
        op.drop_index(f"ix_{table_name}_project_created_at", table_name=table_name)
        op.drop_index(op.f(f"ix_{table_name}_video_project_id"), table_name=table_name)
        op.drop_table(table_name)

    op.drop_index("ix_channel_memories_channel_created_at", table_name="channel_memories")
    op.drop_index(op.f("ix_channel_memories_channel_id"), table_name="channel_memories")
    op.drop_table("channel_memories")

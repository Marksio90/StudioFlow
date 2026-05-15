"""add topic research reports for idea-level research output

Revision ID: 20260515_0010
Revises: 20260515_0009
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0010"
down_revision = "20260515_0009"
branch_labels = None
depends_on = None


topic_research_recommendation_enum = sa.Enum(
    "approved",
    "needs_more_research",
    "too_generic",
    "reject",
    name="topicresearchrecommendation",
)


def upgrade() -> None:
    topic_research_recommendation_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "topic_research_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idea_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("search_intent_score", sa.Float(), nullable=False),
        sa.Column("viewer_curiosity_score", sa.Float(), nullable=False),
        sa.Column("emotional_pull_score", sa.Float(), nullable=False),
        sa.Column("evergreen_score", sa.Float(), nullable=False),
        sa.Column("series_potential_score", sa.Float(), nullable=False),
        sa.Column("difficulty_score", sa.Float(), nullable=False),
        sa.Column("evidence_required_score", sa.Float(), nullable=False),
        sa.Column("generic_risk_score", sa.Float(), nullable=False),
        sa.Column("overall_topic_score", sa.Float(), nullable=False),
        sa.Column("recommendation", topic_research_recommendation_enum, nullable=False),
        sa.Column("topic_summary", sa.Text(), nullable=False),
        sa.Column("target_viewer", sa.Text(), nullable=False),
        sa.Column("viewer_problem", sa.Text(), nullable=False),
        sa.Column("viewer_promise", sa.Text(), nullable=False),
        sa.Column("curiosity_drivers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("possible_content_angles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("risk_of_generic_content", sa.Text(), nullable=False),
        sa.Column("recommended_next_step", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["video_ideas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topic_research_reports_idea_id", "topic_research_reports", ["idea_id"], unique=False)
    op.create_index(
        "ix_topic_research_reports_idea_id_created_at_desc",
        "topic_research_reports",
        ["idea_id", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_topic_research_reports_idea_id_created_at_desc", table_name="topic_research_reports")
    op.drop_index("ix_topic_research_reports_idea_id", table_name="topic_research_reports")
    op.drop_table("topic_research_reports")
    topic_research_recommendation_enum.drop(op.get_bind(), checkfirst=True)

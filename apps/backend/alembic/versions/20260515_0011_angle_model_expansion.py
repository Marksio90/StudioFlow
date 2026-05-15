"""expand angles with idea linkage, structured fields, and approval audit metadata

Revision ID: 20260515_0011
Revises: 20260515_0010
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0011"
down_revision = "20260515_0010"
branch_labels = None
depends_on = None


SCORE_CHECKS = [
    ("ck_angles_originality_score_range", "originality_score >= 0 AND originality_score <= 10"),
    ("ck_angles_differentiation_score_range", "differentiation_score >= 0 AND differentiation_score <= 10"),
    (
        "ck_angles_viewer_transformation_score_range",
        "viewer_transformation_score >= 0 AND viewer_transformation_score <= 10",
    ),
    ("ck_angles_evidence_strength_score_range", "evidence_strength_score >= 0 AND evidence_strength_score <= 10"),
    ("ck_angles_human_judgment_score_range", "human_judgment_score >= 0 AND human_judgment_score <= 10"),
    ("ck_angles_generic_content_risk_range", "generic_content_risk >= 0 AND generic_content_risk <= 10"),
    ("ck_angles_overall_angle_score_range", "overall_angle_score >= 0 AND overall_angle_score <= 10"),
]


def upgrade() -> None:
    op.add_column("angles", sa.Column("idea_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("angles", sa.Column("main_insight", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("viewer_transformation", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("contradiction", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("emotional_pull", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("differentiator", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("evidence_notes", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("human_judgment", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("originality_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("angles", sa.Column("differentiation_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("angles", sa.Column("viewer_transformation_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("angles", sa.Column("evidence_strength_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("angles", sa.Column("human_judgment_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("angles", sa.Column("generic_content_risk", sa.Float(), nullable=False, server_default="0"))
    op.add_column("angles", sa.Column("overall_angle_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("angles", sa.Column("recommendation", sa.Text(), nullable=False, server_default=""))
    op.add_column("angles", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("angles", sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("angles", sa.Column("override_reason", sa.Text(), nullable=True))
    op.add_column("angles", sa.Column("override_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("angles", sa.Column("override_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE angles SET idea_id = NULL")

    op.create_foreign_key("fk_angles_idea_id_video_ideas", "angles", "video_ideas", ["idea_id"], ["id"])
    op.create_foreign_key("fk_angles_approved_by_users", "angles", "users", ["approved_by"], ["id"])
    op.create_foreign_key("fk_angles_override_by_users", "angles", "users", ["override_by"], ["id"])

    op.create_index("ix_angles_idea_id", "angles", ["idea_id"], unique=False)
    op.create_index("ix_angles_idea_created_at", "angles", ["idea_id", "created_at"], unique=False)
    op.create_index("ix_angles_approval_state", "angles", ["approved_at", "override_at"], unique=False)

    for name, condition in SCORE_CHECKS:
        op.create_check_constraint(name, "angles", condition)


def downgrade() -> None:
    for name, _ in SCORE_CHECKS:
        op.drop_constraint(name, "angles", type_="check")

    op.drop_index("ix_angles_approval_state", table_name="angles")
    op.drop_index("ix_angles_idea_created_at", table_name="angles")
    op.drop_index("ix_angles_idea_id", table_name="angles")

    op.drop_constraint("fk_angles_override_by_users", "angles", type_="foreignkey")
    op.drop_constraint("fk_angles_approved_by_users", "angles", type_="foreignkey")
    op.drop_constraint("fk_angles_idea_id_video_ideas", "angles", type_="foreignkey")

    for col in [
        "override_at",
        "override_by",
        "override_reason",
        "approved_by",
        "approved_at",
        "recommendation",
        "overall_angle_score",
        "generic_content_risk",
        "human_judgment_score",
        "evidence_strength_score",
        "viewer_transformation_score",
        "differentiation_score",
        "originality_score",
        "human_judgment",
        "evidence_notes",
        "differentiator",
        "emotional_pull",
        "contradiction",
        "viewer_transformation",
        "main_insight",
        "idea_id",
    ]:
        op.drop_column("angles", col)

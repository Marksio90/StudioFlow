"""publishing plan package completeness fields

Revision ID: 20260515_0004
Revises: 20260515_0003
Create Date: 2026-05-15 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260515_0004"
down_revision = "20260515_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("publishing_plans", sa.Column("selected_title_variant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("publishing_plans", sa.Column("selected_thumbnail_concept_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("publishing_plans", sa.Column("final_description_snapshot", sa.Text(), nullable=True))
    op.add_column("publishing_plans", sa.Column("final_tags_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("publishing_plans", sa.Column("compliance_report_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("publishing_plans", sa.Column("asset_bundle_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_foreign_key(
        "fk_publishing_plans_selected_title_variant_id",
        "publishing_plans",
        "title_variants",
        ["selected_title_variant_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_publishing_plans_selected_thumbnail_concept_id",
        "publishing_plans",
        "thumbnail_concepts",
        ["selected_thumbnail_concept_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_publishing_plans_compliance_report_id",
        "publishing_plans",
        "compliance_reports",
        ["compliance_report_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_publishing_plans_compliance_report_id", "publishing_plans", type_="foreignkey")
    op.drop_constraint("fk_publishing_plans_selected_thumbnail_concept_id", "publishing_plans", type_="foreignkey")
    op.drop_constraint("fk_publishing_plans_selected_title_variant_id", "publishing_plans", type_="foreignkey")

    op.drop_column("publishing_plans", "asset_bundle_metadata")
    op.drop_column("publishing_plans", "compliance_report_id")
    op.drop_column("publishing_plans", "final_tags_snapshot")
    op.drop_column("publishing_plans", "final_description_snapshot")
    op.drop_column("publishing_plans", "selected_thumbnail_concept_id")
    op.drop_column("publishing_plans", "selected_title_variant_id")

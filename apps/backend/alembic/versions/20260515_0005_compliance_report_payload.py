"""add compliance report payload

Revision ID: 20260515_0005
Revises: 20260515_0004
Create Date: 2026-05-15 12:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260515_0005"
down_revision = "20260515_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "compliance_reports",
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE compliance_reports
            SET payload = (
                COALESCE(findings::jsonb, '{}'::jsonb)
                || jsonb_build_object(
                    'score', CASE
                        WHEN risk_level = 'blocked' THEN 0
                        WHEN risk_level = 'high' THEN 40
                        WHEN risk_level = 'medium' THEN 70
                        ELSE 100
                    END,
                    'requires_ai_disclosure', false,
                    'disclosure_decision_missing', false,
                    'ai_disclosure_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'inauthentic_content_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'repetitive_content_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'copyright_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'sensitive_claims_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'clickbait_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'asset_license_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'synthetic_media_realism_risk', CASE WHEN risk_level IN ('high', 'blocked') THEN 'high' WHEN risk_level = 'medium' THEN 'medium' ELSE 'low' END,
                    'reasons', COALESCE(findings::jsonb -> 'reasons', '[]'::jsonb),
                    'recommendations', COALESCE(findings::jsonb -> 'recommendations', '[]'::jsonb),
                    'blocking_issues', CASE
                        WHEN risk_level = 'blocked' THEN '[]'::jsonb || '"risk_level_blocked"'::jsonb
                        ELSE COALESCE(findings::jsonb -> 'blocking_issues', '[]'::jsonb)
                    END
                )
            )
            """
        )
    )

    op.execute(sa.text("UPDATE compliance_reports SET payload = '{}'::jsonb WHERE payload IS NULL"))
    op.alter_column("compliance_reports", "payload", nullable=False)


def downgrade() -> None:
    op.drop_column("compliance_reports", "payload")

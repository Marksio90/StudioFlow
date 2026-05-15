"""add channel profile fields and tenant-scoped slug uniqueness

Revision ID: 20260515_0007
Revises: 20260515_0006
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260515_0007'
down_revision = '20260515_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('channels', sa.Column('slug', sa.String(length=255), nullable=True))
    op.add_column('channels', sa.Column('description', sa.Text(), nullable=False, server_default=''))
    op.add_column('channels', sa.Column('niche', sa.String(length=255), nullable=False, server_default=''))
    op.add_column('channels', sa.Column('language', sa.String(length=32), nullable=False, server_default='en'))
    op.add_column('channels', sa.Column('target_audience', sa.Text(), nullable=False, server_default=''))
    op.add_column('channels', sa.Column('tone_of_voice', sa.Text(), nullable=False, server_default=''))
    op.add_column('channels', sa.Column('content_pillars', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column('channels', sa.Column('brand_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column('channels', sa.Column('status', sa.String(length=32), nullable=False, server_default='active'))

    # Backfill slug deterministically from channel name, with stable tenant-local dedupe.
    op.execute(
        """
        WITH base AS (
            SELECT
                id,
                organization_id,
                workspace_id,
                CASE
                    WHEN trim(regexp_replace(lower(coalesce(name, '')), '[^a-z0-9]+', '-', 'g'), '-') = ''
                    THEN 'channel'
                    ELSE trim(regexp_replace(lower(coalesce(name, '')), '[^a-z0-9]+', '-', 'g'), '-')
                END AS base_slug
            FROM channels
        ), ranked AS (
            SELECT
                id,
                base_slug,
                row_number() OVER (
                    PARTITION BY organization_id, workspace_id, base_slug
                    ORDER BY id
                ) AS dup_no
            FROM base
        )
        UPDATE channels c
        SET slug = CASE
            WHEN ranked.dup_no = 1 THEN ranked.base_slug
            ELSE ranked.base_slug || '-' || ranked.dup_no
        END
        FROM ranked
        WHERE ranked.id = c.id;
        """
    )

    op.alter_column('channels', 'slug', nullable=False)
    op.create_unique_constraint('uq_channels_org_workspace_slug', 'channels', ['organization_id', 'workspace_id', 'slug'])
    op.create_index('ix_channels_workspace_slug', 'channels', ['workspace_id', 'slug'], unique=False)

    op.alter_column('channels', 'description', server_default=None)
    op.alter_column('channels', 'niche', server_default=None)
    op.alter_column('channels', 'language', server_default=None)
    op.alter_column('channels', 'target_audience', server_default=None)
    op.alter_column('channels', 'tone_of_voice', server_default=None)
    op.alter_column('channels', 'content_pillars', server_default=None)
    op.alter_column('channels', 'brand_rules', server_default=None)
    op.alter_column('channels', 'status', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_channels_workspace_slug', table_name='channels')
    op.drop_constraint('uq_channels_org_workspace_slug', 'channels', type_='unique')

    op.drop_column('channels', 'status')
    op.drop_column('channels', 'brand_rules')
    op.drop_column('channels', 'content_pillars')
    op.drop_column('channels', 'tone_of_voice')
    op.drop_column('channels', 'target_audience')
    op.drop_column('channels', 'language')
    op.drop_column('channels', 'niche')
    op.drop_column('channels', 'description')
    op.drop_column('channels', 'slug')

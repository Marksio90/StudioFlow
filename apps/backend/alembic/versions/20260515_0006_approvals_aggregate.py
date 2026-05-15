"""add approvals aggregate table

Revision ID: 20260515_0006
Revises: 20260515_0005
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260515_0006'
down_revision = '20260515_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'approvals',
        sa.Column('video_project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('video_projects.id'), primary_key=True),
        sa.Column('status', sa.Enum('awaiting_review', 'approved', 'rejected', 'needs_changes', name='approvalstatus'), nullable=False, server_default='awaiting_review'),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('latest_comment', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('approvals')

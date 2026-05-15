"""expand llm_calls with observability and safe audit fields

Revision ID: 20260515_0009
Revises: 20260515_0008
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260515_0009"
down_revision = "20260515_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("llm_calls", sa.Column("provider", sa.String(length=64), nullable=False, server_default="unknown"))
    op.add_column("llm_calls", sa.Column("prompt_template_name", sa.String(length=255), nullable=True))
    op.add_column("llm_calls", sa.Column("prompt_template_version", sa.String(length=64), nullable=True))
    op.add_column("llm_calls", sa.Column("input_hash", sa.String(length=128), nullable=True))
    op.add_column("llm_calls", sa.Column("input_preview", sa.String(length=512), nullable=True))
    op.add_column("llm_calls", sa.Column("output_hash", sa.String(length=128), nullable=True))
    op.add_column("llm_calls", sa.Column("output_preview", sa.String(length=512), nullable=True))
    op.add_column("llm_calls", sa.Column("total_tokens", sa.Integer(), nullable=True))
    op.add_column("llm_calls", sa.Column("estimated_cost_usd", sa.Float(), nullable=True))
    op.add_column("llm_calls", sa.Column("latency_ms", sa.Integer(), nullable=True))
    op.add_column("llm_calls", sa.Column("status", sa.String(length=32), nullable=False, server_default="success"))
    op.add_column("llm_calls", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("llm_calls", sa.Column("trace_id", sa.String(length=128), nullable=True))
    op.add_column("llm_calls", sa.Column("request_id", sa.String(length=128), nullable=True))
    op.add_column("llm_calls", sa.Column("related_entity_type", sa.String(length=128), nullable=True))
    op.add_column("llm_calls", sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.alter_column("llm_calls", "prompt_tokens", existing_type=sa.Integer(), nullable=True)
    op.alter_column("llm_calls", "completion_tokens", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column("llm_calls", "completion_tokens", existing_type=sa.Integer(), nullable=False)
    op.alter_column("llm_calls", "prompt_tokens", existing_type=sa.Integer(), nullable=False)

    op.drop_column("llm_calls", "related_entity_id")
    op.drop_column("llm_calls", "related_entity_type")
    op.drop_column("llm_calls", "request_id")
    op.drop_column("llm_calls", "trace_id")
    op.drop_column("llm_calls", "error_message")
    op.drop_column("llm_calls", "status")
    op.drop_column("llm_calls", "latency_ms")
    op.drop_column("llm_calls", "estimated_cost_usd")
    op.drop_column("llm_calls", "total_tokens")
    op.drop_column("llm_calls", "output_preview")
    op.drop_column("llm_calls", "output_hash")
    op.drop_column("llm_calls", "input_preview")
    op.drop_column("llm_calls", "input_hash")
    op.drop_column("llm_calls", "prompt_template_version")
    op.drop_column("llm_calls", "prompt_template_name")
    op.drop_column("llm_calls", "provider")

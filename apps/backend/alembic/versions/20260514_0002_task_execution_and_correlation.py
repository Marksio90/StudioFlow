"""task execution tracking and correlation ids

Revision ID: 20260514_0002
Revises: 20260514_0001
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260514_0002"
down_revision = "20260514_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workflow_events", sa.Column("correlation_id", sa.String(length=128), nullable=True))
    op.create_index(op.f("ix_workflow_events_correlation_id"), "workflow_events", ["correlation_id"], unique=False)

    op.create_table(
        "task_executions",
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_name", sa.String(length=128), nullable=False),
        sa.Column("business_key", sa.String(length=255), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_key"),
    )
    op.create_index(op.f("ix_task_executions_workflow_run_id"), "task_executions", ["workflow_run_id"], unique=False)
    op.create_index(op.f("ix_task_executions_idempotency_key"), "task_executions", ["idempotency_key"], unique=False)
    op.create_index(op.f("ix_task_executions_status"), "task_executions", ["status"], unique=False)

    op.create_table(
        "task_attempts",
        sa.Column("task_execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_execution_id"], ["task_executions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_attempts_task_execution_id"), "task_attempts", ["task_execution_id"], unique=False)
    op.create_index(op.f("ix_task_attempts_status"), "task_attempts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_attempts_status"), table_name="task_attempts")
    op.drop_index(op.f("ix_task_attempts_task_execution_id"), table_name="task_attempts")
    op.drop_table("task_attempts")

    op.drop_index(op.f("ix_task_executions_status"), table_name="task_executions")
    op.drop_index(op.f("ix_task_executions_idempotency_key"), table_name="task_executions")
    op.drop_index(op.f("ix_task_executions_workflow_run_id"), table_name="task_executions")
    op.drop_table("task_executions")

    op.drop_index(op.f("ix_workflow_events_correlation_id"), table_name="workflow_events")
    op.drop_column("workflow_events", "correlation_id")

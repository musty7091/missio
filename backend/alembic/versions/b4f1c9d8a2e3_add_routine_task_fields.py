"""add routine task fields

Revision ID: b4f1c9d8a2e3
Revises: 7f15391ac7c5
Create Date: 2026-05-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b4f1c9d8a2e3"
down_revision = "7f15391ac7c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add routine task fields to task and task_template tables."""

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.add_column(
            sa.Column(
                "template_id",
                sa.Integer(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "task_type",
                sa.String(length=30),
                nullable=False,
                server_default="extra",
            )
        )
        batch_op.add_column(
            sa.Column(
                "task_date",
                sa.Date(),
                nullable=False,
                server_default=sa.text("CURRENT_DATE"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "assigned_at_utc",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "fk_tasks_template_id_task_templates",
            "task_templates",
            ["template_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_tasks_template_id",
            ["template_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_tasks_task_type",
            ["task_type"],
            unique=False,
        )
        batch_op.create_index(
            "ix_tasks_task_date",
            ["task_date"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uq_tasks_business_template_user_date",
            [
                "business_id",
                "template_id",
                "assigned_to_user_id",
                "task_date",
            ],
        )

    with op.batch_alter_table("task_templates") as batch_op:
        batch_op.add_column(
            sa.Column(
                "assigned_to_user_id",
                sa.Integer(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "created_by_user_id",
                sa.Integer(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "recurrence_type",
                sa.String(length=30),
                nullable=False,
                server_default="daily",
            )
        )
        batch_op.add_column(
            sa.Column(
                "default_due_time_local",
                sa.Time(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at_utc",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )
        batch_op.create_foreign_key(
            "fk_task_templates_assigned_to_user_id_users",
            "users",
            ["assigned_to_user_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_task_templates_created_by_user_id_users",
            "users",
            ["created_by_user_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_task_templates_assigned_to_user_id",
            ["assigned_to_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_task_templates_created_by_user_id",
            ["created_by_user_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_task_templates_recurrence_type",
            ["recurrence_type"],
            unique=False,
        )


def downgrade() -> None:
    """Remove routine task fields from task and task_template tables."""

    with op.batch_alter_table("task_templates") as batch_op:
        batch_op.drop_index("ix_task_templates_recurrence_type")
        batch_op.drop_index("ix_task_templates_created_by_user_id")
        batch_op.drop_index("ix_task_templates_assigned_to_user_id")
        batch_op.drop_constraint(
            "fk_task_templates_created_by_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_task_templates_assigned_to_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("updated_at_utc")
        batch_op.drop_column("default_due_time_local")
        batch_op.drop_column("recurrence_type")
        batch_op.drop_column("created_by_user_id")
        batch_op.drop_column("assigned_to_user_id")

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_constraint(
            "uq_tasks_business_template_user_date",
            type_="unique",
        )
        batch_op.drop_index("ix_tasks_task_date")
        batch_op.drop_index("ix_tasks_task_type")
        batch_op.drop_index("ix_tasks_template_id")
        batch_op.drop_constraint(
            "fk_tasks_template_id_task_templates",
            type_="foreignkey",
        )
        batch_op.drop_column("assigned_at_utc")
        batch_op.drop_column("task_date")
        batch_op.drop_column("task_type")
        batch_op.drop_column("template_id")
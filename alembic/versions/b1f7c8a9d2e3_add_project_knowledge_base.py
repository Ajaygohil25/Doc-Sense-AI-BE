"""add project knowledge base

Revision ID: b1f7c8a9d2e3
Revises: 8f2a7c4d1b90
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1f7c8a9d2e3"
down_revision: Union[str, Sequence[str], None] = "8f2a7c4d1b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_owner_id"), "project", ["owner_id"], unique=False)

    op.add_column("file_upload", sa.Column("project_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_file_upload_project_id"), "file_upload", ["project_id"], unique=False)
    op.create_foreign_key(
        "fk_file_upload_project_id_project",
        "file_upload",
        "project",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.alter_column("chat_room", "file_id", existing_type=sa.UUID(), nullable=True)
    op.add_column("chat_room", sa.Column("project_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_chat_room_project_id"), "chat_room", ["project_id"], unique=False)
    op.create_foreign_key(
        "fk_chat_room_project_id_project",
        "chat_room",
        "project",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_chat_room_single_scope",
        "chat_room",
        "(file_id IS NOT NULL AND project_id IS NULL) OR "
        "(file_id IS NULL AND project_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_chat_room_single_scope", "chat_room", type_="check")
    op.drop_constraint("fk_chat_room_project_id_project", "chat_room", type_="foreignkey")
    op.drop_index(op.f("ix_chat_room_project_id"), table_name="chat_room")
    op.drop_column("chat_room", "project_id")
    op.alter_column("chat_room", "file_id", existing_type=sa.UUID(), nullable=False)

    op.drop_constraint("fk_file_upload_project_id_project", "file_upload", type_="foreignkey")
    op.drop_index(op.f("ix_file_upload_project_id"), table_name="file_upload")
    op.drop_column("file_upload", "project_id")

    op.drop_index(op.f("ix_project_owner_id"), table_name="project")
    op.drop_table("project")

"""add name to chat room

Revision ID: 8f2a7c4d1b90
Revises: 44b74b279567
Create Date: 2026-06-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f2a7c4d1b90"
down_revision: Union[str, Sequence[str], None] = "44b74b279567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_room", sa.Column("name", sa.String(length=120), nullable=True))
    op.execute("UPDATE chat_room SET name = 'Default chat' WHERE name IS NULL OR name = ''")
    op.alter_column("chat_room", "name", nullable=False)


def downgrade() -> None:
    op.drop_column("chat_room", "name")

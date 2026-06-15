from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "44b74b279567"
down_revision: Union[str, None] = "5deec004550e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


chat_sender_enum = sa.Enum(
    "USER",
    "ASSISTANT",
    name="chat_sender_enum",
)


def upgrade() -> None:
    bind = op.get_bind()

    chat_sender_enum.create(bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE chat_message
        ALTER COLUMN sender TYPE chat_sender_enum
        USING sender::chat_sender_enum
        """
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.execute(
        """
        ALTER TABLE chat_message
        ALTER COLUMN sender TYPE VARCHAR
        USING sender::VARCHAR
        """
    )

    chat_sender_enum.drop(bind, checkfirst=True)
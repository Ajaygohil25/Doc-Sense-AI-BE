from uuid import uuid4

from sqlalchemy import Column, UUID, ForeignKey, Text, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base_declarative_model import BaseDeclarativeModel

class ChatMessage(Base, BaseDeclarativeModel):
    __tablename__ = "chat_message"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_room.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    sender = Column(String, nullable=False)
    # user / assistant / system

    message = Column(Text, nullable=False)

    # relationship
    chat_room = relationship("ChatRoom", back_populates="messages")
from uuid import uuid4

from sqlalchemy import Column, UUID, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base_declarative_model import BaseDeclarativeModel
from app.models.chat_message_model import ChatMessage


class ChatRoom(Base, BaseDeclarativeModel):
    __tablename__ = "chat_room"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("file_upload.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # relationship
    file = relationship("FileUploadModel", back_populates="chat_room")
    messages = relationship("ChatMessage", back_populates="chat_room")




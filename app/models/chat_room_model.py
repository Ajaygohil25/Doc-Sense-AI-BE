from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, UUID, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base_declarative_model import BaseDeclarativeModel
from app.models.chat_message_model import ChatMessage


class ChatRoom(Base, BaseDeclarativeModel):
    __tablename__ = "chat_room"
    __table_args__ = (
        CheckConstraint(
            "(file_id IS NOT NULL AND project_id IS NULL) OR "
            "(file_id IS NULL AND project_id IS NOT NULL)",
            name="ck_chat_room_single_scope",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(120), nullable=False, default="Default chat")

    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("file_upload.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # relationship
    file = relationship("FileUploadModel", back_populates="chat_room")
    project = relationship("ProjectModel", back_populates="chat_rooms")
    messages = relationship("ChatMessage", back_populates="chat_room")


from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base_declarative_model import BaseDeclarativeModel


class ProjectModel(Base, BaseDeclarativeModel):
    __tablename__ = "project"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    owner = relationship("User", back_populates="projects")
    files = relationship("FileUploadModel", back_populates="project", cascade="all, delete-orphan")
    chat_rooms = relationship("ChatRoom", back_populates="project", cascade="all, delete-orphan")

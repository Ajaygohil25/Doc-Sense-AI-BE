from uuid import uuid4
from sqlalchemy import Column, String, Boolean, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base_declarative_model import BaseDeclarativeModel


class FileUploadModel(Base, BaseDeclarativeModel):
    __tablename__ = "file_upload"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default='pending')
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_on_s3_bucket = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="file_upload")

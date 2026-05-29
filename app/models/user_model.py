from uuid import uuid4
from sqlalchemy import Column, String, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base_declarative_model import BaseDeclarativeModel
from app.models import password_reset_token_model
from app.models.file_upload_model import FileUploadModel

class User(Base, BaseDeclarativeModel):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)

    #relationship
    password_reset_tokens = relationship("PasswordResetTokenModel", back_populates="user")
    file_upload = relationship("FileUploadModel", back_populates="user")

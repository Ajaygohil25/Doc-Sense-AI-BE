from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy import Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base_declarative_model import BaseDeclarativeModel


class PasswordResetTokenModel(Base, BaseDeclarativeModel):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False, index=True)  # store HMAC hex
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)


    user = relationship("User", back_populates="password_reset_tokens")
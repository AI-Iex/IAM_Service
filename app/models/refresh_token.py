from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    jti = Column(UUID(as_uuid = True), unique = True, index = True, nullable = False)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id", ondelete = "CASCADE"), index = True, nullable = False)
    hashed_token = Column(String(128), nullable = False)
    issued_at = Column(DateTime(timezone = True), server_default = func.now())
    expires_at = Column(DateTime(timezone = True), nullable = False)
    revoked = Column(Boolean, default = False)
    replaced_by = Column(UUID(as_uuid=True), nullable = True)
    last_used_at = Column(DateTime(timezone = True), nullable = True)
    ip = Column(String(45), nullable = True)
    user_agent = Column(Text, nullable = True)

    def __repr__(self):
        return f"<RefreshToken(id='{self.id}', user_id='{self.user_id}', revoked={self.revoked})>"
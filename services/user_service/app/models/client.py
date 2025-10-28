from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    client_id = Column(UUID(as_uuid = True), unique = True, index = True, nullable = False)
    name = Column(String(255), nullable = True)
    hashed_secret = Column(String(255), nullable = False)
    is_active = Column(Boolean, default = True)
    scopes = Column(Text, nullable = True)
    created_at = Column(DateTime(timezone = True), server_default = func.now())

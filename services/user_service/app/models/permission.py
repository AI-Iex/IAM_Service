from sqlalchemy import Column, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key = True, default = uuid.uuid4, index = True)
    name = Column(String, nullable = False, index = True)
    service_name = Column(String, nullable=False, index=True)
    description = Column(String, nullable = True)
    created_at = Column(DateTime(timezone = True), server_default = func.now(), nullable = False)
    updated_at = Column(DateTime(timezone = True), onupdate = func.now())

    roles = relationship("Role", secondary = "role_permissions", back_populates = "permissions", lazy = "selectin")

    __table_args__ = (
        UniqueConstraint('name', 'service_name', name='uq_permissions_name_service'),
    )

    def __repr__(self):
        return f"<Permission name={self.name}>"

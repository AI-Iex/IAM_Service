from sqlalchemy import Column, DateTime, Integer, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", secondary=UserRole.__table__, back_populates="roles", lazy="selectin")

    permissions = relationship(
        "Permission", secondary=RolePermission.__table__, back_populates="roles", lazy="selectin"
    )

    def __repr__(self):
        return f"<Role(id='{self.id}', name='{self.name}')>"

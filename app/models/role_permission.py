from sqlalchemy import Column, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from app.db.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),)

    def __repr__(self):
        return f"<RolePermission role_id={self.role_id} permission_id={self.permission_id}>"

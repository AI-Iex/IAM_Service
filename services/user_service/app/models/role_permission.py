from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid = True), ForeignKey("roles.id", ondelete = "CASCADE"), primary_key = True),
    Column("permission_id", UUID(as_uuid = True), ForeignKey("permissions.id", ondelete = "CASCADE"), primary_key = True),
)

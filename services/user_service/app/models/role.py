from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.user_role import user_roles

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4, index = True)
    name = Column(String, nullable = False, unique = True)

    users = relationship("User", secondary = user_roles, back_populates = "roles", lazy = "joined")

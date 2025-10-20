from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.user_role import user_roles   

class User(Base):
     __tablename__ = "users"

     id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4, index = True)
     full_name = Column(String, nullable = False, unique = False, index = True)
     email = Column(String, nullable = False, unique = True, index = True)
     hashed_password  = Column(String, nullable = False)

     is_active = Column(Boolean, default = True)
     is_superuser = Column(Boolean, default = False)

     roles = relationship("Role", secondary = user_roles, back_populates = "users", lazy = "joined")

     created_at = Column(DateTime(timezone = True), server_default = func.now())
     last_login = Column(DateTime(timezone = True), nullable = True)

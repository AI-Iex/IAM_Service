from sqlalchemy import Table, Column, Integer, ForeignKey

from app.db.base import Base 

user_roles = Table(
    "user_roles",
    Base.metadata,  # ← Esto es obligatorio para que la tabla exista en la metadata
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

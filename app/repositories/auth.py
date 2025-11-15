from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.models.user import User
from app.models.client import Client
from app.models.role import Role
from app.models.permission import Permission
from app.repositories.interfaces.auth import IAuthRepository
from typing import Optional
from app.core.exceptions import RepositoryError

class AuthRepository(IAuthRepository):
    
    async def get_user_for_auth(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        
        """Retrieve user with roles and permissions for authentication."""

        try:

            query = (
                select(User)
                .options(
                    selectinload(User.roles).selectinload(Role.permissions)
                )
                .where(User.id == user_id)
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error reading user by ID: {str(e)}") from e
    
    async def get_client_for_auth(self, db: AsyncSession, client_id: UUID) -> Optional[Client]:
        
        """Retrieve active client for authentication. """

        try:

            query = select(Client).where(Client.id == client_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        
        except Exception as e:
            raise RepositoryError(f"Error reading client by ID: {str(e)}") from e
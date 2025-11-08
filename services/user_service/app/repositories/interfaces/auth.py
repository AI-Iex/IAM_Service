# app/repositories/interfaces/auth.py
from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional
from app.models.user import User
from app.models.client import Client
from sqlalchemy.ext.asyncio import AsyncSession

class IAuthRepository(ABC):

    """Repository interface for authentication-related operations."""
    
    @abstractmethod
    async def get_user_for_auth(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Retrieve user with roles and permissions for authentication. """
        pass
    
    @abstractmethod
    async def get_client_for_auth(self, db: AsyncSession, client_id: UUID) -> Optional[Client]:
        """Retrieve client with permissions for authentication. """
        pass


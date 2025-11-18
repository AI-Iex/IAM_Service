from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from abc import ABC, abstractmethod
from app.models.refresh_token import RefreshToken


class IRefreshTokenRepository(ABC):

    @abstractmethod
    async def create_refresh_token(
        self,
        db: AsyncSession,
        jti: UUID,
        user_id: UUID,
        hashed_token: str,
        expires_at: datetime,
        user_agent: Optional[str],
        client_ip: Optional[str],
    ) -> RefreshToken:
        """Create and persist a RefreshToken row returning the created object"""

    @abstractmethod
    async def get_refresh_token_by_jti(self, db: AsyncSession, jti: UUID) -> RefreshToken | None:
        """Retrieve refresh token row by its jti"""

    @abstractmethod
    async def get_by_token_hash(self, db: AsyncSession, token_hash: str) -> RefreshToken | None:
        """Lookup a refresh token by its hashed token"""

    @abstractmethod
    async def revoke_refresh_token(self, db: AsyncSession, jti: UUID) -> None:
        """Mark a refresh token revoked by jti"""

    @abstractmethod
    async def mark_refresh_token_replaced(self, db: AsyncSession, old_jti: UUID, new_jti: UUID) -> None:
        """Mark old token revoked and set replaced_by to new jti"""

    @abstractmethod
    async def revoke_all_refresh_tokens_for_user(self, db: AsyncSession, user_id: UUID) -> None:
        """Revoke all refresh tokens for a given user"""

    @abstractmethod
    async def update_refresh_token_last_used(
        self, db: AsyncSession, jti: UUID, used_at: Optional[datetime] = None
    ) -> None:
        """Update last_used_at for a refresh token"""

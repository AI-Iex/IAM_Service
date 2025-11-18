from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone

from app.repositories.interfaces.refresh_token import IRefreshTokenRepository
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository(IRefreshTokenRepository):

    async def create_refresh_token(
        self,
        db: AsyncSession,
        jti: UUID,
        user_id: UUID,
        hashed_token: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        client_ip: Optional[str] = None,
    ):
        """Create and persist a RefreshToken row returning the created object"""

        rt = RefreshToken(
            jti=jti,
            user_id=user_id,
            hashed_token=hashed_token,
            expires_at=expires_at,
            ip=client_ip,
            user_agent=user_agent,
        )

        db.add(rt)
        await db.flush()
        await db.refresh(rt)
        return rt

    async def get_by_token_hash(self, db: AsyncSession, token_hash: str):
        """Retrieve refresh token row by its hashed token"""

        q = select(RefreshToken).where(RefreshToken.hashed_token == token_hash)
        res = await db.execute(q)
        return res.scalars().first()

    async def get_refresh_token_by_jti(self, db: AsyncSession, jti: UUID):
        """Retrieve refresh token row by its jti"""

        q = select(RefreshToken).where(RefreshToken.jti == jti)
        res = await db.execute(q)
        return res.scalars().first()

    async def revoke_refresh_token(self, db: AsyncSession, jti: UUID):
        """Mark a refresh token revoked by jti"""

        q = update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True)
        await db.execute(q)
        await db.flush()

    async def mark_refresh_token_replaced(self, db: AsyncSession, old_jti: UUID, new_jti: UUID):
        """Mark old token revoked and set replaced_by to new jti"""

        q = update(RefreshToken).where(RefreshToken.jti == old_jti).values(revoked=True, replaced_by=new_jti)
        await db.execute(q)
        await db.flush()

    async def revoke_all_refresh_tokens_for_user(self, db: AsyncSession, user_id: UUID):
        """Revoke all refresh tokens for a given user"""

        q = update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        await db.execute(q)
        await db.flush()

    async def update_refresh_token_last_used(self, db: AsyncSession, jti: UUID, used_at: datetime = None):
        """Update last_used_at for a refresh token"""

        if used_at is None:
            used_at = datetime.now(timezone.utc)
        q = update(RefreshToken).where(RefreshToken.jti == jti).values(last_used_at=used_at)
        await db.execute(q)
        await db.flush()

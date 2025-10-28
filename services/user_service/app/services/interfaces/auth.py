from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.schemas.auth import TokenPair, UserAndToken
from app.schemas.user import UserRead


class IAuthService(ABC):
    @abstractmethod
    async def login(self, email: str, password: str, ip: Optional[str] = None, user_agent: Optional[str] = None) -> UserAndToken:
        """Autentica un usuario y devuelve user + tokens."""
        pass

    @abstractmethod
    async def refresh_with_refresh_token(self, presented_raw: str, presented_jti: Optional[UUID],
                                         ip: Optional[str] = None, user_agent: Optional[str] = None) -> dict:
        """Rota el refresh token y genera nuevo access."""
        pass

    @abstractmethod
    async def logout(self, user_id: UUID, jti: UUID):
        """Revoca el refresh token del usuario."""
        pass

    @abstractmethod
    async def revoke_refresh_token_by_jti(self, jti: UUID):
        """Revoca el refresh token del usuario."""
        pass

    @abstractmethod
    async def revoke_refresh_token_by_raw(self, raw_token: str):
        """Revoca un refresh token dado el token en bruto (raw)."""
        pass

    @abstractmethod
    async def logout_all_devices(self, user_id: UUID):
        """Revoca todos los refresh tokens del usuario."""
        pass

    @abstractmethod
    async def client_credentials(self, client_id: UUID, client_secret: str) -> dict:
        """Issue an access token for a confidential client (client credentials grant)."""
        pass

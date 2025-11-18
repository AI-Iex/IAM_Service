from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token, AccessTokenType
from app.repositories.interfaces.auth import IAuthRepository
from app.dependencies.services import get_auth_repository, get_uow_factory
from app.db.unit_of_work import UnitOfWorkFactory
from uuid import UUID
from app.schemas.user import UserRead, UserReadDetailed
from app.schemas.client import ClientRead
from app.schemas.auth import Principal
from app.core.config import settings

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.route_prefix}/auth/token")

    
async def get_current_principal_optional(
    token: str = Depends(oauth2_scheme),
    auth_repository: IAuthRepository = Depends(get_auth_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> Optional[Principal]:
    
    """
    Returns None if token is missing/invalid/expired.\n 
    Used for endpoints that allow both authenticated and unauthenticated access like log out.
    """

    # Decode token to check validity, if not provided/invalid/expired return None
    try:
        decode_token(token)
    except Exception:
        return None

    # Get full Principal or return None if invalid
    try:
        return await get_current_principal(token=token, auth_repository=auth_repository, uow_factory=uow_factory)
    except HTTPException:
        return None


async def get_current_principal(
    token: str = Depends(oauth2_scheme),
    auth_repository: IAuthRepository = Depends(get_auth_repository),
    uow_factory: UnitOfWorkFactory = Depends(get_uow_factory),
) -> Principal:
    
    """Resolve the authenticated principal (user or client) from the token. """

    # 0. Decode token
    try:
        payload = decode_token(token)
    except Exception as exc:
        msg = str(exc) or "Invalid token"
        if "expired" in msg.lower():
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Token expired")
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = msg)

    # 1. Get principal type
    token_type = getattr(payload, "type", None)
    if not token_type:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Malformed token")

    # 2. Get the identifier
    sub = payload.sub
    if not sub:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Malformed token")

    # 3. Resolve principal based on type using a unit-of-work (single DB session)
    async with uow_factory() as db:
        
        # User principal handling
        if token_type == AccessTokenType.USER.value:
            try:
                user = await auth_repository.get_user_for_auth(db, UUID(sub))
            except Exception:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

            return Principal(kind=AccessTokenType.USER.value, token=payload, user=user)

        # Client principal handling
        elif token_type == AccessTokenType.CLIENT.value:
            try:
                client = await auth_repository.get_client_for_auth(db, UUID(sub))
            except Exception:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Client not found or inactive")

            return Principal(kind=AccessTokenType.CLIENT.value, token=payload, client=client)

    # Unknown token type (not user or client)
    raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Unknown token type")


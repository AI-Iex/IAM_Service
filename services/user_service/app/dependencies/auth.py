from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token
from app.services.interfaces.user import IUserService
from app.dependencies.services import get_user_service
from uuid import UUID
from app.schemas.user import UserRead
from app.core.config import settings

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v{settings.API_VERSION}/auth/token")
f"/api/v{settings.API_VERSION}"

    
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: IUserService = Depends(get_user_service)
) -> UserRead:

    """ Obtain the current authenticated user based on the provided JWT token """

    try:
        payload = decode_token(token)
        
    except Exception as exc:
        msg = str(exc) or "Invalid token"
        if "expired" in msg.lower():
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Token expired" )
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = msg)

    sub = payload.sub

    if not sub:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Malformed token")

    try:
        user = await user_service.read_by_id(UUID(sub))
        
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    
    return user


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    user_service: IUserService = Depends(get_user_service)
) -> Optional[UserRead]:
    
    """
    Optional version of get_current_user.
    Returns None if token is invalid, expired, or missing
    """

    if not token:
        return None
    
    try:
        return await get_current_user(token, user_service)
    
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise
    except Exception:
        return None

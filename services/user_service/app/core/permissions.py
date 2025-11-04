from fastapi import Depends, HTTPException, status
from functools import wraps
from app.schemas.user import UserRead, UserReadDetailed
from app.dependencies.auth import get_current_user
from app.core.permissions_loader import SERVICE_NAME

# Permission checker dependency
def requires_permission(permission_name: str, return_user: bool = True):

    """Dependency to check if the current user has the required permission."""

    async def checker(current_user: UserReadDetailed = Depends(get_current_user)):
        
        user_permissions = {
            f"{perm.service_name}:{perm.name}"
            for role in current_user.roles
            for perm in getattr(role, "permissions", [])
        }

        # 1. Check if user is superuser
        if current_user.is_superuser:
            return current_user if return_user else None
        
        if current_user.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # 3. Check if user is required to change password
        if current_user.require_password_change:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must change password before proceeding"
            )
        
        
        # 4. Check if user has the required permission
        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail = "Access denied"
            )
        
        return current_user if return_user else None
        
    return Depends(checker)

from fastapi import Depends, HTTPException, status
from functools import wraps
from app.schemas.user import UserRead, UserReadDetailed
from app.schemas.client import ClientRead
from app.dependencies.auth import get_current_principal
from app.schemas.auth import Principal


# Permission checker dependency
def requires_permission(permission_name: str, return_user: bool = True):

    """Dependency to check if the current principal (user or client) has the required permission.

    - If a user principal: check roles -> permissions, superuser bypass, active/require_password_change checks.
    - If a client principal: check client.permissions and is_active.

    Returns either the UserReadDetailed or ClientRead depending on who is calling and `return_user`.
    """

    async def checker(principal: Principal = Depends(get_current_principal)):

        # User principal handling
        if principal.kind == "user" and principal.user:
            current_user: UserReadDetailed = principal.user

            # 1. Check if user is active
            if current_user.is_active is False:
                raise HTTPException(
                    status_code = status.HTTP_403_FORBIDDEN,
                    detail = "User account is inactive"
                )

            # 2. Check if user is required to change password
            if current_user.require_password_change:
                raise HTTPException(
                    status_code = status.HTTP_403_FORBIDDEN,
                    detail = "User must change password before proceeding"
                )
           
            # 3. Check if user is superuser
            if getattr(current_user, "is_superuser", False):
                return current_user if return_user else None

            user_permissions = {
                perm.name
                for role in current_user.roles
                for perm in getattr(role, "permissions", [])
            }

            # 4. Check if required permission is present
            if permission_name not in user_permissions:
                raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Access denied")

            return current_user if return_user else None

        # Client principal handling
        if principal.kind == "client" and principal.client:
            client: ClientRead = principal.client

            # 1. Check if client is active
            if client.is_active is False:
                raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Client account is inactive")

            client_permissions = {p.name for p in (client.permissions or [])}

            # 2. Check if required permission is present
            if permission_name not in client_permissions:
                raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Access denied")

            return principal if return_user else None

        # Fallback: principal missing or malformed
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Unauthenticated")

    return Depends(checker)

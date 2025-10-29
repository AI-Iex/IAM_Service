from fastapi import (
    APIRouter, Depends, status, HTTPException, Response, Request, Cookie, Header
)
from uuid import UUID
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.schemas.user import UserRead, UserRegister
from app.schemas.auth import AuthResponse, TokenPair, TokenPayload, LogoutRequest, UserAndToken
from app.services.user import UserService
from app.services.auth import AuthService
from app.dependencies.services import get_user_service, get_auth_service
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.core.security import decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# Register new user 
@router.post(
    "",
    response_model = UserRead,
    status_code = status.HTTP_201_CREATED,
    summary = "Register a new user",
    description = 
    "Register a new user, necessary fields:\n "
    "- `Email`: The user's email address. **Valid domains**: gmail.com, yahoo.com, outlook.com, hotmail.com, mahle.com\n" \
    "- `Full name`: The user's name and surname. **Min length**: 2 characters\n"
    "- `Password`: The user's password. **Validation**: Min length 8 characters, 1 uppercase, 1 number and 1 special character are required.",
)
async def create_user(
    payload: UserRegister,
    user_service: UserService = Depends(get_user_service)
) -> UserRead:
    return await user_service.register_user(payload)


# Log in
@router.post(
    "/login",
    response_model = UserAndToken,
    status_code = status.HTTP_200_OK,
    summary = "Log in",
    description = 
    "Log in the user and creates a access token, refresh token, and refresh cookie.\n"
    "- `Username`: The **email** address.\n"
    "- `Password`: The user's **password**.",
    response_description = "Returns access and refresh tokens for the authenticated user and user data"
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserAndToken:
    
    # Obtain the User IP and the User device info (agent)
    ip = request.client.host if request and request.client else None
    ua = request.headers.get("user-agent") if request else None

    # Call the auth service to log in
    login_response = await auth_service.login(form_data.username, form_data.password, ip = ip, user_agent = ua)

    token = login_response.token

    # Create and set the refresh token cookie
    response.set_cookie(
        key = "refresh",                                                # Name of the cookie
        value = f"{token.refresh_token}::{token.jti}",                  # Token + JTI for tracking
        httponly = True,                                                # Prevent access via JavaScript for more security
        secure = not settings.is_development,                           # Only over HTTPS
        samesite = "lax",                                               # Protection against CSRF
        max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,       # Expiration time in seconds
        path = "/auth" if settings.is_development else "/auth/refresh"  # Only send to specific routes
    )

    return login_response


# Log out
@router.post(
    "/logout",
    response_model = None,
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Log out",
    description =
    "Log out the user revoking the refresh token.\n"
    "\nSupports both cookie-based and Swagger/manual requests.\n"
    "- For **cookie-based** requests, the `refresh` cookie will be used.\n"
    "- For non-cookie **Swagger/manual** requests, provide the `refresh_token` in the request body or <raw>::<jti> format.",
)
async def logout_user(
    request: Request,
    body: Optional[LogoutRequest] = None,
    current_user: Optional[UserRead] = Depends(get_current_user_optional),
    auth_service: AuthService = Depends(get_auth_service),
    response: Response = None,
):

    refresh_token = None

    # 1️. Try to get the refresh token from cookie
    refresh_cookie = request.cookies.get("refresh")
    
    if refresh_cookie:
        refresh_token = refresh_cookie.split("::", 1)[0]

    # 2️. If no cookie, try to get from body
    elif body and body.refresh_token:
        refresh_token = body.refresh_token

    # 3️. If no refresh token, we can't revoke anything
    if not refresh_token:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    # 4️. Determine jti or use raw token fallback
    jti = None
    raw = None

    # Try to extract jti from cookie
    if refresh_cookie:
        try:
            raw, jti = refresh_cookie.split("::", 1)

        except Exception:
            raw = refresh_cookie

    # Try to extract jti from body
    elif body and body.refresh_token:
        if "::" in body.refresh_token:
            raw, jti = body.refresh_token.split("::", 1)
        else:
            raw = body.refresh_token

    # 5️. If we have a jti we can revoke directly; prefer logout check if current_user available
    if jti:
        
        # This will be the normal case logouts
        if current_user:
            await auth_service.logout(current_user.id, jti)
        
        # Fallback if no current_user (e.g. Swagger with jti)  
        else:
            await auth_service.revoke_refresh_token_by_jti(jti)
    
    # Otherwise, revoke by raw token (e.g. Swagger without jti)
    else:
        
        if not raw:
            return Response(status_code = status.HTTP_400_BAD_REQUEST)
        
        await auth_service.revoke_refresh_token_by_raw(raw)

    # 6️. Clean up cookie if present
    if response:
        response.delete_cookie("refresh")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Log out all devices
@router.post(
    "/logout_all_devices",
    response_model = None,
    status_code = status.HTTP_204_NO_CONTENT,
    summary = "Log out the user from all devices",
    description = 
    "Logs out the user from all logged-in devices by revoking all refresh tokens",
    response_description = None
)
async def logout_all_devices_handler(
    current_user: UserRead = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    response: Response = None
):
    await auth_service.logout_all_devices(current_user.id)
    if response:
        response.delete_cookie("refresh")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Refresh
@router.post(
    "/refresh",
    response_model = UserAndToken,
    status_code = status.HTTP_200_OK,
    summary = "Refresh access token",
    description =
    "Refresh endpoint. Supports multiple input methods to make it easy to use from both browser and API clients:\n"
    "- Cookie: `refresh` sent as cookie by the client automatically.\n"
    "- Header: `Refresh-Token` (raw or raw::jti) and optional `Refresh-JTI`.\n"
    "- Body JSON: { \"refresh_token\": \"<raw>\" } or { \"refresh_token\": \"<raw>::<jti>\" }.\n"
    "Cookie has priority over header, which has priority over body.",
    response_description = "Returns new access and refresh tokens for the user"
)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Header(None, alias = "refresh"),
    refresh_jti: Optional[str] = Header(None, alias = "refresh_jti"),
    body: Optional[LogoutRequest] = None,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserAndToken:

    raw = None
    jti = None
    jti_uuid = None

    refresh_cookie = request.cookies.get("refresh")

    # 1. Get from cookie first if present, with highest priority
    if refresh_cookie:
        try:
            raw, jti = refresh_cookie.split("::", 1)
        except Exception:
            raw = refresh_cookie

    # 2. Get from headers if present, second priority
    elif refresh_token:
        try:
            raw, jti = refresh_token.split("::", 1)
        except Exception:
            raw = refresh_token

        if refresh_jti:
            jti = refresh_jti

    # 3. Get from body if present, last priority
    elif body and getattr(body, "refresh_token", None):
        try:
            raw, jti = body.refresh_token.split("::", 1) 
        except Exception:
            raw = body.refresh_token

    if not raw:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "No refresh token provided")

    # 4. Check jti format if present
    if jti:
        try:
            jti_uuid = UUID(jti)
        except Exception:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Invalid jti format")

    # 5. Obtain the User IP and the User device info (agent)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    # 6. Call the auth service to refresh
    refresh_response = await auth_service.refresh_with_refresh_token(raw, jti_uuid, ip = ip, user_agent = ua)

    token: TokenPair = refresh_response.token

    # 7. Rotate cookie for security
    response.set_cookie(
        key = "refresh",                                                # Name of the cookie
        value = f"{token.refresh_token}::{token.jti}",                  # Token + JTI for tracking
        httponly = True,                                                # Prevent access via JavaScript for more security
        secure = not settings.is_development,                           # Only over HTTPS
        samesite = "lax",                                               # Protection against CSRF
        max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,       # Expiration time in seconds
        path = "/auth" if settings.is_development else "/auth/refresh"  # Only send to specific routes
    )

    return refresh_response


# ⚙️ Token endpoint (for Swagger / dev tools)
@router.post(
    "/token",
    summary="Token endpoint for Swagger or client_credentials flow"
)
async def token_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    request: Request = None,
):
    """
    Token endpoint supporting both client_credentials and password grants.

    - `grant_type=client_credentials`: username=client_id, password=client_secret
    - `grant_type=password`: username=email, password=password
    """
    grant_type = getattr(form_data, "grant_type", None) or "client_credentials"
    ip = request.client.host if request and request.client else None
    ua = request.headers.get("user-agent") if request else None

    try:
        if grant_type == "client_credentials":
            res = await auth_service.client_credentials(form_data.username, form_data.password)
        elif grant_type == "password":
            res = await auth_service.login(form_data.username, form_data.password, ip = ip, user_agent = ua)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported grant_type: {grant_type}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    tokens = res.token
    return {
        "access_token": tokens.access_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in,
        "refresh_token": tokens.refresh_token,
        "jti": getattr(tokens, "jti", None),
    }


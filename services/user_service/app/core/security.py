from passlib.context import CryptContext
from jose import jwt, JWTError
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from typing import Tuple
from uuid import uuid4, UUID
import uuid
import secrets
import hashlib
import hmac
from app.schemas.auth import TokenPair, TokenPayload
from enum import Enum
from app.core.exceptions import DomainError


class AccessTokenType(str, Enum):

    """Enum for access token types."""

    USER = "user"
    CLIENT = "client"


# Password hashing context
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__type="ID"
)


def hash_password(password: str) -> str:
    
    ''' Hash a plain password. '''

    if not password:
        raise ValueError("Password cannot be empty.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:

    ''' Verify a plain password against a hashed password '''

    if not plain_password or not hashed_password:
        raise ValueError("Passwords cannot be empty.")
    return pwd_context.verify(plain_password, hashed_password)



def _create_access_token(payload_extra: dict, expires_minutes: int | None = None) -> TokenPair:

    """Internal helper to create the JWT given payload extras. """

    now = datetime.now(timezone.utc)
    expire_minutes = expires_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    if expire_minutes <= 0:
        raise ValueError(f"Invalid token expiration time: {expire_minutes} minutes")

    expire = now + timedelta(minutes = expire_minutes)

    jti = str(uuid.uuid4())

    # Base payload
    payload = {
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
    }

    payload.update(payload_extra)

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm = settings.JWT_ALGORITHM)

    return TokenPair(
        access_token = token,
        jti = jti,
        expires_in = int((expire - now).total_seconds()),
    )


def create_user_access_token(
    subject: str,
    roles: list | None = None,
    is_superuser: bool = False,
    expires_minutes: int | None = None,
) -> TokenPair:
    
    """Create an access token for a user. """

    payload_extra = {
        "sub": str(subject),
        "type": AccessTokenType.USER.value,
        "roles": roles or [],
        "is_superuser": is_superuser,
    }

    return _create_access_token(payload_extra, expires_minutes = expires_minutes)


def create_client_access_token(
    subject: str,
    permissions: list | None = None,
    expires_minutes: int | None = None,
) -> TokenPair:
    
    """Create an access token for a client. """

    payload_extra = {
        "sub": str(subject),
        "type": AccessTokenType.CLIENT.value,
        "permissions": permissions or [],
        "is_superuser": False,
    }

    return _create_access_token(payload_extra, expires_minutes = expires_minutes)


def decode_token(token: str) -> TokenPayload:

    """ Decode and verify a JWT token. """

    payload_dict = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True}
        )
    
    payload = TokenPayload(**payload_dict)
    
    return payload


def _hmac_sha256_hexdigest(key: str, msg: str) -> str:

    """ Generate HMAC-SHA256 hexdigest. """

    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()


def hash_refresh_token(raw_token: str) -> str:

    """ Hash a raw refresh token. """

    return _hmac_sha256_hexdigest(settings.REFRESH_TOKEN_SECRET, raw_token)


def generate_raw_refresh_token() -> Tuple[str, str]:

    """ Generate a new raw refresh token and its unique identifier (JTI). """

    raw = secrets.token_urlsafe(64)
    jti = str(uuid.uuid4())
    return raw, jti


def refresh_token_expiry_datetime(expires_days: int | None = None) -> datetime:

    """ Calculate refresh token expiry datetime. """

    return datetime.now(timezone.utc) + timedelta(days = expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS)
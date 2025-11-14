from datetime import datetime, timezone, timedelta
import time
import pytest
from jose import jwt, JWTError

from app.core.security import (
    create_user_access_token,
    create_client_access_token,
    decode_token,
)
from app.core.config import settings


def test_create_and_decode_user_token_fields():

    ''' Creating a user access token and decoding it should preserve all fields. '''

    pair = create_user_access_token(subject = "123", permissions = ["a","b"], is_superuser = True, expires_minutes = 5)

    payload = decode_token(pair.access_token)

    assert payload.sub == "123"
    assert payload.type == "user"
    
    raw = jwt.decode(pair.access_token, settings.JWT_SECRET_KEY, algorithms = [settings.JWT_ALGORITHM], options = {"verify_exp": True})

    assert isinstance(raw.get("permissions", []), list)
    assert payload.is_superuser is True
    assert payload.jti == pair.jti
    
    # iat < exp and exp reasonable
    now_ts = int(datetime.now(timezone.utc).timestamp())
    assert payload.iat <= now_ts + 5*60
    assert payload.exp > payload.iat

def test_create_and_decode_client_token():

    ''' Creating a client access token and decoding it should preserve all fields. '''
    
    pair = create_client_access_token(subject = "client-1", permissions = ["x"], expires_minutes = 10)
    payload = decode_token(pair.access_token)

    assert payload.sub == "client-1"
    assert payload.type == "client"
    assert payload.is_superuser is False

def test_jti_uniqueness_between_tokens():

    ''' Verify each created token should have a unique jti. '''

    # Create two tokens for the same subject and ensure jti differs
    
    t1 = create_user_access_token(subject = "1", expires_minutes = 5)
    t2 = create_user_access_token(subject = "1", expires_minutes = 5)

    assert t1.jti != t2.jti

def test_decode_expired_token_raises():

    ''' Decoding an expired token should raise JWTError. '''

    # Craft a token with exp in the past
    now = datetime.now(timezone.utc)
    payload = {"sub": "u", "type": "user", "permissions": [], "is_superuser": False, "iat": int((now - timedelta(hours=1)).timestamp()), "exp": int((now - timedelta(minutes=30)).timestamp()), "jti": "old"}
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(JWTError):
        decode_token(token)

def test_invalid_signature_detection():

    ''' Tampering with a token should cause signature verification to fail. '''

    pair = create_user_access_token(subject = "123", expires_minutes = 5)

    # Tamper token by corrupting the signature part explicitly
    parts = pair.access_token.split(".")
    assert len(parts) == 3
    header, payload, signature = parts
    tampered_signature = "invalid-signature"  # guaranteed not to match
    tampered = ".".join([header, payload, tampered_signature])

    with pytest.raises(JWTError):
        decode_token(tampered)

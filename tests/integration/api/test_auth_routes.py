import pytest
from uuid import uuid4
from httpx import AsyncClient
from app.core.security import hash_password
from app.core.config import settings


@pytest.mark.anyio
async def test_login_and_get_tokens_logout(async_client: AsyncClient, db_session, token_headers):
    """User can log in and receive access and refresh tokens."""

    email = f"auth_login_{uuid4().hex[:6]}@gmail.com"
    password = "StrongPass1!"

    # Register user via API
    register_payload = {
        "email": email,
        "full_name": "Auth Login User",
        "password": password,
    }
    reg_resp = await async_client.post(f"{settings.route_prefix}/auth", json=register_payload)
    assert reg_resp.status_code == 201

    # Login to get tokens
    payload = {"username": email, "password": password}
    resp = await async_client.post(f"{settings.route_prefix}/auth/login", data=payload)
    assert resp.status_code == 200

    # Extract tokens from response
    data = resp.json()
    token = data["token"]
    assert "access_token" in token
    assert "refresh_token" in token
    assert token["token_type"].lower() == "bearer"
    assert data["user"]["email"] == email

    # Prepare headers for authenticated request
    headers = await token_headers(email, password)

    # Logout using body refresh_token
    logout_payload = {"refresh_token": token["refresh_token"]}
    logout_resp = await async_client.post(f"{settings.route_prefix}/auth/logout", json=logout_payload, headers=headers)
    assert logout_resp.status_code == 204


@pytest.mark.anyio
async def test_login_invalid_credentials(async_client: AsyncClient, db_session):
    """Invalid credentials should return 401."""

    payload = {"username": "nonexistent@gmail.com", "password": "BadPass1!"}
    resp = await async_client.post(f"{settings.route_prefix}/auth/login", data=payload)
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_refresh_access_token(async_client: AsyncClient, db_session, token_headers):
    """Refresh endpoint should issue a new access token from a valid refresh token."""

    email = f"auth_refresh_{uuid4().hex[:6]}@gmail.com"
    password = "StrongPass1!"

    # Register user via API
    register_payload = {
        "email": email,
        "full_name": "Auth Refresh User",
        "password": password,
    }
    reg_resp = await async_client.post(f"{settings.route_prefix}/auth", json=register_payload)
    assert reg_resp.status_code == 201

    # First login to obtain refresh token
    login_payload = {"username": email, "password": password}
    login_resp = await async_client.post(f"{settings.route_prefix}/auth/login", data=login_payload)
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    refresh_token = tokens["token"]["refresh_token"]

    # Refresh the access token using the refresh token
    resp = await async_client.post(f"{settings.route_prefix}/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200

    # Extract new tokens from response
    data = resp.json()
    token = data["token"]
    assert "access_token" in token
    assert token["token_type"].lower() == "bearer"
    assert data["user"]["email"] == email


@pytest.mark.anyio
async def test_client_credentials_auth(async_client: AsyncClient, db_session, token_headers):
    """Client can authenticate with client_id and secret."""

    from app.repositories.user import UserRepository
    from app.schemas.user import UserCreateInDB

    # Create an admin user to be able to create a client
    user_repo = UserRepository()
    admin_email = f"admin_client_auth_{uuid4().hex[:6]}@gmail.com"
    admin_password = "StrongPass1!"

    admin_dto = UserCreateInDB(
        email=admin_email,
        full_name="Admin Client Auth",
        hashed_password=hash_password(admin_password),
        is_active=True,
        is_superuser=True,
        require_password_change=False,
    )
    await user_repo.create(db_session, admin_dto)

    admin_headers = await token_headers(admin_email, admin_password)

    # Create client via API using admin credentials
    client_payload = {"name": f"auth_client_{uuid4().hex[:6]}", "is_active": True}
    client_resp = await async_client.post(
        f"{settings.route_prefix}/clients", json=client_payload, headers=admin_headers
    )
    assert client_resp.status_code == 201

    # Authenticate using client credentials
    client_data = client_resp.json()
    client_auth_payload = {
        "client_id": str(client_data["client_id"]),
        "client_secret": client_data["secret"],
        "grant_type": "client_credentials",
    }
    auth_resp = await async_client.post(f"{settings.route_prefix}/auth/client", json=client_auth_payload)
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    assert auth_data["client_id"] == str(client_data["client_id"])
    assert "access_token" in auth_data["token"]

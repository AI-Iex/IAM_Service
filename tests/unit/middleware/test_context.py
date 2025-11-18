import pytest
from uuid import UUID
from app.main import app
from app.core.logging_config import get_request_context
from app.core.security import create_user_access_token


@pytest.mark.anyio
async def test_request_sets_request_id_header_and_context(async_client):
    """Verify that the access/context middleware sets a request id and exposes it via header and contextvars."""

    # Register a small test route that returns the current request context
    @app.get("/__test/get_context")
    async def _get_context():
        rid, uid = get_request_context()
        return {"request_id": rid, "user_id": str(uid) if uid is not None else None}

    resp = await async_client.get("/__test/get_context")
    assert resp.status_code == 200

    # Header X-Request-Id must be present and match the context value returned by the route
    header_rid = resp.headers.get("X-Request-Id")
    body = resp.json()
    assert header_rid is not None
    assert body["request_id"] == header_rid


@pytest.mark.anyio
async def test_auth_context_sets_user_id_in_context(async_client, create_user):
    """When a valid Bearer token is provided, the auth middleware must populate the user id in contextvars."""

    # Create a user and issue an access token for them
    user = await create_user("ctxuser@example.com", "password123", full_name="Ctx User")
    token_pair = create_user_access_token(subject=str(user.id), permissions=[], is_superuser=False)
    token = token_pair.access_token

    # Reuse the same test route to inspect context
    @app.get("/__test/get_context_auth")
    async def _get_context_auth():
        rid, uid = get_request_context()
        # Return user id as string when present
        return {"request_id": rid, "user_id": str(uid) if uid is not None else None}

    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.get("/__test/get_context_auth", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == str(user.id)
    assert "request_id" in body and body["request_id"] is not None

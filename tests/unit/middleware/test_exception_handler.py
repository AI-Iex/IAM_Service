import pytest
from uuid import UUID
from app.main import app
from app.core.exceptions import (
    EntityAlreadyExists,
    DomainError,
    NotFoundError,
    RepositoryError,
)
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel


class DummyModel(BaseModel):
    name: str


@pytest.mark.anyio
async def test_unauthorized_error_maps_to_401(async_client):
    """Raising UnauthorizedError in a route should map to 401 with the correct error code."""

    from app.core.exceptions import UnauthorizedError

    @app.get("/__test/raise_unauthorized")
    async def _raise_unauthorized():
        raise UnauthorizedError("not authenticated")

    resp = await async_client.get("/__test/raise_unauthorized")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error_type"] == "UNAUTHORIZED"
    assert body["error_code"] == "APP.AUTH.401"


@pytest.mark.anyio
async def test_request_validation_uuid_error(async_client):
    """Requests with invalid UUID path parameter should return the INVALID_UUID_FORMAT error payload and 422."""

    @app.get("/__test/items/{item_id}")
    async def read_item(item_id: UUID):
        return {"ok": True}

    resp = await async_client.get("/__test/items/not-a-uuid")
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_type"] == "INVALID_UUID_FORMAT"
    assert body["error_code"] == "APP.VAL.002"
    assert "request_id" in body


@pytest.mark.anyio
async def test_entity_already_exists_maps_to_409(async_client):
    """Raising EntityAlreadyExists in a route should map to 409 and the expected error code."""

    @app.get("/__test/raise_exists")
    async def _raise_exists():
        raise EntityAlreadyExists("user exists")

    resp = await async_client.get("/__test/raise_exists")
    assert resp.status_code == 409
    body = resp.json()
    assert body["error_type"] == "ENTITY_ALREADY_EXISTS"
    assert body["error_code"] == "APP.USR.001"


@pytest.mark.anyio
async def test_domain_error_maps_to_400(async_client):
    @app.get("/__test/raise_domain")
    async def _raise_domain():
        raise DomainError("invalid business rule")

    resp = await async_client.get("/__test/raise_domain")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error_type"] == "DOMAIN_ERROR"
    assert body["error_code"] == "APP.BIZ.001"


@pytest.mark.anyio
async def test_not_found_maps_to_404(async_client):
    @app.get("/__test/raise_not_found")
    async def _raise_not_found():
        raise NotFoundError("nope")

    resp = await async_client.get("/__test/raise_not_found")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error_type"] == "NOT_FOUND"
    assert body["error_code"] == "APP.ERR.404"


@pytest.mark.anyio
async def test_repository_error_maps_to_500(async_client, monkeypatch):
    """RepositoryError should return 500 and the REPOSITORY_ERROR code."""

    @app.get("/__test/raise_repo")
    async def _raise_repo():
        raise RepositoryError("db fail")

    # Ensure DEBUG is False so sanitized_traceback is not injected into logs
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEBUG", False)

    resp = await async_client.get("/__test/raise_repo")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error_type"] == "REPOSITORY_ERROR"
    assert body["error_code"] == "APP.DB.001"


@pytest.mark.anyio
async def test_unhandled_exception_maps_to_500(async_client):
    @app.get("/__test/raise_unhandled")
    async def _raise_unhandled():
        raise RuntimeError("boom")

    resp = await async_client.get("/__test/raise_unhandled")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error_type"] == "INTERNAL_SERVER_ERROR"
    assert body["error_code"] == "APP.ERR.500"

import time
import pytest
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateInDB
from app.core.security import hash_password

iterations = 5
max_seconds_per_query = 1.0


@pytest.mark.anyio
async def test_database_query_latency(db_session):
    """Basic read queries should execute with an acceptable time."""

    repo = UserRepository()

    base_email = "perf_user"
    password = "PerfTestPass1!"
    for i in range(iterations):
        dto = UserCreateInDB(
            email=f"{base_email}_{i}@example.com",
            full_name=f"Perf User {i}",
            hashed_password=hash_password(password),
            is_active=True,
            is_superuser=False,
            require_password_change=False,
        )
        await repo.create(db_session, dto)

    start = time.perf_counter()

    for i in range(iterations):
        _ = await repo.read_by_email(db_session, f"{base_email}_{i}@example.com")
    elapsed = time.perf_counter() - start

    avg = elapsed / iterations
    assert avg <= max_seconds_per_query, f"DB query too slow: avg {avg:.4f}s > {max_seconds_per_query:.2f}s"

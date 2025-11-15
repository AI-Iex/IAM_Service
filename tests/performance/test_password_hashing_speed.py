import time
import pytest
from app.core.security import hash_password

iterations = 5
max_seconds_per_hash = 1.0

@pytest.mark.anyio
async def test_password_hashing_speed():
    
    """Password hashing should complete with an acceptable time."""

    password = "PerfTestPass1!"
    
    start = time.perf_counter()
    for _ in range(iterations):
        _ = hash_password(password)
    elapsed = time.perf_counter() - start

    avg = elapsed / iterations
    
    assert avg <= max_seconds_per_hash, (
        f"Password hashing too slow: avg {avg:.4f}s > {max_seconds_per_hash:.2f}s"
    )

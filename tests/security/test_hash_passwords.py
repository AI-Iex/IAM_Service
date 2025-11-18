import pytest
from app.core.security import hash_password, verify_password


def test_password_hash_and_verify():
    """Test that hashing and verifying passwords works as expected."""

    try:
        plain = "SuperSecure123!"
        hashed = hash_password(plain)

        assert hashed != plain
        assert len(hashed) > 0
        assert verify_password(plain, hashed)
        assert not verify_password("wrong_password", hashed)

    except Exception as e:
        pytest.fail(f"Error: Password hash/verify test: {e}")


def test_empty_password_raises_error():
    """Test that hashing or verifying empty passwords raises ValueError."""

    with pytest.raises(ValueError):
        hash_password("")

    with pytest.raises(ValueError):
        verify_password("", "hash")

    with pytest.raises(ValueError):
        verify_password("", "")

    with pytest.raises(ValueError):
        verify_password("plain", "")

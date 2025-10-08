import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from app.core.config import settings

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(settings.DATABASE_URL)
    yield engine
    engine.dispose()

# Test to check database connection
def test_db_connection(db_engine):
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except OperationalError as e:
        pytest.fail(f"Error: Could not connect to the DB: {e}")

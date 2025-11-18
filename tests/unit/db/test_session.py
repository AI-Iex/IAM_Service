import pytest
from sqlalchemy import text


@pytest.mark.anyio
async def test_engine_connect(engine):
    """Sanity-check that the test engine is connectable and can execute a simple query."""

    async with engine.connect() as conn:
        res = await conn.execute(text("select 1"))
        val = res.scalar_one()
        assert int(val) == 1

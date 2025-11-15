import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import session as db_session_module
from app.db.unit_of_work import get_uow_factory
from app.repositories.role import RoleRepository
from app.schemas.role import RoleCreate

def _make_session_factory(engine):

    """Return a callable factory that produces AsyncSession instances bound to the provided engine."""

    def factory():
        Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        return Session()
    return factory

@pytest.mark.anyio
async def test_uow_commits(engine, monkeypatch, db_session):

    """SQLAlchemyUnitOfWork should commit changes when exiting the context without exceptions."""

    factory = _make_session_factory(engine)
   
    monkeypatch.setattr(db_session_module, "AsyncSessionLocal", factory)
    monkeypatch.setattr("app.db.unit_of_work.AsyncSessionLocal", factory)

    uow_factory = get_uow_factory()
    role_repo = RoleRepository()

    # Use the uow to create a role and let it commit
    async with uow_factory() as db:
        r = await role_repo.create(db, RoleCreate(name="test-uow-role", description="desc"))
        created_id = r.id

    # Outside the UoW, verify the role exists using the standard db_session fixture
    found = await role_repo.read_by_id(db_session, created_id)
    assert found is not None and found.id == created_id

@pytest.mark.anyio
async def test_uow_rolls_back_on_exception(engine, monkeypatch, db_session):

    """SQLAlchemyUnitOfWork should rollback if an exception is raised inside the context."""
    
    factory = _make_session_factory(engine)
    monkeypatch.setattr(db_session_module, "AsyncSessionLocal", factory)
    monkeypatch.setattr("app.db.unit_of_work.AsyncSessionLocal", factory)
    uow_factory = get_uow_factory()
    role_repo = RoleRepository()

    # Exception inside the UoW should trigger rollback
    try:
        async with uow_factory() as db:
            r = await role_repo.create(db, RoleCreate(name="uow-should-rollback", description="desc"))
            # Force an error to trigger rollback
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass

    # The role should not have been committed
    res = await role_repo.read_with_filters(db_session, name="uow-should-rollback")
    assert len(res) == 0

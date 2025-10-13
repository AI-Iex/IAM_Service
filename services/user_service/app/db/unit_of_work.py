from contextlib import contextmanager
from typing import Iterator, Callable, ContextManager
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

UnitOfWorkFactory = Callable[[], ContextManager[Session]]

@contextmanager
def unit_of_work() -> Iterator[Session]:

    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

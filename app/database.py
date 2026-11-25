"""Database engine, session factory and FastAPI session dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

# check_same_thread=False is required because FastAPI may use a session
# from a different thread than the one that created it (SQLite only).
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and make sure it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

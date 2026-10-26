"""Database connection and session factory management supporting SQLite and PostgreSQL."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from supplychain_iq.db.models import Base

DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
DEFAULT_SQLITE_PATH = DEFAULT_DB_DIR / "supplychain_iq.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"


def get_db_url() -> str:
    """Retrieve DATABASE_URL from environment with documented local SQLite fallback."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        DEFAULT_DB_DIR.mkdir(parents=True, exist_ok=True)
        return DEFAULT_DATABASE_URL
    # Normalize Postgres URI scheme if provided as postgres://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def get_db_engine(database_url: Optional[str] = None) -> Engine:
    """Create a SQLAlchemy Engine with connection parameters tuned for the dialect."""
    url = database_url or get_db_url()
    is_sqlite = url.startswith("sqlite")

    connect_args = {}
    if is_sqlite:
        connect_args["check_same_thread"] = False

    engine = create_engine(
        url,
        connect_args=connect_args,
        echo=False,
        future=True,
    )

    # Enable foreign keys for SQLite connections
    if is_sqlite:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def init_db(engine: Optional[Engine] = None) -> None:
    """Idempotently create all relational tables."""
    eng = engine or get_db_engine()
    Base.metadata.create_all(bind=eng)


@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Provide a transactional database session scope."""
    eng = engine or get_db_engine()
    session_factory = sessionmaker(bind=eng, expire_on_commit=False)
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

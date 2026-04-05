"""
SQLAlchemy database setup for the Laghu Parashari backend.
Uses SQLite for portability; swap DATABASE_URL for PostgreSQL in production.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./laghu_parashari.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once at app startup."""
    from models.db_models import NatalChart, LessonProgress  # noqa: F401
    Base.metadata.create_all(bind=engine)
